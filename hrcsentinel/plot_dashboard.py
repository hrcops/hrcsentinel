#!/usr/bin/env conda run -n ska3 python

import argparse
import datetime as dt
import sys

import matplotlib.dates as mdate
import matplotlib.pyplot as plt
import numpy as np
import pytz

try:
    from cheta import fetch
    from kadi import events
except ImportError:
    sys.exit("Failed to import cheta (aka ska). Make sure you're using the latest version of the ska runtime environment (and that you have the conda environment initialized!).")

import event_times
import msidlists
import plot_stylers
from chandratime import convert_to_doy, cxctime_to_datetime
from monitor_comms import convert_bus_current_to_dn
from plot_motors import make_motor_plots
from plot_rates import make_shield_plot
from plot_thermals import make_thermal_plots
from heartbeat import timestamp_string


def comm_status_stamp(comm_status, code_start_time, hostname, fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/', debug_prints=False) -> None:
    '''
    Make the comm status stamp
    '''

    if comm_status is True:
        commreport = f'In Comm!'
        subtext = f"Comm appears to have started at {dt.datetime.now(tz=pytz.timezone('US/Eastern')).strftime('%Y %b %d %H:%M:%S')}"
        textcolor = 'steelblue'
    elif comm_status is False:

        commreport = 'Not in Comm'
        # and (try to) figure out when the next comm is:
        # comm_fetch_success, next_comm_string = calc_time_to_next_comm(
        #     debug_prints=debug_prints)

        comm_fetch_success = False

        if comm_fetch_success:
            subtext = f'Next Comm should be in {next_comm_string}'
        elif not comm_fetch_success:
            subtext = ''
        textcolor = 'slategray'

    code_uptime = dt.datetime.now(
        tz=pytz.timezone('US/Eastern')) - code_start_time

    fig = plt.figure(figsize=(8, 2))
    plt.axis('off')
    plt.tight_layout()
    fig.patch.set_facecolor('white')

    text = plt.text(0.001, 0.2, commreport, color=textcolor, fontsize=50)
    subtext = plt.text(
        0.004, 0.08, subtext, color=textcolor, fontsize=12)
    uptime_text = plt.text(
        0.004, 0.0001, 'HRCMonitor has been running on {} since {} ({} days)'.format(hostname, code_start_time.strftime("%Y %b %d %H:%M:%S"), code_uptime.days), color='slategray', fontsize=9)

    plt.savefig(fig_save_directory + 'comm_status.png', dpi=300)
    plt.close('all')


def make_realtime_plot(counter=None, plot_start=dt.datetime(2020, 8, 31, 00), plot_stop=dt.date.today() + dt.timedelta(days=2), sampling='full', current_hline=False, date_format=mdate.DateFormatter('%d %H'), force_limits=False, missionwide=False, fig_save_directory=None, show_in_gui=False, use_cheta=False) -> None:
    plotnum = -1

    fig = plt.figure(figsize=(16, 6), constrained_layout=True)
    gs = fig.add_gridspec(3, 4)
    # gridspec rocks

    if (sampling == 'full') and (use_cheta is False):
        fetch.data_source.set('maude allow_subset=False')

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

    # we're making a 4x3 plot using gridspec (see above)
    for i in range(3):
        for j in range(4):
            ax = fig.add_subplot(gs[i, j])
            plotnum += 1
            for msid in dashboard_msids[plotnum]:

                data = fetch.get_telem(msid, start=convert_to_doy(
                    plot_start), sampling=sampling, max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)

                print(
                    f'({timestamp_string()}) Fetching from {convert_to_doy(plot_start)} at {sampling} resolution: {msid}', end='\r', flush=True)
                # Clear the command line manually
                sys.stdout.write("\033[K")

                if sampling == 'full':
                    ax.plot_date(cxctime_to_datetime(
                        data[msid].times), data[msid].vals, markersize=1, label=msid, zorder=1, rasterized=True)
                elif sampling == 'daily':
                    # Then plot the means
                    ax.plot_date(cxctime_to_datetime(
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

            if missionwide is False:
                # Then add labels
                ax.text(dt.datetime.now(tz=pytz.timezone('US/Eastern')), ax.get_ylim()[1],
                        'Now', fontsize=6, color='slategray', zorder=3)
                ax.axvline(dt.datetime.now(tz=pytz.timezone(
                    'US/Eastern')), color='gray', alpha=0.5)

                if plotnum == 11:
                    try:
                        # then this is the Pitch plot, and I want to underplot spacecraft pitch
                        fifo_resets = fetch.get_telem('2FIFOAVR', start=convert_to_doy(
                            plot_start), sampling=sampling, max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
                        format_changes = fetch.get_telem('CCSDSTMF', start=convert_to_doy(
                            plot_start), sampling=sampling, max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
                        ax_resets = ax.twinx()
                        ax_resets.plot_date(cxctime_to_datetime(
                            fifo_resets['2FIFOAVR'].times), fifo_resets['2FIFOAVR'].vals, linewidth=0.5, marker=None, fmt="", alpha=0.7,  color=plot_stylers.blue, label='FIFO Reset', zorder=0, rasterized=True)
                        ax_resets.plot_date(cxctime_to_datetime(format_changes['CCSDSTMF'].times), format_changes['CCSDSTMF'].vals,
                                            linewidth=0.5, marker=None, fmt="", alpha=0.7,  color=plot_stylers.purple, label='Format Changes', zorder=0, rasterized=True)
                        ax_resets.tick_params(labelright='off')
                        ax_resets.set_yticks([])
                        ax_resets.legend(prop={'size': 8}, loc=3)
                    except ValueError:
                        continue

            # Do mission-wide tweaking
            elif missionwide is True:
                if plotnum == 0:
                    # Fetch the Side A Bus Data, anomaly and all :(
                    voltage_msids_a = ['2P24VAVL',  # 24 V bus EED voltage,
                                       '2P15VAVL',  # +15 V bus EED voltage
                                       '2P05VAVL',  # +05 V bus EED voltage
                                       '2N15VAVL'  # +15 V bus EED voltage
                                       ]
                    for msid in voltage_msids_a:
                        a_side_voltages = fetch.get_telem(msid, start=convert_to_doy(plot_start), stop=convert_to_doy(
                            event_times.time_of_cap_1543), sampling=sampling, max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
                        ax.plot_date(cxctime_to_datetime(a_side_voltages[msid].times), a_side_voltages[msid].means,
                                     color=plot_stylers.green, markersize=0.3, alpha=0.3, label=msid, zorder=1, rasterized=True)

                    # Label the B-side swap (Aug 2020)
                    ax.text(event_times.time_of_cap_1543, ax.get_ylim()[
                            1], 'Side B Swap', fontsize=6, color='slategray')
                    ax.axvline(event_times.time_of_cap_1543,
                               color='gray', alpha=0.5)

                if plotnum == 11:
                    # then we're plotting AntiCo shield rate, not pitch, so log it
                    ax.set_yscale('symlog')

            if plotnum == 2:
                # Then this is the Bus Current plot. Overplot the CAUTION and WARNING limits
                ax.axhspan(2.3, 2.5, facecolor=plot_stylers.yellow, alpha=0.3)
                ax.axhspan(2.5, 3.5, facecolor=plot_stylers.red, alpha=0.3)
                # Also, save the latest bus current value for the suptitle
                latest_bus_current = data[msid].vals[-1]

            if plotnum == 10:
                # then this is the shield/det event rate plot and it's better in log y
                ax.set_yscale('symlog')

            # Set all limits
            ax.set_xlim(plot_start, plot_stop)
            ax.set_ylabel(dashboard_units[plotnum], color='slategray', size=8)

            if plotnum in range(8, 12):
                # Only label the x axes of the bottom row of plots
                ax.set_xlabel('Date (UTC)', color='slategray', size=6)

            # Set everything to our preferred date format
            plt.gca().xaxis.set_major_formatter(date_format)

            plt.xticks(rotation=0)

            if plotnum != 0:
                # Legend gets too busy on the Bus Voltage plot
                ax.legend(prop={'size': 8}, loc=2)
            ax.set_title('{}'.format(
                dashboard_tiles[plotnum]), color='slategray', loc='center')

    # Title the top of the figure
    if missionwide is False:
        plt.suptitle(t='Latest Bus Current: {} DN ({} A) | Updated as of {} EST'.format(convert_bus_current_to_dn(latest_bus_current), np.round(
            latest_bus_current, 2),  dt.datetime.now(tz=pytz.timezone('US/Eastern')).strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=6)
    elif missionwide is True:
        plt.suptitle(t='Updated as of {} EST'.format(
            dt.datetime.now(tz=pytz.timezone('US/Eastern')).strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=6)

    if fig_save_directory is not None:
        # Then the user wants to save the figure
        if missionwide is False:
            plt.savefig(fig_save_directory + 'status.png', dpi=300)
            plt.savefig(fig_save_directory + 'status.pdf',
                        dpi=300)
        elif missionwide is True:
            plt.savefig(fig_save_directory + 'status_wide.png', dpi=300)
            plt.savefig(fig_save_directory + 'status_wide.pdf',
                        dpi=300)

    if show_in_gui:
        plt.show(block=False)

    plt.close()


def make_ancillary_plots(fig_save_directory, show_in_gui=False):
    '''
    Create the thermal and motor plots
    '''

    five_days_ago = dt.date.today() - dt.timedelta(days=5)
    two_days_hence = dt.date.today() + dt.timedelta(days=2)

    fetch.data_source.set('maude allow_subset=True')
    print('Updating Event Rates Plot', end="\r", flush=True)
    make_shield_plot(fig_save_directory=fig_save_directory,
                     plot_start=five_days_ago, plot_stop=two_days_hence, show_in_gui=show_in_gui)
    print('Done', end="\r", flush=True)
    # Clear the command line manually
    sys.stdout.write("\033[K")

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
    parser = argparse.ArgumentParser()

    parser.add_argument('--start', dest="plot_start",  type=valid_date,
                        required=False, help='The Start Date - format YYYY-MM-DD')
    parser.add_argument('--stop', dest="plot_stop", type=valid_date,
                        required=False, help='The Start Date - format YYYY-MM-DD')
    parser.add_argument('--sampling', choices=[
        'full', '5min', 'daily'], required=False, default='full', help='Sampling to use instead of full resolution?')

    parser.add_argument('--use_cheta', action='store_true')

    parser.add_argument('--force_limits', action='store_true')

    args = parser.parse_args()

    return args


def main() -> None:
    # Enable this thing to run on the command line for on-demand plots with specific date ranges

    # Force a gui backend
    # matplotlib.use('MacOSX', force=True)
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

    if args.use_cheta:
        fetch.data_source.set('cxc')

    make_realtime_plot(plot_start=plot_start, plot_stop=plot_stop,
                       current_hline=False, sampling=args.sampling, force_limits=args.force_limits, show_in_gui=True, use_cheta=args.use_cheta)


if __name__ == '__main__':
    main()
