#!/usr/bin/env conda run -n ska3 python
from plot_stylers import *
from event_times import *
from msidlists import *
import pandas as pd
import numpy as np
import os
import sys
import shutil
import time
import pytz
import traceback

from Ska.engarchive import fetch_eng as fetch
import Chandra.Time

from astropy.table import Table

import datetime as dt
import matplotlib.dates as mdate
from matplotlib import gridspec

from chandratime import cxc2dt, convert_to_doy


import matplotlib.pyplot as plt
# plt.switch_backend('agg')


def make_motor_plots(counter=None, fig_save_directory='/Users/grant/Desktop/'):

    time_of_2022_anomaly = 760799927.93
    fetch.data_source.set('maude')

    plt.style.use('ggplot')
    labelsizes = 8
    # plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['font.size'] = labelsizes

    plt.rcParams['axes.titlesize'] = labelsizes
    plt.rcParams['axes.labelsize'] = labelsizes
    plt.rcParams['xtick.labelsize'] = labelsizes - 2
    plt.rcParams['ytick.labelsize'] = labelsizes - 2

    fig = plt.figure(figsize=(16, 6), constrained_layout=True)
    gs = fig.add_gridspec(3, 4)

    plotnum = -1
    for i in range(3):
        for j in range(4):
            ax = fig.add_subplot(gs[i, j])
            plotnum += 1
            for msid in motor_dashboard_msids[plotnum]:
                print(f'fetching {msid}')
                data = fetch.MSID(msid, start='2022:030', stop='2022:042')
                print(f'done')

                # plotting the absolute value here to ignore -1
                ax.plot((data.times - time_of_2022_anomaly), data.raw_vals,
                        markersize=1, label=msid, zorder=1, rasterized=True, alpha=0.8)

            ax.set_xlim(-80, 20)
            # ax.set_ylim(-0.2, 1.2)

            # ax.set_yticks([0, 1])
            # ax.set_yticklabels(['ENAB', 'DISAB'])

            ax.legend(prop={'size': 8}, loc=3)
            ax.set_title('{}'.format(
                motor_dashboard_tiles[plotnum]), color='slategray', loc='center')

    if counter is not None:
        plt.suptitle(t='Updated as of {} EST'.format(dt.datetime.now(
        ).strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=6)

    fig.savefig(fig_save_directory + 'motors.png',
                dpi=300, bbox_inches='tight')
    fig.savefig(fig_save_directory + 'motors.pdf',
                dpi=300, bbox_inches='tight')
    plt.close()
    fetch.data_source.set('cxc')


if __name__ == "__main__":
    make_motor_plots(fig_save_directory='/Users/grant/Desktop/')
