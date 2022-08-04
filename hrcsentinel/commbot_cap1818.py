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

from chandratime import (convert_chandra_time, convert_to_doy)
from heartbeat import are_we_in_comm

import psutil
process = psutil.Process(os.getpid())


def audit_telemetry(start):

    # print(f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) TELEMETRY AUDIT', end='\r')

    critical_msidlist = {
        '2C15PALV': (14.9, 15.1),
    }

    telem = fetch.get_telem(list(critical_msidlist.keys()),
                            start=start, quiet=True, unit_system='eng')

    latest_telem = telem['2C15PALV'].vals[-1]

    return latest_telem

    # values_since_comm_start = fetch.get_telem(
    #     list(critical_msidlist.keys()), start=start, quiet=True, unit_system='eng')

    # for msid in list(critical_msidlist.keys()):
    #     out_of_limit_mask = (values_since_comm_start[msid].vals < critical_msidlist[msid][0]) or (
    #         values_since_comm_start[msid].vals > critical_msidlist[msid][1])
    #     if sum(out_of_limit_mask) > 0:
    #         send_slack_message(
    #             f'TEST{msid}: {values_since_comm_start[out_of_limit_mask][0]}. This is beyond CAUTION/WARN limit of {critical_msidlist[msid]}', channel=channel)

    #     if sum(out_of_limit_mask) > 3:
    #         send_slack_message(
    #             f'{msid} shows out-of-green-range values: {values_since_comm_start[out_of_limit_mask][0]}. This is beyond CAUTION/WARN limit of {critical_msidlist[msid]}', channel=channel)


def main():

    fetch.data_source.set('maude allow_subset=True')

    iteration = 0

    while True:
        in_comm = are_we_in_comm(verbose=False, cadence=5)

        if in_comm:
            reference_telem = audit_telemetry(start=CxoTime.now() - 60 * u.s)
            time.sleep(3)
            latest_telem = audit_telemetry(start=CxoTime.now() - 60 * u.s)

            print(f'Iteration {iteration}: {latest_telem} V')

            if iteration == 0:
                send_slack_message(
                    f'Comm Bot started with +15 V reference value of: {reference_telem} V ', channel='#hrc-s_side_a_test_aug2022_cap1618')

            if latest_telem != reference_telem:
                send_slack_message(
                    f'WARNING: the +15V Bus Voltage has changed from {reference_telem} V to {latest_telem} V. Check this!', channel='#hrc-s_side_a_test_aug2022_cap1618')

            iteration += 1


if __name__ == '__main__':
    main()
