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
from cheta import fetch
from cxotime import CxoTime

from heartbeat import are_we_in_comm, timestamp_string, force_timeout, TimeoutException
from goes_proxy import get_goes_proxy
from monitor_comms import send_slack_message


def check_safe_modes(start_time, slack_channel=''):
    '''
    Check for any current or prior safing actions
    '''
    scs_107_state = fetch.MSID('COSCS107S', start=start_time)


def audit_telemetry(start_time, iteration_counter=0):
    '''
    Audit the most relevant telemetry and send slack warnings if they are out of bounds
    '''

    # Check the Mission-critical CEA Temperature

    return None
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

    in_comm_counter = 0
    out_of_comm_refresh_counter = 0
    iteration_counter = 0

    # Loop infintely :)
    while True:
        try:
            with force_timeout(600):  # don't let this take longer than 10 minutes

                in_comm = are_we_in_comm(
                    verbose=False, cadence=5, fake_comm=fake_comm)

                if not in_comm:
                    print(
                        f'({timestamp_string()}) Not in Comm.                                  ', end='\r\r\r')

                elif in_comm:
                    print(f"({timestamp_string()})  In Comm!", flush=True)
                    audit_telemetry(CxoTime.now() - 1 * u.hr,
                                    iteration_counter=iteration_counter)

                    iteration_counter += 1
                    print(iteration_counter)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
