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