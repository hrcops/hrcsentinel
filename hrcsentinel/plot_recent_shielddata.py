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

fetch.data_source.set('maude allow_subset=False')

msidlist = ['2TLEV1RT', '2VLEV1RT', '2SHEV1RT']

plot_start = dt.date.today() - dt.timedelta(days=2)

fig, ax = plt.subplots(figsize=(10, 6))

for msid in msidlist:
    data = fetch.get_telem(msid, start=convert_to_doy(plot_start),sampling='full', max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
    # ax.plot(data[msid].times, data[msid].vals, label=msid)
    ax.plot_date(convert_chandra_time(data[msid].times), data[msid].vals, marker=None, linestyle='-', linewidth=1.5, label=msid)

# format = fetch.get_telem('CCSDSTMF', start=convert_to_doy(plot_start),sampling='full')
# fifo = fetch.get_telem('2FIFOAVR', start=convert_to_doy(plot_start),sampling='full')
# vcdu_major = fetch.get_telem('CVCMJCTR', start=convert_to_doy(plot_start),sampling='full')
# vcdu_minor = fetch.get_telem('CVCMNCTR', start=convert_to_doy(plot_start),sampling='full')

# ax2 = ax.twinx()
# # ax2.plot(format['CCSDSTMF'].times, format['CCSDSTMF'].vals, label='FIFO Resets', color=yellow)
# ax2.plot(fifo['2FIFOAVR'].times, fifo['2FIFOAVR'].vals, label='FIFO Resets', color=green)

# ax2.plot(vcdu_major['CVCMJCTR'].times, vcdu_major['CVCMJCTR'].vals, label='Major VCDU', color=green)
# # ax2.plot(vcdu_minor['CVCMNCTR'].times, vcdu_minor['CVCMNCTR'].vals, label='Major VCDU', color=yellow)

ax2 = ax.twiny()

ax2.plot(data['2SHEV1RT'].times/1e8, data['2SHEV1RT'].vals, label=msid, linewidth=0, marker=None)
ax2.set_xlabel(r'Chandra Time ($1\times10^{8}$)')
ax2.grid(None)
ax2.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))


ax.set_ylabel(r'Event Rates (counts s$^{-1}$)')
ax.set_xlabel('Date UTC')
# ax.set_yscale('log')
ax.legend()
plt.show()