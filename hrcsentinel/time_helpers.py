#!/usr/bin/env conda run -n ska3 python
# -*- coding: utf-8 -*-

from cxotime import CxoTime
from Ska.Matplotlib import cxctime2plotdate as cxc2pd


def cxctime_to_datetime(rawtimes):
    """
    Convert input CXC time (seconds since 1998.0) to a datetime object

    This nest of functions effectively converts:
    rawtimes is in units of CXC seconds, or seconds since 1998.0,
    applies delta T between 1998.0 (CXC's Epoch) and 1970.0 (Unix Epoch),
    and converts to plot_date, which expects days since start of Year 1 AD.

    seconds_since_1998_0 = time_array[0]
    cxctime = dt.datetime(1998, 1, 1, 0, 0, 0)
    unixtime = dt.datetime(1970, 1, 1, 0, 0, 0)


    t0 = Chandra.Time.DateTime(times[0]).unix
    delta_time = (cxctime - unixtime).total_seconds() + seconds_since_1998_0
    plotdate_start = mdate.epoch2num(delta_time) # convert to days since start of Year 1 AD

    DEPRECATE THIS. JUST USE CXOTIME!

    OKAY. Done. I used to do something idiotic like this, which was totally circular:
        plot_date_time = mdate.num2date(cxc2pd(cxcDateTime(rawtimes).secs))

    """

    datetime = CxoTime(rawtimes).datetime

    return datetime


def convert_to_doy(datetime_start):
    '''
    Return a string like '2020:237' that will be passed to start= in
    fetch.get_telem(), fetch.MSID(), as well as e.g. URL strings for the web-Kadi API.
    '''

    year = datetime_start.year
    day_of_year = datetime_start.timetuple().tm_yday

    # you have to zero-pad the day number! i.e. you want '2022:002', not '2022:2'
    doystring = '{}:{:03d}'.format(year, day_of_year)

    return doystring


def timedelta_formatter(timedelta_object):
    # getting the seconds field of the timedelta
    td_sec = timedelta_object.seconds
    # calculating the total hours
    hour_count, rem = divmod(td_sec, 3600)
    minute_count, second_count = divmod(
        rem, 60)         # distributing the remainders

    day_msg = f"{timedelta_object.days} days, " if timedelta_object.days > 0 else ""
    hour_msg = f"{hour_count} hours, " if hour_count > 0 else ""
    minute_msg = f"{minute_count} minutes, " if minute_count > 0 else ""
    second_msg = f"{second_count} seconds" if second_count > 0 else ""

    msg = f"{day_msg}{hour_msg}{minute_msg}{second_msg}"
    return msg                                           # returning the custom output