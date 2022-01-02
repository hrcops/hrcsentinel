#!/usr/bin/env conda run -n ska3 python

import numpy as np
import matplotlib.dates as mdate
import datetime as dt


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


def convert_kadi_time(rawtime):
    """[summary]

    Args:
        rawtime (str): A string of time in the format: 2021:347:17:35:14.442
    """

    datetime_object = "blah"

    return datetime_object


def convert_to_doy(datetime_start):
    '''
    Return a string like '2020:237' that will be passed to start= in
    fetch.get_telem() and fetch.MSID(). Note that you have to zero-pad the day
    number e.g. 2020:002 instead of 2020:2, otherwise the pull will fail.
    '''

    year = datetime_start.year
    day_of_year = datetime_start.timetuple().tm_yday

    # you have to zero-pad the day number!
    doystring = '{}:{:03d}'.format(year, day_of_year)

    return doystring
