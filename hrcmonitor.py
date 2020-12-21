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


def update_plot(counter, plot_start=dt.datetime(2020, 8, 31, 00), plot_end=dt.date.today() + dt.timedelta(days=2), sampling='full', current_hline=False, date_format=mdate.DateFormatter('%d %H'), force_limits=False, missionwide=False):
    plotnum = -1
    for i in range(3):
        for j in range(4):
            ax = plt.subplot2grid((3, 4), (i, j))
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
                        today = dt.datetime.utcnow().date()
                        yesterday = today - dt.timedelta(days=1)
                        with fetch.data_source('maude'):
                            latest_data = fetch.get_telem(
                                msid, start=convert_to_doy(yesterday), quiet=True)
                        ax.axhline(
                            latest_data[msid].vals[-1], color=yellow, zorder=2)
                        # then we've fetched from CXC/Ska and we don't. So grab it (with low fetch overhead)
                if force_limits is True:
                    ax.set_ylim(dashboard_limits[plotnum])

            if plotnum == 2:
                # Then this is the Bus Current plot. Overplot the CAUTION and WARNING limits
                ax.axhspan(2.3, 2.5, facecolor=yellow, alpha=0.3)
                ax.axhspan(2.5, 4.0, facecolor=red, alpha=0.3)

            if plotnum == 10:
                ax.set_yscale('log')

            if missionwide is True and plotnum == 11:
                ax.set_ylabel(r'Counts s$^{-1}$')
                data = fetch.get_telem('2SHEV1RT', start=plot_start, sampling=sampling,
                                       max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
                # It will have already plotted pitch. So just clear it.
                ax.clear()
                ax.plot_date(convert_chandra_time(
                    data['2SHEV1RT'].times), data['2SHEV1RT'].midvals, markersize=1, label=msid, zorder=1, rasterized=True)
                with fetch.data_source('maude'):
                    latest_data = fetch.get_telem(
                        '2SHEV1RT', start=convert_to_doy(yesterday), quiet=True)
                ax.axhline(
                    latest_data['2SHEV1RT'].vals[-1], color=yellow, zorder=2)

            ax.set_xlim(plot_start, plot_end)
            ax.set_ylabel(dashboard_units[plotnum])

            # ax.axvline(eventdate, color=red)
            # ax.axvline(time_of_second_anomaly, color=red)
            # ax.axvline(time_of_cap_1543, color='gray')
            ax.axvline(dt.datetime.now(pytz.utc),
                       color='gray', alpha=0.5)

            ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1],
                    'Now', fontsize=6, color='slategray')

            plt.gca().xaxis.set_major_formatter(date_format)

            plt.xticks(rotation=0)

            ax.legend(prop={'size': 8}, loc=3)
            ax.set_title('{}'.format(
                dashboard_tiles[plotnum]), color='slategray', loc='center')

            if missionwide is True:
                if plotnum == 10:
                    ax.set_ylim(1, 10000)
                    ax.set_yscale('log')
                if plotnum == 11:
                    ax.set_ylim(1, 10000)
                    ax.set_ylabel(r"Counts s$^{-1}$")
                    ax.set_title('Shield Rate'.format(),
                                 color='slategray', loc='center')

            plt.suptitle(t='Iteration {} | Updated as of {} EST'.format(
                counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), y=0.99, color='slategray', size=6)


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
    plt.figure(figsize=(17, 6))

    counter = 0

    while True:

        try:

            # fetch.data_source.set('cxc', 'maude allow_subset=False')
            fetch.data_source.set('maude allow_subset=False')

            print("Refreshing dashboard (Iteration {}) at {}".format(
                counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), flush=True)

            two_days_ago = dt.date.today() - dt.timedelta(days=2)
            four_days_ago = dt.date.today() - dt.timedelta(days=4)
            six_days_ago = dt.date.today() - dt.timedelta(days=6)
            two_days_hence = dt.date.today() + dt.timedelta(days=2)

            update_plot(counter, plot_start=six_days_ago,
                        plot_end=two_days_hence, sampling='full', date_format=mdate.DateFormatter('%m-%d'), force_limits=True)

            plt.draw()
            # plt.tight_layout()
            plt.savefig(fig_save_directory + 'status.png', dpi=300)
            plt.savefig(fig_save_directory + 'status.pdf',
                        dpi=300, rasterized=True)
            print('Saved Current Status Plots to {}'.format(
                fig_save_directory), end="\r", flush=True)
            # Clear the command line manually
            sys.stdout.write("\033[K")

            plt.clf()

            fetch.data_source.set('cxc')

            update_plot(counter, plot_start=dt.datetime(
                2000, 1, 4), plot_end=None, sampling='daily', date_format=mdate.DateFormatter('%Y'), current_hline=True, missionwide=True)

            # plt.tight_layout()
            plt.draw()
            plt.savefig(fig_save_directory + 'status_wide.png', dpi=300)
            plt.savefig(fig_save_directory + 'status_wide.pdf',
                        dpi=300, rasterized=True)

            print('Saved Mission-Wide Plots to {}'.format(
                fig_save_directory), end="\r", flush=True)
            # Clear the command line manually
            sys.stdout.write("\033[K")

            print('Updating Motor Plots', end="\r", flush=True)
            make_motor_plots(counter, fig_save_directory=fig_save_directory, plot_start=six_days_ago,
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
        sleep_period_seconds = 30
        for i in range(0, sleep_period_seconds):
            # you need to flush this print statement
            print('Refreshing plots in {} seconds...'.format(
                sleep_period_seconds-i), end="\r", flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
