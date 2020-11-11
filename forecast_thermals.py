#!/usr/bin/env conda run -n ska3 python
#!/usr/bin/env conda run -n ska3 python
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

import matplotlib.pyplot as plt
plt.switch_backend('agg')

import numpy as np
import pandas as pd

import numpy as np
from scipy.interpolate import spline
from scipy.interpolate import interp1d
from scipy.signal import hilbert


from msidlists import *
from event_times import *
from plot_stylers import *




def convert_chandra_time(rawtimes):
    """
    Convert input CXC time (seconds since 1998.0) to the time base required for
    the matplotlib plot_date function (days since start of the Year 1 A.D).
    """

    # rawtimes is in units of CXC seconds, or seconds since 1998.0
    # Compute the Delta T between 1998.0 (CXC's Epoch) and 1970.0 (Unix Epoch)

    seconds_since_1998_0 = rawtimes[0]

    cxctime = dt.datetime(1998, 1, 1, 0, 0, 0)
    unixtime = dt.datetime(1970, 1, 1, 0, 0, 0)

    # Calculate the first offset from 1970.0, needed by matplotlib's plotdate
    # The below is equivalent (within a few tens of seconds) to the command
    # t0 = Chandra.Time.DateTime(times[0]).unix
    delta_time = (cxctime - unixtime).total_seconds() + seconds_since_1998_0

    plotdate_start = mdate.epoch2num(delta_time)

    # Now we use a relative offset from plotdate_start
    # the number 86,400 below is the number of seconds in a UTC day

    chandratime = (np.asarray(rawtimes) -
                   rawtimes[0]) / 86400. + plotdate_start

    return chandratime



def compute_yearly_average(values, window):

    array = values

    cumulative_sum, moving_aves = [0], []

    for i, x in enumerate(array, 1):
        cumulative_sum.append(cumulative_sum[i-1] + x)
        if i >= window:
            moving_ave = (cumulative_sum[i] - cumulative_sum[i-window])/window
            # can do stuff with moving_ave here
            moving_aves.append(moving_ave)

    # Ensure that this is a Numpy array, so that we can do some proper vector math with it.
    moving_ave_array = np.asarray(moving_aves)
    return moving_ave_array


