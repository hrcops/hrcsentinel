#!/usr/bin/env python

import Ska.engarchive.fetch as fetch
import Chandra.Time

import datetime as dt
import matplotlib.dates as mdate
from matplotlib import gridspec

import matplotlib.pyplot as plt

import numpy as np
import pandas as pd

from msidlists import *
from event_times import *
from plot_stylers import *

import pytz

from hrcsentinel import hrccore as hrc
hrc.styleplots()
labelsizes = 12
plt.rcParams['axes.titlesize'] = labelsizes
plt.rcParams['axes.labelsize'] = labelsizes
plt.rcParams['xtick.labelsize'] = labelsizes
plt.rcParams['ytick.labelsize'] = labelsizes


# allow_subset=True should let us draw more data points
fetch.data_source.set('cxc', 'maude allow_subset=True')


def update_plot():

    rasterized = True
    markersize = 1.0
    colors_to_use = [yellow, blue, green, red]

    hrcI_msids = ['2IMTPAST', '2IMBPAST', '2IMHBLV', '2IMHVLV']

    for msid, color in zip(hrcI_msids, colors_to_use):
        msid = fetch.MSID(msid, start='2021:045')
        times = hrc.convert_chandra_time(msid.times)
        vals = msid.vals
        ax1.plot_date(times, vals,
                      markersize=markersize, rasterized=rasterized, color=color,  label=msid.MSID)

    ax1.set_ylabel('HRC-I Voltage Step / Monitor Value')
    xmin = dt.datetime(2021, 2, 16, 0)
    # Use today's date, plus 2 days
    end_date = dt.date.today() + dt.timedelta(days=1)
    xmax = end_date
    ax1.set_xlim(xmin, xmax)
    ax1.set_ylim(-2, 130)
    # ax1.legend()

    # ax1.axvline(dt.datetime.now(pytz.utc),
    #             color='gray', alpha=0.5)

    ax2.axhline(-20, color='gray')
    ax2.axhline(-40, color=red)

    n_lines = len(temperature_msids)
    color_idx = np.linspace(0, 1, n_lines)

    for i, msid in zip(color_idx, temperature_msids):
        msid = fetch.MSID(msid, start='2021:045')

        times = hrc.convert_chandra_time(msid.times)

        if msid.unit == 'K':
            vals = msid.vals - 273.15
        else:
            vals = msid.vals

        if msid.content == 'hrc5eng':
            ax2.plot_date(times, vals, markersize=markersize,
                          rasterized=rasterized, color=plt.cm.tab20(i), label=msid.MSID)

    # lgnd = ax2.legend()
    # for i in range(len(lgnd.legendHandles)):
    #     lgnd.legendHandles[i]._legmarker.set_markersize(20)

    ax2.set_ylabel('Temperature (C)')

    ax2.set_xlim(xmin, xmax)

    ax2.set_ylim(-50, 50)

    rates = fetch.get_telem(['2TLEV1RT', '2VLEV1RT'], start='2021:045')
    rate_times = hrc.convert_chandra_time(rates['2TLEV1RT'].times)
    ax3.plot_date(
        rate_times, rates['2TLEV1RT'].vals, color=red, markersize=markersize)
    ax3.plot_date(hrc.convert_chandra_time(
        rates['2VLEV1RT'].times), rates['2VLEV1RT'].vals, color=blue, markersize=markersize)

    ax3.set_ylim(0, 400)
    ax3.set_ylabel(r'Total/Valid Event Rates (counts s$^{-1}$)')

    ax3.set_xlabel('Date (UTC)')
    ax1.text(xmin, 130, 'HRC-I Voltage Steps & Monitors',
             color='slategray', fontsize=12)
    ax2.text(xmin, 51, 'Temperatures', color='slategray', fontsize=12)
    ax3.text(xmin, 341, 'Event Rates',
             color='slategray', fontsize=12)


if __name__ == "__main__":
    plt.ion()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    # plt.tight_layout()
    counter = 0
    while True:
        # plt.clf()
        try:
            update_plot()
            counter += 1
            # plt.suptitle("Iteration {} | {}".format(counter, dt.datetime.now()))
            plt.pause(60)
            plt.draw()
        except Exception as e:
            print('MAUDE error')
            continue
