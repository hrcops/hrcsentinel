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


def audit_telemetry(start_time):
    '''
    Audit the most relevant telemetry and send slack warnings if they are out of bounds
    '''

    # Check the Mission-critical CEA Temperature

    ceatemp = fetch.MSID('2CEAHVPT', start=start_time, stat='full')

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


def main():
    '''
    The main event loop. While in comm, check all relevant telemetry for bad values. Just do this explicitly

    '''

    fetch.data_source.set('maude allow_subset=False')

    in_comm_counter = 0
    out_of_comm_refresh_counter = 0

    # Loop infintely :)
    while True:
        try:
            with force_timeout(600):  # don't let this take longer than 10 minutes

                in_comm = are_we_in_comm(verbose=False, cadence=5)

                if not in_comm:
                    print(
                        f'({timestamp_string()}) Not in Comm.                                  ', end='\r\r\r')

                elif in_comm:
                    print(f"({timestamp_string()})  In Comm!", flush=True)



        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
