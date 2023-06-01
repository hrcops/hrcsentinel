#!/usr/bin/env conda run -n ska3 python

import os
import argparse
import datetime as dt
import json
import socket
import sys
import time
import traceback

import astropy.units as u
import numpy as np
import requests
from cheta import fetch_sci as fetch
from cxotime import CxoTime
from Chandra.Time import DateTime as cxcDateTime

from heartbeat import are_we_in_comm, timestamp_string, force_timeout, TimeoutException
from goes_proxy import get_goes_proxy
from monitor_comms import send_slack_message
from chandratime import convert_to_doy, timedelta_formatter

import datetime as dt


def check_safe_modes(start_time, slack_channel=''):
    '''
    Check for any current or prior safing actions
    '''
    scs_107_state = fetch.MSID('COSCS107S', start=start_time)


# def audit_telemetry(start_time, in_comm: bool):
#     '''
#     Audit the most relevant telemetry and send slack warnings if they are out of bounds
#     '''

#     # Check the Mission-critical MSIDs
#     msidlist = ['2C05PALV', '2C15PALV', '2CEAHVPT']
#     telem = fetch.MSIDset(msidlist, start=start_time)

#     # Find where the 15V has been OFF, i.e. reads between 19 and 20 V (usually/always 19.84375 V)
#     fifteen_volt_off_mask = np.ma.masked_inside(
#         telem['2C15PALV'].vals, 19, 20).mask

#     fifteen_volt_on_mask = np.logical_not(fifteen_volt_off_mask)

#     print(fifteen_volt_off_mask)

#     # Check the latest values
#     latest_5v = np.round(telem['2C05PALV'].vals[-1], 1)
#     latest_15v = np.round(telem['2C15PALV'].vals[-1], 1)
#     latest_ceatemp = np.round(telem['2CEAHVPT'].vals[-1], 1)

#     if latest_15v < 20.0 and latest_15v > 19.0:
#         # then the 15V is probably off
#         print('The 15V is OFF')
#         print(
#             f"({timestamp_string()}) last 100 values: {telem['2C15PALV'].vals[0:100]}")

#     if latest_ceatemp < 10.0 and latest_ceatemp > -15.0:
#         # then the 15V is probably off
#         print(f'({timestamp_string()}) CEA HVPS Temperature is {latest_ceatemp} C')

#     return None
    # critical_msidlist = ['CCSDSTMF', '2SHEV1RT', '2PRBSCR', '2FHTRMZT', '2CHTRPZT',
    #                     '2IMTPAST', '2IMBPAST', '2SPTPAST', '2SPBPAST', '2TLEV1RT', '2VLEV1RT']

    # telem = fetch.MSIDset(
    #     critical_msidlist, start=CxoTime.now() - 1 * u.hr)

    # for msid in critical_msidlist:
    #     print(f'Latest {msid} is : {telem[msid].vals[-1]}')

    # try:
    #     _, goes_rates = get_goes_proxy()
    #     print(
    #         f'Latest GOES rate is {int(goes_rates[-1])} CPS')
    # except:
    #     continue


def get_args():
    '''Fetch command line args, if given'''

    argparser = argparse.ArgumentParser(
        description='Monitor the VCDU telemetry stream, and update critical status plots whenever we are in comm.')

    argparser.add_argument("--fake_comm", help="Trick the code to think we are in comm. Useful for testing. ",
                           action="store_true")

    argparser.add_argument("--test", help="Run a full test of the code. ",
                           action="store_true")

    args = argparser.parse_args()

    return args


def main():
    '''
    The main event loop. While in comm, check all relevant telemetry for bad values. Just do this explicitly

    '''

    print('\033[1mHRCSentinel\033[0m | Anomaly Monitor')

    args = get_args()
    fake_comm = args.fake_comm

    fetch.data_source.set('maude allow_subset=False')

    iteration_counter = 0

    misidlist = ['2C15PALV', '2N15PALV', '2FHTRMZT', '2CHTRPZT']

    # Loop infintely :)
    while True:

        # Let's check the last 24h of data, which is longer than the longest time we'll ever be out of comm (hopefully!)
        two_days_ago = dt.datetime.now() - dt.timedelta(days=2)
        # Convert this to a YYYY:DOY string like '2023:101'
        pull_telem_from = convert_to_doy(two_days_ago)

        try:
            with force_timeout(600):  # don't let this take longer than 10 minutes

                # Check the Mission-critical MSIDs

                state_msidlist = ['215PCAST']
                telem_msidlist = ['2C05PALV', '2C15PALV', '2CEAHVPT']
                telem_msidlist_units = ['V', 'V', 'C']

                state = fetch.MSIDset(state_msidlist, start=pull_telem_from)
                telem = fetch.MSIDset(
                    telem_msidlist, start=pull_telem_from)

                fifteen_volt_should_be_on = state['215PCAST'].vals[-1] == 'ON'

                if fifteen_volt_should_be_on:

                    print(
                        f"({timestamp_string()}) \033[1mLast received telemetry report\033[0m")
                    for msid, unit in zip(telem_msidlist, telem_msidlist_units):

                        # Calculate age of this telemetry
                        latest_value = np.round(telem[msid].vals[-1], 3)
                        latest_time = cxcDateTime(
                            telem[msid].times[-1]).date

                        telemetry_age_seconds = CxoTime().now().secs - \
                            telem[msid].times[-1]  # in units of seconds
                        telemetry_age_timedelta = timedelta_formatter(dt.timedelta(
                            seconds=telemetry_age_seconds))

                        print(f'{msid}: {latest_value} {unit}')

                        if msid == '2C15PALV':
                            pass

                            if telem[msid].vals[-1] > 14.0:
                                print(
                                    f"HRC is ON and the +15V bus is GOOD at {latest_value} (Latest telemetry is {telemetry_age_timedelta} old)")
                    print('\n')
                    # print(
                    #     f'({timestamp_string()}) Latest {msid} is : {latest_value} at {latest_time} ({telemetry_age_timedelta} old)')

        except Exception as e:
            print(f'ERROR: {traceback.format_exc()}')

        # time.sleep(20)


if __name__ == "__main__":
    main()
