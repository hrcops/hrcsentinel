#!/usr/bin/env conda run -n ska3 python

import time
import argparse
from cheta import fetch_sci as fetch


import numpy as np
import datetime as dt
import matplotlib.pyplot as plt

from cxotime import CxoTime
from Chandra.Time import DateTime as chandraDateTime
from chandratime import convert_to_doy

from heartbeat import are_we_in_comm
from plot_helpers import drawnow, figure, scp_file_to_hrcmonitor
import plot_stylers
import event_times


def update_plot(telem_start, time_zero, iteration_count, old_telem=None, save_path=None, monitor=False):
    """ Uses Python's global scope """

    weight = 2.0
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
                '2FHTRMZT', '2CHTRPZT', '2LVPLATM', '2DTSTATT', '2SPINATM', '3FABRAAT'
                ]
    telem = fetch.MSIDset(msidlist, start=telem_start)
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot((telem['2P15VAVL'].times - time_zero.secs) / 3600,
             telem['2P15VAVL'].vals, lw=weight, label='+15V 2P15VAVL')
    ax1.plot((telem['2N15VAVL'].times - time_zero.secs) / 3600,
             telem['2N15VAVL'].vals, lw=weight, label='-15V 2N15VAVL (Dwell)')
    ax1.plot((telem['2P05VAVL'].times - time_zero.secs) / 3600,
             telem['2P05VAVL'].vals, lw=weight, label='+5V 2P05VAVL')
    ax1.plot((telem['2P24VAVL'].times - time_zero.secs) / 3600,
             telem['2P24VAVL'].vals, lw=weight, label='+24V 2P24VBVL')

    ax1.set_ylabel('Bus Voltages (V)')

    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    ax2.plot((telem['2CHTRPZT'].times - time_zero.secs) / 3600,
             telem['2CHTRPZT'].vals, lw=weight, label='CEA Temperature 2CHTRPZT')
    ax2.plot((telem['2FHTRMZT'].times - time_zero.secs) / 3600,
             telem['2FHTRMZT'].vals, lw=weight, label='FEA Temperature 2FHTRMZT')
    ax2.plot((telem['2LVPLATM'].times - time_zero.secs) / 3600,
             telem['2LVPLATM'].vals, lw=weight, label='LV Plate 2LVPLATM')

    # ax2.plot((telem['2SPINATM'].times - time_zero.secs) / 3600,
    #          telem['2SPINATM'].vals, lw=weight, label='2SPINATM')

    # ax2.plot((telem['2DTSTATT'].times - time_zero.secs) / 3600,
    #          telem['2DTSTATT'].vals, lw=weight, label='2DTSTATT')

    ax2.set_xlabel(f'Hours relative to CAP Start \n ({time_zero.date})')
    ax2.set_ylabel('CEA & FEA Temperature (C)')

    # ax3 = ax2.twinx()
    # ax3.plot(telem['3FABRAAT'].times - time_zero.secs /
    #          3600, telem['3FABRAAT'].vals, label='FA6')

    # ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1],
    #         'Now', fontsize=6, color='slategray', zorder=3)
    # ax.axvline(dt.datetime.now(pytz.utc), color='gray', alpha=0.5)

    if old_telem is not None:
        reftime = chandraDateTime(event_times.sideA_reset).secs

        ax1.plot((old_telem['2P05VAVL'].times - reftime) / 3600, old_telem['2P05VAVL'].vals,
                 color='gray', alpha=0.1, zorder=1, label='2020 Side A Restart')
        ax1.plot((old_telem['2P15VAVL'].times - reftime) / 3600, old_telem['2P15VAVL'].vals,
                 color='gray', alpha=0.1, zorder=1)
        ax1.plot((old_telem['2N15VAVL'].times - reftime) / 3600, old_telem['2N15VAVL'].vals,
                 color='gray', alpha=0.1, zorder=1)

        ax2.plot((old_telem['2CHTRPZT'].times - reftime) / 3600, old_telem['2CHTRPZT'].vals,
                 color='gray', alpha=0.1, zorder=1, label='2020 Side A Restart')
        ax2.plot((old_telem['2FHTRMZT'].times - reftime) / 3600,
                 old_telem['2FHTRMZT'].vals, color='gray', alpha=0.1, zorder=1)

    for ax in [ax1, ax2]:
        ax.set_xlim(-1, 3.5)
        if ax == ax1:
            ax.set_ylim(-16, 16)
        if ax == ax2:
            ax.set_ylim(-12, 10)
        ax.grid(False)
        ax.axvline(0, color='slategray', alpha=0.5)
        ax.text(0, ax.get_ylim()[
            1], 'CAP 1618 Start', ha='left', fontsize=8, color='slategray', zorder=3)
        nowtime = (CxoTime.now().secs - time_zero.secs)/3600
        ax.axvline(nowtime, color=comm_status_color, alpha=0.5)
        nowtext = ax.text(nowtime, ax.get_ylim()[
            1], 'Now (' + comm_status_text + ')', fontsize=8, color=comm_status_color, va='top', zorder=3)
        # Give the "now" label a white background because it's gonna overlap things...
        # nowtext.set_bbox(dict(facecolor='white', alpha=1.0, edgecolor='white'))

        ax.legend(prop={'size': 10}, loc='lower right')

        bot_start = CxoTime('2022:213:18:10:00').secs - time_zero.secs
        maneuver = CxoTime('2022:213:18:00:14').secs - time_zero.secs

        comm_end = CxoTime('2022:213:21:10:00').secs - time_zero.secs

        ax.axvline(bot_start/3600, color=plot_stylers.red, alpha=0.5)
        ax.axvline(comm_end/3600, color=plot_stylers.purple, alpha=0.5)

        ax.axvline(maneuver/3600, color=plot_stylers.red, alpha=0.5)

        ax.text(bot_start/3600, ax.get_ylim()
                [1], 'BOT', color=plot_stylers.red, ha='left', fontsize=8)

        ax.text(comm_end/3600, ax.get_ylim()
                [1], 'EOT', color=plot_stylers.purple, ha='right', fontsize=8)

        ax.text(maneuver/3600, ax.get_ylim()
                [1], 'LETG Insert', color=plot_stylers.red, ha='right', fontsize=8)

    ax1.set_title(
        f'Iteration {iteration_count} | Updated as of {dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")}', fontsize=10, pad=10)

    plt.suptitle(comm_status_text, color=comm_status_color, fontsize=16)

    if save_path is not None:
        plt.savefig(save_path, dpi=300)

        if monitor is True:
            scp_file_to_hrcmonitor(
                file_to_scp=save_path, destination='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/cap1618.png')


