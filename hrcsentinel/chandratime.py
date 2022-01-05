#!/usr/bin/env conda run -n ska3 python

import datetime as dt

import matplotlib.dates as mdate
import numpy as np
import pytz
from kadi import events


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


def calc_time_to_next_comm():
    '''
    Queries the Kadi event database for the next several (scheduled) comm passes.
    Calculates the duration between now (in UTC) and the next comm pass.
    If that duration is negative (i.e. that comm already happened), it searches
    the list of passes for the first positive time delta, i.e. the first comm pass in the future.
    Returns a string in reporting the time to the next comm pass.
    '''
    # Now must be in UTC becuase the comm table is is.
    comms = events.dsn_comms.filter(
        start=convert_to_doy(dt.datetime.utcnow())).table

    # The NEXT comm will either be row zero of the table, or row one. It depends on when you fetch. So just check.

    comm_tdelta = None

    for i in range(0, 4):
        raw_comm_start = dt.datetime.strptime(
            comms['start'][i], "%Y:%j:%H:%M:%S.%f")

        est = pytz.timezone('US/Eastern')
        utc = pytz.utc

        localized_comm_start = utc.localize(raw_comm_start)
        # I DO NOT understand why DST is not being accounted for! the subtraction of 1 hour is a brute-force fix.
        localized_now = est.localize(dt.datetime.now()) - dt.timedelta(hours=1)
        comm_tdelta = localized_comm_start - localized_now

        if comm_tdelta.total_seconds() > 0:
            # Then we have (hopefully) succeeded, and now need only format a string to return.

            days = int(comm_tdelta.days)
            seconds = round(int(comm_tdelta.seconds), 0)
            # the // operator rounds down the answer, and returns a whole number.
            hours = seconds // 3600
            minutes = (seconds//60) % 60

            next_comm_string = f'{days} days, {hours} hours, {minutes} minutes'

            return next_comm_string

    if comm_tdelta is None:
        # Then the code has failed to find a next comm and there is a problem. Just report that.
        return "ERROR: Failed to find next comm!"

    del comms
