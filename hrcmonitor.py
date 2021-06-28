#!/usr/bin/env conda run -n ska3 python


import time
import shutil
import sys
import os
import argparse

import matplotlib
import datetime as dt
import Chandra.Time
import Ska.engarchive.fetch as fetch
import socket
import traceback
import pytz

import numpy as np
import pandas as pd

from msidlists import *
from event_times import *
from plot_stylers import *

from forecast_thermals import make_thermal_plots
from plot_motors import make_motor_plots

from chandratime import convert_chandra_time, convert_to_doy
from cxotime import CxoTime

from heartbeat import are_we_in_comm

plt.style.use('ggplot')
labelsizes = 8
# plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.size'] = labelsizes

plt.rcParams['axes.titlesize'] = labelsizes
plt.rcParams['axes.labelsize'] = labelsizes
plt.rcParams['xtick.labelsize'] = labelsizes - 2
plt.rcParams['ytick.labelsize'] = labelsizes - 2

# Use the new Matplotlib 3.X constrained_layout solver in lieu of tight_layout()
# plt.rcParams['figure.constrained_layout.use'] = True


def make_realtime_plot(counter, plot_start=dt.datetime(2020, 8, 31, 00), plot_end=dt.date.today() + dt.timedelta(days=2), sampling='full', current_hline=False, date_format=mdate.DateFormatter('%d %H'), force_limits=False, missionwide=False, fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/', show_in_gui=False):
    plotnum = -1

    fig = plt.figure(figsize=(16, 6), constrained_layout=True)
    gs = fig.add_gridspec(3, 4)

    if missionwide is False:
        # Then override the existing dashboard_msid* with the missionwide one
        dashboard_msids = dashboard_msids_latest
        dashboard_tiles = dashboard_tiles_latest
        dashboard_limits = dashboard_limits_latest
        dashboard_units = dashboard_units_latest
    elif missionwide is True:
        # Then override the existing dashboard_msid* with the missionwide one
        dashboard_msids = dashboard_msids_missionwide
        dashboard_tiles = dashboard_tiles_missionwide
        dashboard_limits = dashboard_limits_missionwide
        dashboard_units = dashboard_units_missionwide

    for i in range(3):
        for j in range(4):
            ax = fig.add_subplot(gs[i, j])
            plotnum += 1
            for msid in dashboard_msids[plotnum]:

                data = fetch.get_telem(
                    msid, start=convert_to_doy(plot_start), sampling=sampling, max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)

                print('Fetching from {} at {} resolution: {}'.format(
                    convert_to_doy(plot_start), sampling, msid), end='\r', flush=True)
                # Clear the command line manually
                sys.stdout.write("\033[K")

                if sampling == 'full':
                    ax.plot_date(convert_chandra_time(
                        data[msid].times), data[msid].vals, markersize=1, label=msid, zorder=1, rasterized=True)
                elif sampling == 'daily':
                    # Then plot the means
                    ax.plot_date(convert_chandra_time(
                        data[msid].times), data[msid].means, markersize=1, label=msid, zorder=1, rasterized=True)
                # Plot a HORIZONTAL line at location of last data point.
                if current_hline is True:
                    if missionwide is False:
                        # then we already have the latest MAUDE data
                        ax.axhline(data[msid].vals[-1],
                                   color=green, zorder=2)
                    elif missionwide is True:
                        if plotnum != 0:
                            today = dt.datetime.utcnow().date()
                            yesterday = today - dt.timedelta(days=1)
                            with fetch.data_source('maude'):
                                latest_data = fetch.get_telem(
                                    msid, start=convert_to_doy(yesterday), quiet=True)
                            ax.axhline(
                                latest_data[msid].vals[-1], color=yellow, zorder=2)
                if force_limits is True:
                    ax.set_ylim(dashboard_limits[plotnum])

            if plotnum == 2:
                # Then this is the Bus Current plot. Overplot the CAUTION and WARNING limits
                ax.axhspan(2.3, 2.5, facecolor=yellow, alpha=0.3)
                ax.axhspan(2.5, 4.0, facecolor=red, alpha=0.3)
                # Also, save the latest bus current value for the suptitle
                latest_bus_current = data[msid].vals[-1]

            if plotnum == 10:
                ax.set_yscale('log')

            if missionwide is True:
                if plotnum == 11:
                    ax.set_yscale('log')

            ax.set_xlim(plot_start, plot_end)
            ax.set_ylabel(dashboard_units[plotnum], color='slategray', size=8)

            if plotnum in range(8, 12):
                ax.set_xlabel('Date (UTC)', color='slategray', size=6)

            if missionwide is True:
                if plotnum == 0:
                    ax.text(time_of_cap_1543, ax.get_ylim()[
                            1], 'Side B Swap', fontsize=6, color='slategray')
                    ax.axvline(time_of_cap_1543, color='gray', alpha=0.5)
            else:
                ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1],
                        'Now', fontsize=6, color='slategray')
                ax.axvline(dt.datetime.now(pytz.utc), color='gray', alpha=0.5)

            plt.gca().xaxis.set_major_formatter(date_format)

            plt.xticks(rotation=0)

            ax.legend(prop={'size': 8}, loc=3)
            ax.set_title('{}'.format(
                dashboard_tiles[plotnum]), color='slategray', loc='center')

    if missionwide is False:
        plt.suptitle(t='Latest Bus Current: {} A\nIteration {} | Updated as of {} EST'.format(np.round(
            latest_bus_current, 2), counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=6)
    elif missionwide is True:
        plt.suptitle(t='Iteration {} | Updated as of {} EST'.format(
            counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=6)

    if missionwide is False:
        plt.savefig(fig_save_directory + 'status.png', dpi=300)
        plt.savefig(fig_save_directory + 'status.pdf',
                    dpi=300, rasterized=True)
    elif missionwide is True:
        plt.savefig(fig_save_directory + 'status_wide.png', dpi=300)
        plt.savefig(fig_save_directory + 'status_wide.pdf',
                    dpi=300, rasterized=True)

    if show_in_gui:
        plt.show()

    plt.close()


def comm_status_stamp(comm_status, code_start_time, hostname, fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/'):

    if comm_status is True:
        commreport = f'In Comm!'
        subtext = f'Comm appears to have started at {dt.datetime.now().strftime("%H:%M:%S")}'
        textcolor = 'steelblue'
    elif comm_status is False:
        commreport = 'Not in Comm'
        subtext = f'Out of Comm since {dt.datetime.now().strftime("%H:%M:%S")}'
        textcolor = 'slategray'

    code_uptime = dt.datetime.now() - code_start_time

    fig = plt.figure(figsize=(8, 2))
    plt.axis('off')
    plt.tight_layout()
    fig.patch.set_facecolor('white')

    text = plt.text(0.001, 0.2, commreport, color=textcolor, fontsize=50)
    subtext = plt.text(
        0.004, 0.08, subtext, color=textcolor, fontsize=12)
    uptime_text = plt.text(
        0.004, 0.0001, 'HRCMonitor has been running on {} since {} ({} days)'.format(hostname,code_start_time.strftime("%Y %b %d %H:%M:%S"), code_uptime.days), color='slategray', fontsize=9)

    plt.savefig(fig_save_directory + 'comm_status.png', dpi=300)
    plt.close()


def update_ancillary_plots(iteration_counter, fig_save_directory):

    five_days_ago = dt.date.today() - dt.timedelta(days=5)
    two_days_hence = dt.date.today() + dt.timedelta(days=2)


    fetch.data_source.set('cxc')
    make_realtime_plot(iteration_counter, fig_save_directory=fig_save_directory, plot_start=dt.datetime(
        2000, 1, 4), plot_end=None, sampling='daily', date_format=mdate.DateFormatter('%Y'), current_hline=True, missionwide=True, force_limits=True)

    print('Saved Mission-Wide Plots to {}'.format(
        fig_save_directory), end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    print('Updating Motor Plots', end="\r", flush=True)
    make_motor_plots(iteration_counter, fig_save_directory=fig_save_directory, plot_start=five_days_ago,
                        plot_end=two_days_hence, sampling='full', date_format=mdate.DateFormatter('%m-%d'))
    print('Done', end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    print('Saved Motor Plots to {}'.format(
        fig_save_directory), end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    print('Updating Thermal Plots', end="\r", flush=True)
    make_thermal_plots(
        iteration_counter, fig_save_directory=fig_save_directory)
    print('Done', end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    print('Saved Thermal Plots to {}'.format(
        fig_save_directory), end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    plt.close('all')

def get_args():
    '''Fetch command line args, if given'''

    parser = argparse.ArgumentParser(
        description='Monitor the VCDU telemetry stream, and update critical status plots whenever we are in comm.')

    parser.add_argument("--fake_comm", help="Trick the code to think it's in comm. Useful for testing. ",
                        action="store_true")

    parser.add_argument("--force_ska", help="Trick the code pull from Ska/CXC instead of MAUDE with a switch to fetch.data_source.set() ",
                        action="store_true")

    parser.add_argument("--report_errors", help="Print MAUDE exceptions (which are common) to the command line",
                        action="store_true")

    parser.add_argument("--show_in_gui", help="Show plots with plt.show()",
                        action="store_true")

    args = parser.parse_args()
    return args


def main():
    '''
    The main event loop. Sets plotting parameters and data sources, and makes
    both plots. Saves them to preferred directories. Pauses the loop for a few
    minutes of sleep to avoid overwhelming MAUDE and wasting cycles.
    '''

    hostname = socket.gethostname()

    if hostname == 'han-v.cfa.harvard.edu':
        print('Recognized host: {}'.format(hostname))
        fig_save_directory = '/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/'
    elif hostname == 'symmetry.local':
        print('Recognized host: {}'.format(hostname))
        fig_save_directory = '/Users/grant/Desktop/'
    else:
        sys.exit('I do not recognize the hostname {}. Exiting.'.format(
            hostname))

    args = get_args()
    fake_comm = args.fake_comm

    if args.show_in_gui is False:
        # Then we're on a headless machine and you should use agg
        backend = 'agg'
    elif args.show_in_gui is True:
        backend = 'MacOSX'
    matplotlib.use(backend, force=True)

    from matplotlib import gridspec
    import matplotlib.dates as mdate
    import matplotlib.pyplot as plt
    print("Using Matplotlib backend:", matplotlib.get_backend())

    # Initial settings
    recently_in_comm = False
    in_comm_counter = 0
    out_of_comm_refresh_counter = 0
    iteration_counter = 0

    # Loop infinitely :)
    while True:

        try:

            in_comm = are_we_in_comm(
                verbose=False, cadence=2, fake_comm=fake_comm)

            # Generate the first comm status stamp and create code start date
            if iteration_counter == 0:
                code_start_time = dt.datetime.now()
                comm_status_stamp(comm_status=in_comm, fig_save_directory=fig_save_directory, code_start_time=code_start_time, hostname=hostname)

            if not in_comm:

                if recently_in_comm:
                    # Then update the text stamp
                    comm_status_stamp(comm_status=in_comm, code_start_time=code_start_time,
                                      fig_save_directory=fig_save_directory, hostname=hostname)

                    update_ancillary_plots(iteration_counter, fig_save_directory)

                    plt.close('all')

                recently_in_comm = False
                in_comm_counter = 0
                out_of_comm_refresh_counter += 1
                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) Not in Comm.                                 ', end='\r\r\r')

                if out_of_comm_refresh_counter == 20:
                    # Refresh the plots every 20th iteration out-of-comm
                    print("Performing out-of-comm plot refresh at {}".format(dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), flush=True)

                    five_days_ago = dt.date.today() - dt.timedelta(days=5)
                    two_days_hence = dt.date.today() + dt.timedelta(days=2)

                    make_realtime_plot(iteration_counter, plot_start=five_days_ago, fig_save_directory=fig_save_directory,
                                plot_end=two_days_hence, sampling='full', date_format=mdate.DateFormatter('%m-%d'), force_limits=True, show_in_gui=args.show_in_gui)

                    update_ancillary_plots(iteration_counter, fig_save_directory)
                    plt.close('all')

                    # Reset the refresh counter
                    out_of_comm_refresh_counter = 0




            if in_comm:

                recently_in_comm = True
                in_comm_counter += 1

                if in_comm_counter == 1:
                    # Then update the text stamp
                    comm_status_stamp(comm_status=in_comm, code_start_time=code_start_time,
                                      fig_save_directory=fig_save_directory, hostname=hostname)


                if in_comm_counter == 5:
                    # Then create the mission-wide status plots
                    print("Refreshing long term Plots at {}".format(iteration_counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), flush=True)
                    update_ancillary_plots(iteration_counter, fig_save_directory)
                    plt.close('all')

                # Explicitly set maude each time, because ancillary plots use CXC
                fetch.data_source.set('maude allow_subset=False')
                if args.force_ska:
                    fetch.data_source.set('cxc')

                print("Refreshing dashboard (Iteration {}) at {}".format(
                    iteration_counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), flush=True)

                five_days_ago = dt.date.today() - dt.timedelta(days=5)
                two_days_hence = dt.date.today() + dt.timedelta(days=2)

                make_realtime_plot(iteration_counter, plot_start=five_days_ago, fig_save_directory=fig_save_directory,
                            plot_end=two_days_hence, sampling='full', date_format=mdate.DateFormatter('%m-%d'), force_limits=True, show_in_gui=args.show_in_gui)

                print('Saved Current Status Plots to {}'.format(
                    fig_save_directory), end="\r", flush=True)
                # Clear the command line manually
                sys.stdout.write("\033[K")

                plt.close('all')


                sleep_period_seconds = 3

                for i in range(0, sleep_period_seconds):
                    # you need to flush this print statement
                    print('Refreshing plots in {} seconds...'.format(
                        sleep_period_seconds-i), end="\r", flush=True)
                    time.sleep(1)  # sleep for 1 second per iteration

            iteration_counter += 1

        except Exception as e:
            if args.report_errors is True:
                print("ERROR on Iteration {}: {}".format(iteration_counter, e))
                print("Heres the traceback:")
                print(traceback.format_exc())
                print("Pressing on...")
            elif args.report_errors is False:
                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) MAUDE Error =(                             ', end='\r\r\r')
            continue


if __name__ == "__main__":
    main()
