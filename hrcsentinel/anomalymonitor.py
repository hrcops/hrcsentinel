#!/usr/bin/env python

from commbot import send_slack_message
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
from heartbeat import are_we_in_comm

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

    fetch.data_source.set('maude allow_subset=True')

    iteration = 0

    while True:
        in_comm = are_we_in_comm(verbose=False, cadence=5)

        if not in_comm:
            print(f'Not in comm')

        if in_comm:
            try:
                reference_telem = audit_telemetry(
                    start=CxoTime.now() - 60 * u.s)
                time.sleep(3)
                latest_telem = audit_telemetry(start=CxoTime.now() - 60 * u.s)

                print(f'Iteration {iteration}: {latest_telem} V')

                if iteration == 0:
                    send_slack_message(
                        f'Comm Bot started with +15 V reference value of: {reference_telem} V ', channel='#hrc-s_side_a_checkout_sep2022_cap1636')

                if latest_telem < 14.0:
                    send_slack_message(
                        f'WARNING: the +15V Bus Voltage looks bad ({latest_telem} V) Check this!', channel='#hrc-s_side_a_checkout_sep2022_cap1636')

                iteration += 1
            except Exception as e:
                print(e)
                continue


if __name__ == '__main__':
    main()
