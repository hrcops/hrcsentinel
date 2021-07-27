#!/usr/bin/env conda run -n ska3 python

import time
import shutil
import sys
import os
import argparse

# Third party modules
import numpy as np
import matplotlib
import matplotlib.dates as mdate
import matplotlib.pyplot as plt

# Time is the fire in which we burn
import datetime as dt
import pytz

# Ska / Cheta
try:
    from cheta import fetch
except ImportError:
    sys.exit("Failed to import cheta (aka ska). Make sure you're using the latest version of the ska runtime environment (and that you have the conda environment initialized!).")


# HRCSentinel stuff
import plot_stylers
import msidlists
import event_times

from plot_thermals import make_thermal_plots
from plot_motors import make_motor_plots

from chandratime import convert_chandra_time, convert_to_doy
from commbot import convert_bus_current_to_dn


def make_realtime_plot(counter=None, plot_start=dt.datetime(2020, 8, 31, 00), plot_stop=dt.date.today() + dt.timedelta(days=2), sampling='full', current_hline=False, date_format=mdate.DateFormatter('%d %H'), force_limits=False, missionwide=False, fig_save_directory=None, show_in_gui=False):
    plotnum = -1

    fig = plt.figure(figsize=(16, 6), constrained_layout=True)
    gs = fig.add_gridspec(3, 4)

    if missionwide is False:
        # Then override the existing dashboard_msid* with the missionwide one
        dashboard_msids = msidlists.dashboard_msids_latest
        dashboard_tiles = msidlists.dashboard_tiles_latest
        dashboard_limits = msidlists.dashboard_limits_latest
        dashboard_units = msidlists.dashboard_units_latest
    elif missionwide is True:
        # Then override the existing dashboard_msid* with the missionwide one
        dashboard_msids = msidlists.dashboard_msids_missionwide
        dashboard_tiles = msidlists.dashboard_tiles_missionwide
        dashboard_limits = msidlists.dashboard_limits_missionwide
        dashboard_units = msidlists.dashboard_units_missionwide

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
                                latest_data[msid].vals[-1], color=plot_stylers.yellow, zorder=2)
                if force_limits is True:
                    ax.set_ylim(dashboard_limits[plotnum])

            if plotnum == 2:
                # Then this is the Bus Current plot. Overplot the CAUTION and WARNING limits
                ax.axhspan(2.3, 2.5, facecolor=plot_stylers.yellow, alpha=0.3)
                ax.axhspan(2.5, 3.5, facecolor=plot_stylers.red, alpha=0.3)
                # Also, save the latest bus current value for the suptitle
                latest_bus_current = data[msid].vals[-1]

            if plotnum == 10:
                ax.set_yscale('log')

            if missionwide is True:
                if plotnum == 11:
                    ax.set_yscale('log')

            ax.set_xlim(plot_start, plot_stop)
            ax.set_ylabel(dashboard_units[plotnum], color='slategray', size=8)

            if plotnum in range(8, 12):
                ax.set_xlabel('Date (UTC)', color='slategray', size=6)

            if missionwide is True:
                if plotnum == 0:
                    ax.text(event_times.time_of_cap_1543, ax.get_ylim()[
                            1], 'Side B Swap', fontsize=6, color='slategray')
                    ax.axvline(event_times.time_of_cap_1543,
                               color='gray', alpha=0.5)
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
        plt.suptitle(t='Latest Bus Current: {} DN ({} A) | Updated as of {} EST'.format(convert_bus_current_to_dn(latest_bus_current), np.round(
            latest_bus_current, 2),  dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=6)
    elif missionwide is True:
        plt.suptitle(t='Updated as of {} EST'.format(
            dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=6)

    if fig_save_directory is not None:
        # Then the user wants to save the figure
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


def make_ancillary_plots(fig_save_directory):

    five_days_ago = dt.date.today() - dt.timedelta(days=5)
    two_days_hence = dt.date.today() + dt.timedelta(days=2)

    fetch.data_source.set('cxc')
    make_realtime_plot(fig_save_directory=fig_save_directory, plot_start=dt.datetime(
        2000, 1, 4), plot_stop=None, sampling='daily', date_format=mdate.DateFormatter('%Y'), current_hline=True, missionwide=True, force_limits=True)

    print('Saved Mission-Wide Plots to {}'.format(
        fig_save_directory), end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    print('Updating Motor Plots', end="\r", flush=True)
    make_motor_plots(fig_save_directory=fig_save_directory, plot_start=five_days_ago,
                     plot_end=two_days_hence, sampling='full', date_format=mdate.DateFormatter('%m-%d'))
    print('Done', end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    print('Saved Motor Plots to {}'.format(
        fig_save_directory), end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    print('Updating Thermal Plots', end="\r", flush=True)
    make_thermal_plots(fig_save_directory=fig_save_directory)
    print('Done', end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    print('Saved Thermal Plots to {}'.format(
        fig_save_directory), end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

    plt.close('all')


def valid_date(s):
    try:
        return dt.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def parse_args():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--start', dest="plot_start",  type=valid_date,
                           required=False, help='The Start Date - format YYYY-MM-DD')
    argparser.add_argument('--stop', dest="plot_stop", type=valid_date,
                           required=False, help='The Start Date - format YYYY-MM-DD')
    argparser.add_argument('--sampling', choices=[
                           'full', '5min', 'daily'], required=False, default='full', help='Sampling to use instead of full resolution?')

    args = argparser.parse_args()

    return args


def main():
    # Enable this thing to run on the command line for on-demand plots with specific date ranges

    # Force a gui backend

    matplotlib.use('MacOSX', force=True)
    plot_stylers.styleplots()

    args = parse_args()
    # Args will just be datetimes
    if args.plot_start is not None:
        plot_start = args.plot_start
    elif args.plot_stop is None:
        plot_start = dt.date.today() - dt.timedelta(days=5)

    if args.plot_stop is not None:
        plot_stop = args.plot_stop
    elif args.plot_stop is None:
        plot_stop = dt.date.today() + dt.timedelta(days=2)

    make_realtime_plot(plot_start=plot_start, plot_stop=plot_stop,
                       current_hline=False, sampling=args.sampling, force_limits=False, show_in_gui=True)


if __name__ == '__main__':
    main()
