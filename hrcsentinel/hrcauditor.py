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

from heartbeat import are_we_in_comm

# Create a loop to see if we're in comm

select_alarm_file()
# Fetch only the telemetry needed for a quick alarm file selection logic. Use what we have for RTCADS


class BadAlarmFile(Exception):
    pass


def parse_alarm_file(path, fname):
    """Alarm limits are stored in a dictionary indexed by variable name.
    """
    alarmfile = path + '/' + fname
    with open(alarmfile) as afh:
        ald = dict()
        for line in afh:
            if not re.match(r'#', line):
                pcs = re.split('\t', line)
                if len(pcs) == 6:
                    ald[pcs[0]] = dict([('status', int(pcs[1])),
                                        ('rll', float(pcs[2])),
                                        ('yll', float(pcs[3])),
                                        ('yul', float(pcs[4])),
                                        ('rul', float(pcs[5]))])
                else:
                    raise BadAlarmFile(alarmfile)
        return ald
    raise BadAlarmFile(alarmfile)
