#!/usr/bin/env conda run -n ska3 python

import matplotlib.pyplot as plt
from matplotlib import gridspec
import matplotlib.dates as mdate
import datetime as dt
import Chandra.Time
import Ska.engarchive.fetch as fetch
import socket
import traceback
import pytz
import time
import shutil
import sys
import os
import traceback
import numpy as np
import pandas as pd

from msidlists import *
from event_times import *
from plot_stylers import *

from forecast_thermals import make_thermal_plots
from plot_motors import make_motor_plots

from chandratime import convert_chandra_time, convert_to_doy

plt.switch_backend('agg')


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


def update_plot(counter, plot_start=dt.datetime(2020, 8, 31, 00), plot_end=dt.date.today() + dt.timedelta(days=2), sampling='full', current_hline=False, date_format=mdate.DateFormatter('%d %H'), force_limits=False, missionwide=False, fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/'):
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

    plt.close()


def main():
    '''
    The main event loop. Sets plotting parameters and data sources, and makes
    both plots. Saves them to preferred directories. Pauses the loop for a few
    minutes of sleep to avoid overwhelming MAUDE and wasting cycles.
    '''

    if socket.gethostname() == 'han-v.cfa.harvard.edu':
        print('Recognized host: {}'.format(socket.gethostname()))
        fig_save_directory = '/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/'
    elif socket.gethostname() == 'symmetry.local':
        print('Recognized host: {}'.format(socket.gethostname()))
        fig_save_directory = '/Users/grant/Desktop/'
    else:
        sys.exit('I do not recognize the hostname {}. Exiting.'.format(
            socket.gethostname()))

    # plt.ion()

    counter = 0

    while True:

        try:

            # fetch.data_source.set('cxc', 'maude allow_subset=False')
            fetch.data_source.set('maude allow_subset=False')

            print("Refreshing dashboard (Iteration {}) at {}".format(
                counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), flush=True)

            five_days_ago = dt.date.today() - dt.timedelta(days=5)
            two_days_hence = dt.date.today() + dt.timedelta(days=2)

            update_plot(counter, plot_start=five_days_ago, fig_save_directory=fig_save_directory,
                        plot_end=two_days_hence, sampling='full', date_format=mdate.DateFormatter('%m-%d'), force_limits=True)

            print('Saved Current Status Plots to {}'.format(
                fig_save_directory), end="\r", flush=True)
            # Clear the command line manually
            sys.stdout.write("\033[K")

            fetch.data_source.set('cxc')
            update_plot(counter, fig_save_directory=fig_save_directory, plot_start=dt.datetime(
                2000, 1, 4), plot_end=None, sampling='daily', date_format=mdate.DateFormatter('%Y'), current_hline=True, missionwide=True, force_limits=True)

            print('Saved Mission-Wide Plots to {}'.format(
                fig_save_directory), end="\r", flush=True)
            # Clear the command line manually
            sys.stdout.write("\033[K")

            print('Updating Motor Plots', end="\r", flush=True)
            make_motor_plots(counter, fig_save_directory=fig_save_directory, plot_start=five_days_ago,
                             plot_end=two_days_hence, sampling='full', date_format=mdate.DateFormatter('%m-%d'))
            print('Done', end="\r", flush=True)
            # Clear the command line manually
            sys.stdout.write("\033[K")

            print('Saved Motor Plots to {}'.format(
                fig_save_directory), end="\r", flush=True)
            # Clear the command line manually
            sys.stdout.write("\033[K")

            print('Updating Thermal Plots', end="\r", flush=True)
            make_thermal_plots(counter, fig_save_directory=fig_save_directory)
            print('Done', end="\r", flush=True)
            # Clear the command line manually
            sys.stdout.write("\033[K")

            print('Saved Thermal Plots to {}'.format(
                fig_save_directory), end="\r", flush=True)
            # Clear the command line manually
            sys.stdout.write("\033[K")

        except Exception as e:
            print("ERROR on Iteration {}: {}".format(counter, e))
            print("Heres the traceback:")
            print(traceback.format_exc())
            print("Pressing on...")
            continue

        counter += 1
        sleep_period_seconds = 3
        for i in range(0, sleep_period_seconds):
            # you need to flush this print statement
            print('Refreshing plots in {} seconds...'.format(
                sleep_period_seconds-i), end="\r", flush=True)
            time.sleep(1)  # sleep for 1 second per iteration


if __name__ == "__main__":
    main()
