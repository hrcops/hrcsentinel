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

from Ska.engarchive import fetch_sci as fetch
import Chandra.Time

from astropy.table import Table

import datetime as dt
import pytz
import matplotlib.dates as mdate
from matplotlib import gridspec
from matplotlib.ticker import FormatStrFormatter

from chandratime import convert_chandra_time, convert_to_doy
import plot_stylers



def make_shield_plot(fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/'):

    fetch.data_source.set('maude allow_subset=False')

    msidlist = ['2TLEV1RT', '2VLEV1RT', '2SHEV1RT']
    namelist = ['Total Event Rate', 'Valid Event Rate', 'AntiCo Shield Rate']

    plot_start = dt.date.today() - dt.timedelta(days=2)

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, msid in enumerate(msidlist):
        data = fetch.get_telem(msid, start=convert_to_doy(plot_start),sampling='full', max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
        # ax.plot(data[msid].times, data[msid].vals, label=msid)
        ax.plot_date(convert_chandra_time(data[msid].times), data[msid].vals, marker=None, linestyle='-', linewidth=1.5, label=namelist[i])

    ax.set_ylabel(r'Event Rates (counts s$^{-1}$)')
    ax.set_xlabel('Date UTC')
    ax.set_yscale('symlog')
    ax.set_ylim(0, 2000000)
    ax.set_title('Recent Shield & Detector Rates', color='slategray', loc='center')
    ax.axhline(60000, color=plot_stylers.red, linestyle='-', linewidth=0.5)
    ax.legend(prop={'size': 10}, loc=2)

    plt.show()



if __name__ == "__main__":
    print('Updating Shield Plot...', end='')
    make_shield_plot()
    plt.show()
    print('Done', end='')