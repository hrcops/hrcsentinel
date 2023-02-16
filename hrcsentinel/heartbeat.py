#!/usr/bin/env python

import time
from astropy import units as u
import datetime as dt
import pytz
from cxotime import CxoTime
import Ska.engarchive.fetch as fetch

from contextlib import contextmanager
import signal


class TimeoutException(Exception):
    pass


@contextmanager
def force_timeout(seconds):
    '''
    For some reason, my MAUDE fetches using the Ska API sometimes
    timeout on the ssl.do_handshake() call. I'm lazy and don't want
    to figure it out, so this function will force a timeout of the call
    after a given number of seconds. If you wrap it in a try/except and a while
    loop, it will simply try again (which almost always fixes the issue). 
    '''
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out! Pressing on...")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)




def are_we_in_comm(verbose=False, cadence=2, fake_comm=False):
    # Always be fetching from MAUDE
    fetch.data_source.set('maude allow_subset=True')

    # These fetches are really fast. Slow the cadence a bit.
    time.sleep(cadence)  # cadence is in seconds here

    # If there VCDU frame values within the last 60 seconds, this will not be empty
    ref_vcdu = fetch.Msid('CVCDUCTR', start=CxoTime.now() - 60 * u.s)

    # Will be True if in comm, False if not.
    in_comm = len(ref_vcdu) > 0

    if fake_comm is True:
        in_comm = True

    if verbose:
        if in_comm:
            print(
                f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")} | VCDU {ref_vcdu.vals[-1]} | #{in_comm_counter}) IN COMM!', end='\r')
        elif not in_comm:
            print(
                f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) Not in Comm.                                 ', end='\r\r\r')

    return in_comm


def timestamp_string():
    # return CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")
    # return dt.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    return dt.datetime.now(pytz.timezone('US/Eastern')).strftime("%m/%d/%Y %I:%M:%S %p") + f" {dt.datetime.now(pytz.timezone('US/Eastern')).astimezone().tzinfo}"


def main():
    while True:
        in_comm = are_we_in_comm(verbose=True)


if __name__ == "__main__":
    main()
