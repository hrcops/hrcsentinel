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

    # Initial settings
    recently_in_comm = False
    in_comm_counter = 0
    out_of_comm_refresh_counter = 0
    iteration_counter = 0

    lookback_time = CxoTime().now() - 12 * u.hr

    misidlist = ['2C15PALV', '2N15PALV', '2FHTRMZT', '2CHTRPZT']


    # Loop infintely :)
    while True:
        try:
            with force_timeout(600):  # don't let this take longer than 10 minutes

                in_comm = are_we_in_comm(
                    verbose=False, cadence=5, fake_comm=fake_comm)

                if not in_comm:
                    print(
                        f'({timestamp_string()}) Not in Comm.                                  ', end='\r', flush=True)

                    if iteration_counter == 0:
                        # Then grab the reference telemetry
                        reference_telemetry = fetch.MSIDset(msidlist, start=lookback_time)

                        print(f"({timestamp_string()}) Not in Comm. Fetched reference telemetry from last comm. .  ", end='\r', flush=True


                    if recently_in_comm:
                        # We might have just had a loss in telemetry. Try again after waiting for a minute
                        time.sleep(60)
                        in_comm = are_we_in_comm(verbose=False, cadence=2)
                        if in_comm:
                            continue

                        elif not in_comm:
                            #TO DO
                            pass

                    recently_in_comm = False
                    in_comm_counter = 0
                    out_of_comm_refresh_counter += 1

                elif in_comm:

                    if in_comm_counter == 0:
                        comm_start_time = CxoTime.now()

                    # Toggle the recently_in_comm flag so that, on the next out-of-comm loop, it'll allow us to do stuff
                    recently_in_comm = True
                    in_comm_counter += 1

                    print(f"({timestamp_string()})  In Comm!", end='\r', flush=True)

                    telemetry_start_time = CxoTime.now() - 12 * u.hr

                    audit_telemetry(CxoTime.now() - 1 * u.hr, iteration_counter=iteration_counter)

                    iteration_counter += 1

        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