figure(figsize=(12, 8))


def parse_args():

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--freeze', action='store_true')
    argparser.add_argument('--monitor', action='store_true',
                           help='Save every iteration as a PNG and SCP it to HRCmonitor')
    argparser.add_argument('--debug', action='store_true')

    args = argparser.parse_args()

    return args


def main():

    args = parse_args()

    fetch.data_source.set('maude allow_subset=False highrate=True')
    plot_stylers.styleplots(labelsizes=12)

    old_telem = fetch.MSIDset(['2P15VAVL', '2N15VAVL', '2P05VAVL', '2P24VAVL', '2FHTRMZT', '2CHTRPZT'],
                              start=convert_to_doy(
        event_times.sideA_reset),
        stop=convert_to_doy(
        event_times.sideA_reset + dt.timedelta(days=1)))

    # old_times = (old_telem['2P15VBVL'].times -
    #              chandraDateTime(event_times.time_of_cap_1543).secs) / 3600

    # sideB_swap_telem = (old_telem, old_times)

    # msidlist = ['2P15VBVL', '2N15VBVL']

    telem_start = '2022:213'
    # time_zero = CxoTime.now()  # fake for testing
    time_zero = CxoTime('2022:213:18:34:55')  # CAP start

    iteration_count = 0

    # Current chandra time at script start is CxoTime.now().secs

    while True:

        iteration_count += 1

        if args.monitor is True:
            save_path = f'/Users/grant/Desktop/cap1618_plots/{iteration_count}_dashboard.png'
        elif args.monitor is False:
            save_path = None

        update_plot_kwargs = {'telem_start': telem_start,
                              'time_zero': time_zero,
                              'iteration_count': iteration_count,
                              'old_telem': old_telem,
                              'save_path': save_path,
                              'monitor': args.monitor}

        drawnow(update_plot, stop_on_close=True,
                show_once=args.freeze, confirm=args.debug, **update_plot_kwargs)


if __name__ == '__main__':
    main()
