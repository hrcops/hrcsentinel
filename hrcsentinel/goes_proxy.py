#!/usr/bin/env python

import collections
import time

import numpy as np
import requests
from astropy.table import Table
from astropy.time import Time

from chandratime import cxctime_to_datetime

# Globals

# URLs for 6 hour and 7 day JSON files
GOES_URL_ROOT = 'https://services.swpc.noaa.gov/json/goes/primary/'
GOES_6HOUR = f'{GOES_URL_ROOT}/differential-protons-6-hour.json'
GOES_7DAY = f'{GOES_URL_ROOT}/differential-protons-7-day.json'

# Bad or missing data value
BAD_VALUE = -1.0e5

# dTypes from the Replan Central hrc_shield.h5 file. See more here: https://github.com/sot/arc/blob/master/get_hrc.py
data_types = np.dtype([('year', '<i8'), ('month', '<i8'), ('dom', '<i8'), ('hhmm', '<i8'), ('mjd', '<i8'), ('secs', '<i8'), ('p1', '<f8'), ('p2', '<f8'), ('p3', '<f8'), ('p4', '<f8'), ('p5', '<f8'), ('p6', '<f8'), ('p7',
                                                                                                                                                                                                                       '<f8'), ('p8', '<f8'), ('p9', '<f8'), ('p10', '<f8'), ('p11', '<f8'), ('hrc_shield', '<f8'), ('time', '<f8'), ('p2a', '<f8'), ('p2b', '<f8'), ('p8a', '<f8'), ('p8b', '<f8'), ('p8c', '<f8'), ('satellite', '<i8')])


def get_json_data(url):
    """
    Open the json file and return it as an astropy table
    """
    last_err = None
    for _ in range(3):  # try three times
        try:
            json_file = requests.get(url)
            data = json_file.json()
            break
        except Exception as err:
            last_err = err
            time.sleep(5)
    else:
        print(f'Warning: failed to open URL {url}: {last_err}')
        # sys.exit(0) I really dont want this to kill my code. I'd rather just not plot the proxy.

    dat = Table(data)
    return dat


def format_proton_data(dat, data_types):
    """
    Manipulate the data and return them in a desired format
    including columns that the old h5 file format wanted.
    """

    # Create a dictionary to capture the channel data for each time
    out = collections.defaultdict(dict)
    for row in dat:
        out[row['time_tag']][row['channel'].lower()] = row['flux'] * 1000

    # Reshape that data into a table with the channels as columns
    newdat = Table(list(out.values())).filled(BAD_VALUE)
    # Already in time order if dat rows in order
    newdat['time_tag'] = list(out.keys())

    # Assume the satellite is the same for all of the records of one dat/file
    newdat['satellite'] = dat['satellite'][0]

    # Add some time columns
    times = Time(newdat['time_tag'])
    newdat['time'] = times.cxcsec
    newdat['mjd'] = times.mjd.astype(int)
    newdat['secs'] = np.array(np.round((times.mjd - newdat['mjd']) * 86400,
                                       decimals=0)).astype(int)
    newdat['year'] = [t.year for t in times.datetime]
    newdat['month'] = [t.month for t in times.datetime]
    newdat['dom'] = [t.day for t in times.datetime]
    newdat['hhmm'] = np.array(
        [f"{t.hour}{t.minute:02}" for t in times.datetime]).astype(int)

    # Take the Table and make it into an ndarray with the supplied type
    arr = np.ndarray(len(newdat), dtype=data_types)
    for col in arr.dtype.names:

        # This gets any channels that were just missing altogether.  Looks like p2 and p11 now
        if col not in newdat.colnames:
            arr[col] = BAD_VALUE
        else:
            arr[col] = newdat[col]

    # Calculate the hrc shield values using the numpy array and save into the array
    hrc_shield = calc_hrc_shield(arr)
    arr['hrc_shield'] = hrc_shield
    hrc_bad = (arr['p5'] < 0) | (arr['p6'] < 0) | (arr['p7'] < 0)
    arr['hrc_shield'][hrc_bad] = BAD_VALUE  # flag bad inputs

    return arr, hrc_bad


def calc_hrc_shield(dat):
    '''
    Using the raw GOES data, estimate the particle background rate
    (in counts per second) that
    the HRC anticoincidence shield would *probably* see, if it
    were turned on (which it often isn't).


    This is Malgosia's and MTA's proxy model
    For GOES earlier than 16 use columns p5, p6, p7
    hrc_shield = (6000 * dat['p5'] + 270000 * dat['p6']
                  + 100000 * dat['p7']) / 256.
    HRC proxy, GOES-16, used until April 2021
    hrc_shield = (6000 * dat['p5'] + 270000 * dat['p7']
                  + 100000 * dat['p9']) / 256.
    HRC proxy model based on fitting the 2SHLDART data
    with a combination of GOES-16 channels at the time
    of the Sep 2017 flare
    '''

    # ORINIGNAL NORMALIZATION
    # hrc_shield = (143 * dat['p5'] + 64738 * dat['p6']
    #               + 162505 * dat['p7'] + 4127)  # / 256.
    hrc_shield = (143 * dat['p5'] + 64738 * dat['p6']
                  + 162505 * dat['p7'] + 4600)  # / 256.
    return hrc_shield


def get_goes_proxy():
    """
    Return a format string for the PlotDate function and an array of GOES proxy rates.
    Used for HRCMonitor's shield plot
    """
    # Fetch the raw GOES data
    raw_goes_data = get_json_data(GOES_7DAY)

    # Reformat the table into our standard format
    parsed_goes_data, _bad_goes_data = format_proton_data(
        raw_goes_data, data_types=data_types)

    goes_times = cxctime_to_datetime(parsed_goes_data['time'])
    goes_rates = parsed_goes_data['hrc_shield']

    return goes_times, goes_rates
