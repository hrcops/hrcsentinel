#!/usr/bin/env conda run -n ska3 python
from plot_stylers import *
from event_times import *
from msidlists import *
from scipy.signal import hilbert
from scipy.interpolate import interp1d
from scipy.interpolate import spline
import pandas as pd
import numpy as np
import os
import sys
import shutil
import time
import pytz
import traceback

from Ska.engarchive import fetch_sci as fetch
import Chandra.Time

from astropy.table import Table

import datetime as dt
import pytz
import matplotlib.dates as mdate
from matplotlib import gridspec

from chandratime import convert_chandra_time, convert_to_doy


import matplotlib.pyplot as plt
plt.switch_backend('agg')


def make_motor_plots(counter=None, fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/', plot_start=dt.datetime(2020, 8, 31, 00), plot_end=dt.date.today() + dt.timedelta(days=2), sampling='full', current_hline=False, date_format=mdate.DateFormatter('%d %H'), force_limits=False, missionwide=False):

    fig = plt.figure(figsize=(17, 9))
    plotnum = -1
    for i in range(3):
        for j in range(4):
            ax = plt.subplot2grid((3, 4), (i, j))
            plotnum += 1
            for msid in motor_dashboard_msids[plotnum]:
                data = fetch.get_telem(
                    msid, start=convert_to_doy(plot_start), sampling=sampling, max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)

                print('Fetching from {} at {} resolution: {}'.format(
                    convert_to_doy(plot_start), sampling, msid), end='\r', flush=True)
                # Clear the command line manually
                sys.stdout.write("\033[K")

                ax.plot_date(convert_chandra_time(
                    data[msid].times), data[msid].raw_vals, markersize=1, label=msid, zorder=1, rasterized=True)

                # Plot a HORIZONTAL line at location of last data point.
                if current_hline is True:
                    ax.axhline(data[msid].vals[-1], color=green, zorder=2)

            ax.set_xlim(plot_start, plot_end)
            ax.set_ylabel(motor_dashboard_units[plotnum])

            ax.axvline(dt.datetime.now(pytz.utc),
                       color='gray', alpha=0.5)

            ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1],
                    'Now', fontsize=6, color='slategray')

            plt.gca().xaxis.set_major_formatter(date_format)

            plt.xticks(rotation=0)

            ax.legend(prop={'size': 8}, loc=3)
            ax.set_title('{}'.format(
                motor_dashboard_tiles[plotnum]), color='slategray', loc='center')

            if counter is not None:
                plt.suptitle(t='Iteration {} | Updated as of {} EST'.format(counter, dt.datetime.now(
                ).strftime("%Y-%b-%d %H:%M:%S")), y=0.99, color='slategray', size=6)

            fig.savefig(fig_save_directory + 'motors.png',
                        dpi=300, bbox_inches='tight')
            fig.savefig(fig_save_directory + 'motors.pdf',
                        dpi=300, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    make_motor_plots(fig_save_directory='/Users/grant/Desktop/')
