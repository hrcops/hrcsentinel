#!/usr/bin/env conda run -n ska3 python

import time
import pytz
import argparse
from cheta import fetch_sci as fetch
import socket

import numpy as np
import datetime as dt
import matplotlib
import matplotlib.pyplot as plt

from cxotime import CxoTime
from Chandra.Time import DateTime as chandraDateTime

from heartbeat import are_we_in_comm
from plot_helpers import drawnow, figure, scp_file_to_hrcmonitor
import plot_stylers
import event_times

from global_configuration import allowed_hosts
from heartbeat import timestamp_string
from chandratime import convert_to_doy, cxctime_to_datetime


def update_plot(telem_start, iteration_count, save_path=None):
    """ Uses Python's global scope """

    weight = 0.5
    in_comm = are_we_in_comm(cadence=0)
    if in_comm:
        comm_status_text = 'IN COMM'
        comm_status_color = plot_stylers.green

    elif not in_comm:
        comm_status_text = 'NOT IN COMM'
        comm_status_color = plot_stylers.red

    # heartbeat.py currently resets to remove the highrate=True flag. You need to reset!
    fetch.data_source.set('maude allow_subset=False highrate=True')

    msidlist = ['2P15VAVL', '2N15VAVL', '2P05VAVL', '2P24VAVL',
                '2FHTRMZT', '2CHTRPZT', '2LVPLATM', '2DTSTATT', '2SPINATM', '3FABRAAT', '2CEAHVPT',
                ]
    print(f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) Fetching telemetry...', end='\r')
    telem = fetch.MSIDset(msidlist, start=telem_start)

    ax1 = plt.subplot(2, 1, 1)

    ax1.plot_date(cxctime_to_datetime(telem['2P15VAVL'].times), telem['2P15VAVL'].vals,
                  markersize=weight, label='+15V 2P15VAVL')
    ax1.plot_date(cxctime_to_datetime(telem['2N15VAVL'].times),
                  telem['2N15VAVL'].vals, markersize=weight, label='-15V 2N15VAVL')
    ax1.plot_date(cxctime_to_datetime(telem['2P05VAVL'].times),
                  telem['2P05VAVL'].vals, markersize=weight, label='+5V 2P05VAVL')
    ax1.plot_date(cxctime_to_datetime(telem['2P24VAVL'].times),
                  telem['2P24VAVL'].vals, markersize=weight, label='+24V 2P24VBVL')

    ax1.set_ylabel('Bus Voltages (V)')

    ax2 = plt.subplot(2, 1, 2, sharex=ax1)

    ax2.plot_date(cxctime_to_datetime(telem['2CEAHVPT'].times),
                  telem['2CEAHVPT'].vals, markersize=weight, label='2CEAHVPT')

    ax2.plot_date(cxctime_to_datetime(telem['2CHTRPZT'].times),
                  telem['2CHTRPZT'].vals, markersize=weight, label='CEA Temperature 2CHTRPZT')
    ax2.plot_date(cxctime_to_datetime(telem['2FHTRMZT'].times),
                  telem['2FHTRMZT'].vals, markersize=weight, label='FEA Temperature 2FHTRMZT')
    ax2.plot_date(cxctime_to_datetime(telem['2LVPLATM'].times),
                  telem['2LVPLATM'].vals, markersize=weight, label='LV Plate 2LVPLATM')

    ax2.set_xlabel(f'Date')
    ax2.set_ylabel('CEA & FEA Temperature (C)')

    ax2.axhline(10, color=plot_stylers.red,
                linestyle='--', label='CUT OFF LIMIT')

    for ax in [ax1, ax2]:
        ax.set_xlim(dt.datetime.now() - dt.timedelta(hours=12),
                    dt.datetime.now() + dt.timedelta(hours=8))
        if ax == ax1:
            ax.set_ylim(-20, 25)
        if ax == ax2:
            ax.set_ylim(-12, 15)
        ax.grid(False)
        # ax.axvline(0, color='slategray', alpha=0.5)
        # ax.text(0, ax.get_ylim()[
        #     1], 'CAP 1618 Start', ha='left', fontsize=8, color='slategray', zorder=3)

        # Give the "now" label a white background because it's gonna overlap things...
        # nowtext.set_bbox(dict(facecolor='white', alpha=1.0, edgecolor='white'))

        ax.text(dt.datetime.now(tz=pytz.timezone('US/Eastern')), ax.get_ylim()[1],
                f'Now ({timestamp_string()})', fontsize=10, color='slategray', zorder=3)
        ax.axvline(dt.datetime.now(tz=pytz.timezone(
            'US/Eastern')), color='gray', alpha=0.5)

        ax.legend(prop={'size': 10}, loc='lower right')

    ax1.set_title(
        f'Last 12h of telemetry | Iteration {iteration_count} | Updated as of {dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")}', fontsize=10, pad=10)

    plt.suptitle(comm_status_text, color=comm_status_color, fontsize=16)

    if save_path is not None:
        plt.savefig(save_path, dpi=300)


figure(figsize=(12, 8))


def get_args():

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--freeze', action='store_true')
    argparser.add_argument('--monitor', action='store_true',
                           help='Save every iteration as a PNG and SCP it to HRCmonitor')
    argparser.add_argument('--debug', action='store_true')

    args = argparser.parse_args()

    return args


def main():

    args = get_args()

    # split is to get rid of .local or .cfa.harvard.edu
    hostname = socket.gethostname().split('.')[0]

    args = get_args()

    if hostname in allowed_hosts:
        fig_save_directory = allowed_hosts[hostname]
        print(f'({timestamp_string()}) Recognized host: {hostname}. Plots will be saved to {fig_save_directory}')

    plt.ion()
    fetch.data_source.set('maude allow_subset=False highrate=True')
    plot_stylers.styleplots(labelsizes=12)

    # Grab telemetry starting from 24 hours ago
    one_day_ago = dt.datetime.now() - dt.timedelta(days=1)
    telem_start = convert_to_doy(one_day_ago)

    iteration_count = 0

    # Current chandra time at script start is CxoTime.now().secs

    while True:

        iteration_count += 1

        update_plot_kwargs = {'telem_start': telem_start,
                              'iteration_count': iteration_count,
                              'save_path': fig_save_directory}

        drawnow(update_plot, stop_on_close=True,
                show_once=args.freeze, confirm=args.debug, **update_plot_kwargs)


if __name__ == '__main__':
    # matplotlib.use('MacOSX', force=True)
    main()
