#!/usr/bin/env python

import time
from astropy import units as u
from cxotime import CxoTime
import Ska.engarchive.fetch as fetch


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


def main():
    while True:
        in_comm = are_we_in_comm(verbose=True)


if __name__ == "__main__":
    main()