def make_thermal_plots(counter=None):

    fig_save_directory = '/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/'

    # Fetch all MSIDs
    msids_daily = fetch.Msidset(
        monitor_temperature_msids, start='2000:001', stat='daily', filter_bad=True)
    msids_5min = fetch.MSIDset(
        monitor_temperature_msids, start='2000:001', stat='5min', filter_bad=True)

    ave_table = Table()  # Instantiate an empty AstroPy table that we can later sort

    daybin = 100  # The number of days over which we'll compute the rolling average

    all_names = []
    all_means = []
    all_stds = []

    for msid in monitor_temperature_msids:
        mean = np.mean(msids_daily[msid].means[-daybin:]).round(2)
        std = np.std(msids_daily[msid].stds[-daybin:]).round(2)

        all_names.append(msid)
        all_means.append(mean)
        all_stds.append(std)

    ave_table["MSID"] = all_names
    ave_table["{} Day Average".format(daybin)] = all_means
    ave_table["Standard Deviation"] = all_stds

    ave_table.sort("{} Day Average".format(daybin))

    ordered_msidlist = ave_table["MSID"]

    window = 365  # days, i.e. a year
    # Because this funtion will cut off the first 364 datapoints if your window is 365 days
    time_corrector = window - 1

    all_trends = {}

    for msid in ordered_msidlist:
        moving_aves = compute_yearly_average(msids_daily[msid].means, window)
        moving_stds = compute_yearly_average(msids_daily[msid].stds, window)
        all_trends["{}_trend".format(msid)] = moving_aves
        all_trends["{}_stds".format(msid)] = moving_stds

    # Make Figure 1

    # Make this True to ensure the file size is small. Otherwise you're plotting thousands of vector points.
    rasterized = True

    fig, ax = plt.subplots(figsize=(16, 8))

    n_lines = len(ordered_msidlist)
    color_idx = np.linspace(0, 1, n_lines)

    for i, msid in zip(color_idx, ordered_msidlist):

        print('Plotting daily thermals for {}'.format(msid), end='\r', flush=True)
        # Clear the command line manually
        sys.stdout.write("\033[K")
        ax.plot_date(convert_chandra_time(msids_daily[msid].times),
                     msids_daily[msid].means, '.', alpha=1.0, markersize=2.5, label='{}'.format(msid), color=plt.cm.RdYlBu_r(i),  rasterized=rasterized)

        # Draw a large point line where the current data point is
        with fetch.data_source('maude'):
            latest_datapoint = fetch.Msid(msid)
            ax.plot_date(convert_chandra_time(latest_datapoint.times)[
                         -1], latest_datapoint.vals[-1], markersize=8, color=plt.cm.RdYlBu_r(i), rasterized=rasterized, zorder=4)



    ax.set_ylabel("Temperature (C)", fontsize=10)
    ax.set_xlabel("Date", fontsize=10)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    ax.set_ylim(0, 40)

    # ax.set_xlim(dt.date(2018, 10, 6), dt.date(2018, 10, 30))

    if counter is not None:
        ax.set_title('HRC Thermistor MSIDs (Daily Means) | Iteration {} | Updated as of {} EST'.format(
            counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=10)
    else:
        ax.set_title(
            "HRC Thermistor Temperatures (Daily Averages) Over the Mission Lifetime", color='slategray', size=6)
    # ax.legend()
    # ax.set_ylim(10, 40)
    ax.legend(prop={'size': 13}, loc='center left',
              bbox_to_anchor=(1, 0.5))

    # ax.legend(loc=2, prop={'size': 13})

    ax.axvline(dt.datetime.now(pytz.utc),
               color='gray', alpha=0.5)
    ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1]+0.3,
            'Now', fontsize=10, color='slategray')

    fig.savefig(fig_save_directory + 'thermals.png', dpi=300, bbox_inches='tight')
    fig.savefig(fig_save_directory + 'thermals.pdf', dpi=300, bbox_inches='tight')

    plt.close()



    # Make Figure 2

    fetch.data_source.set('cxc')

    fig, ax = plt.subplots(figsize=(17, 8))

    n_lines = len(ordered_msidlist)
    color_idx = np.linspace(0, 1, n_lines)

    for i, msid in zip(color_idx, ordered_msidlist):

        print('Plotting thermal trends for {}'.format(msid), end='\r', flush=True)
        # Clear the command line manually
        sys.stdout.write("\033[K")

        times = convert_chandra_time(msids_daily[msid].times)
        # ax.plot(all_trends["{}_trend".format(msidname)], lw=3.0, label=msidname, color=plt.cm.coolwarm(i))
        ax.plot_date(times[time_corrector:], all_trends["{}_trend".format(
            msid)], '-', label='{}'.format(msid), lw=3.0, color=plt.cm.RdYlBu_r(i), rasterized=rasterized)
        ax.fill_between(times[time_corrector:], all_trends["{}_trend".format(msid)] + all_trends["{}_stds".format(
            msid)], all_trends["{}_trend".format(msid)] - all_trends["{}_stds".format(msid)], facecolor='gray', alpha=0.4)

        # Draw a large point line where the current data point is
        with fetch.data_source('maude'):
            latest_datapoint = fetch.Msid(msid)
            ax.plot_date(convert_chandra_time(latest_datapoint.times)[
                         -1], latest_datapoint.vals[-1], markersize=8, color=plt.cm.RdYlBu_r(i), rasterized=rasterized, zorder=4)

    ax.legend(prop={'size': 13}, loc='center left',
              bbox_to_anchor=(1, 0.5))
    # plt.legend(title='title', bbox_to_anchor=(1.05, 1), loc='upper left')

    if counter is not None:
        ax.set_title('Moving Average Thermal Trends | Iteration {} | Updated as of {} EST'.format(
            counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=10)
    else:
        ax.set_title(
            "HRC Thermistor Temperatures (Moving Averages) Over the Mission Lifetime", color='slategray', size=6)

    ax.set_ylabel("Temperature (C)", fontsize=10)
    ax.set_xlabel("Date", fontsize=10)

    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    ax.axvline(dt.datetime.now(pytz.utc),
               color='gray', alpha=0.5)

    ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1]+0.3,
            'Now', fontsize=10, color='slategray')

    ax.set_xlim(dt.datetime(2001, 1, 1), dt.datetime(2022, 1, 1))

    fig.savefig(fig_save_directory + 'thermal_trends.png', dpi=300, bbox_inches='tight')
    fig.savefig(fig_save_directory + 'thermal_trends.pdf', dpi=300, bbox_inches='tight')

    plt.close()

if __name__ == "__main__":
    print('Updating Thermal Plots...', end='')
    make_thermal_plots()
    plt.show()
    print('Done', end='')
