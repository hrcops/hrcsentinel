#!/usr/bin/env python

from monitor_comms import send_slack_message
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

from chandratime import convert_to_doy
from heartbeat import are_we_in_comm, timestamp_string, force_timeout, TimeoutException

# import psutil
# process = psutil.Process(os.getpid())


def audit_telemetry(start):

    # print(f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) TELEMETRY AUDIT', end='\r')

    critical_msidlist = {
        '2C15PALV': (14.9, 15.1),
    }

    telem = fetch.get_telem(list(critical_msidlist.keys()),
                            start=start, quiet=True, unit_system='eng')

    latest_telem = telem['2C15PALV'].vals[-1]

    return latest_telem


def main():
    '''
    Loop!
    '''
    iteration = 0

    fetch.data_source.set('maude allow_subset=False highrate=True')

    while True:
        try:

            # Grab telemetry starting from 24 hours ago
            one_day_ago = dt.datetime.now() - dt.timedelta(days=1)
            telem_start = convert_to_doy(one_day_ago)

            in_comm = are_we_in_comm(verbose=False, cadence=5)

            if not in_comm:
                print(f'({timestamp_string()}) Not in comm')

            if in_comm:
                try:
                    # reference_telem = audit_telemetry(
                    #     start=telem_start)
                    time.sleep(3)
                    latest_telem = audit_telemetry(
                        start=telem_start)

                    print(
                        f'({timestamp_string()}) Iteration {iteration}: {latest_telem} V')

                    if iteration == 0:
                        send_slack_message(
                            f'Comm Bot started with +15 V reference value of: {latest_telem} V ', channel='#comm_passes')

                    if latest_telem < 14.0:
                        send_slack_message(
                            f'@channel WARNING: the +15V Bus Voltage looks bad ({latest_telem} V) Check this!', channel='#comm_passes')

                    iteration += 1
                except Exception as e:
                    print(e)
                    continue
        except Exception as e:
            print(e)
            continue


if __name__ == '__main__':
    main()
