#!/usr/bin/env conda run -n ska3 python

import time
import argparse
from cheta import fetch_sci as fetch


import numpy as np
import datetime as dt
import matplotlib.pyplot as plt

from cxotime import CxoTime
from Chandra.Time import DateTime as chandraDateTime
from time_helpers import convert_to_doy

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
    fetch.data_source.set('maude allow_subset=False')

    msidlist = ['2IMTPAST', '2IMBPAST', '2IMHBLV',
                '2IMHVLV', '2CEAHVPT', '2TLEV1RT', '2VLEV1RT']

    telem = fetch.MSIDset(msidlist, start=telem_start)
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot((telem['2IMTPAST'].times - time_zero.secs) / 3600,
             telem['2IMTPAST'].vals, lw=weight, label='Top plate HV Step (2IMTPAST)')
    ax1.plot((telem['2IMBPAST'].times - time_zero.secs) / 3600,
             telem['2IMBPAST'].vals, lw=weight, label='Bottom plate HV Step (2IMBPAST)')
    # ax1.plot((telem['2IMHBLV'].times - time_zero.secs) / 3600,
    #          telem['2IMHBLV'].vals, lw=weight, label='Monitor Value 2IMHBLV')
    # ax1.plot((telem['2IMHVLV'].times - time_zero.secs) / 3600,
    #          telem['2IMHVLV'].vals, lw=weight, label='Monitor Value 2IMHVLV')

    ax1.set_ylabel('HRC-I Voltage Step / Monitor Value')

    ax2 = plt.subplot(2, 1, 2, sharex=ax1)

    ax2.plot((telem['2TLEV1RT'].times - time_zero.secs) / 3600,
             telem['2TLEV1RT'].vals, lw=0, marker='o', markersize=2, label='Total Event Rate (2TLEV1RT)')

    ax2.plot((telem['2VLEV1RT'].times - time_zero.secs) / 3600,
             telem['2VLEV1RT'].vals, lw=0, marker='o', markersize=2, label='Valid Event Rate (2VLEV1RT)')

    ax2.set_xlabel(f'Hours relative to CAP Start \n ({time_zero.date})')
    ax2.set_ylabel('Total & Valid Event Rates (cps)')

    # ax3 = ax2.twinx()
    # ax3.plot(telem['3FABRAAT'].times - time_zero.secs /
    #          3600, telem['3FABRAAT'].vals, label='FA6')

    # ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1],
    #         'Now', fontsize=6, color='slategray', zorder=3)
    # ax.axvline(dt.datetime.now(pytz.utc), color='gray', alpha=0.5)

    for ax in [ax1, ax2]:
        ax.set_xlim(-0.6, 2)
        if ax == ax1:
            ax.set_ylim(70, 100)
        if ax == ax2:
            ax.set_ylim(0, 200)
        ax.grid(False)
        # ax.axvline(0, color='slategray', alpha=0.5)
        # ax.text(0, ax.get_ylim()[
        #     1], 'CAP 1618 Start', ha='left', fontsize=8, color='slategray', zorder=3)
        nowtime = (CxoTime.now().secs - time_zero.secs)/3600
        ax.axvline(nowtime, color=comm_status_color, alpha=0.5)
        nowtext = ax.text(nowtime, ax.get_ylim()[
            1], 'Now (' + comm_status_text + ')', fontsize=8, color=comm_status_color, va='top', zorder=3)
        # Give the "now" label a white background because it's gonna overlap things...
        # nowtext.set_bbox(dict(facecolor='white', alpha=1.0, edgecolor='white'))

        ax.legend(prop={'size': 10}, loc='lower right')

        comm_start = time_zero.secs/3600 - time_zero.secs/3600
        comm_end = CxoTime('2024:157:20:35:00.000').secs - time_zero.secs

        ax.axvline(comm_start, color=plot_stylers.purple, alpha=0.5)
        ax.axvline(comm_end/3600, color=plot_stylers.purple, alpha=0.5)
        # ax.axvline(deadman/3600, color=plot_stylers.red, alpha=0.5)
        # ax.axvline(obs_start/3600, color=plot_stylers.green, alpha=0.5)

        ax.text(comm_start/3600, ax.get_ylim()
                [1], 'Activity Window START', color=plot_stylers.red, ha='left', fontsize=8)

        # ax.text(bot_start/3600, ax.get_ylim()
        #         [1], 'BOT', color=plot_stylers.red, ha='right', fontsize=8)

        ax.text(comm_end/3600, ax.get_ylim()
                [1], 'Comm End', color=plot_stylers.purple, ha='right', fontsize=8)

        # ax.text(obs_start/3600, ax.get_ylim()
        #         [1], 'Obs Start', color=plot_stylers.red, ha='right', fontsize=8)

    ax1.set_title(
        f'Iteration {iteration_count} | Updated as of {dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")}', fontsize=10, pad=10)

    plt.suptitle(comm_status_text, color=comm_status_color, fontsize=16)

    if save_path is not None:
        plt.savefig(save_path, dpi=300)

        if monitor is True:
            scp_file_to_hrcmonitor(
                file_to_scp=save_path, destination='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/cap1744.png')


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

    # old_telem = fetch.MSIDset(['2P15VAVL', '2N15VAVL', '2P05VAVL', '2P24VAVL', '2FHTRMZT', '2CHTRPZT'],
    #                           start=convert_to_doy(
    #     event_times.sideA_reset),
    #     stop=convert_to_doy(
    #     event_times.sideA_reset + dt.timedelta(days=1)))

    # old_times = (old_telem['2P15VBVL'].times -
    #              chandraDateTime(event_times.time_of_cap_1543).secs) / 3600

    # sideB_swap_telem = (old_telem, old_times)

    # msidlist = ['2P15VBVL', '2N15VBVL']

    telem_start = '2024:154'
    # time_zero = CxoTime.now()  # fake for testing
    time_zero = CxoTime('2024:157:19:05:00.000')  # CAP start

    iteration_count = 0

    # Current chandra time at script start is CxoTime.now().secs

    while True:

        iteration_count += 1

        if args.monitor is True:
            save_path = f'/Users/grant/Desktop/{iteration_count}_dashboard.png'
        elif args.monitor is False:
            save_path = None

        update_plot_kwargs = {'telem_start': telem_start,
                              'time_zero': time_zero,
                              'iteration_count': iteration_count,
                              'old_telem': None,
                              'save_path': save_path,
                              'monitor': args.monitor}

        drawnow(update_plot, stop_on_close=True,
                show_once=args.freeze, confirm=args.debug, **update_plot_kwargs)


if __name__ == '__main__':
    main()
