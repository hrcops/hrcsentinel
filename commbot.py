#!/usr/bin/env python

import sys
import requests
import json
import time

import numpy as np

from Ska.engarchive import fetch
import datetime as dt
from chandratime import convert_chandra_time, convert_to_doy


fetch.data_source.set('maude allow_subset=True')


def send_slack_message(message, blocks=None):
    with open('/Users/grant/.slackbot/slackbot_oauth_token', 'r') as tokenfile:
        token = tokenfile.readlines()[0]
    slack_token = token
    slack_channel = '#comm_passes'
    slack_icon_url = 'https://avatars.slack-edge.com/2021-01-28/1695804235940_26ef808c676830611f43_512.png'
    slack_user_name = 'HRC CommBot'

    return requests.post('https://slack.com/api/chat.postMessage', {
        'token': slack_token,
        'channel': slack_channel,
        'text': message,
        'icon_url': slack_icon_url,
        'username': slack_user_name,
        'blocks': json.dumps(blocks) if blocks else None}).json()


in_comm_counter = 0

while True:

    # Re-establish today. This is just to ensure we're not fetching too much
    # data from MAUDE, to keep the requests small (and therefore fast)
    now = dt.datetime.now()
    today = dt.date.today()

    ref_vcdu = fetch.MSID('CVCDUCTR', start=convert_to_doy(today)).vals[-1]
    time.sleep(5)
    latest_vcdu = fetch.MSID('CVCDUCTR', start=convert_to_doy(today)).vals[-1]

    frame_delta = latest_vcdu - ref_vcdu

    if frame_delta > 0:
        if in_comm_counter == 4:
            # when comm is first established, grab latest telemetry and report it
            # BUT, we wait until we reach comm_counter = 4 to make sure that MAUDE has telem

            critical_msidlist = ['2SHEV1RT', '2PRBSCR', '2FHTRMZT']
            critical_msids = fetch.get_telem(
                critical_msidlist, quiet=True, unit_system='eng')

            shield_rate = critical_msids['2SHEV1RT'].vals[-1]
            if shield_rate > 0:
                shield_state = 'UP'
            elif shield_rate == 0:
                shield_state = 'DOWN'
            bus_current = np.round(critical_msids['2PRBSCR'].vals[-1], 2)
            fea_temp = np.round(critical_msids['2FHTRMZT'].vals[-1], 2)

            message = f'We are now *IN COMM* as of `{now.strftime("%m/%d/%Y %H:%M:%S")}`. \n *Shields are {shield_state}* with a count rate of `{shield_rate} cps`. \n *Bus Current* is `{bus_current} A` (warning limit is 2.3 A). \n *FEA Temperature* is `{fea_temp} C`'

            send_slack_message(message)

        in_comm_counter += 1
        print(
            f'({now.strftime("%m/%d/%Y %H:%M:%S")} | Refresh #{in_comm_counter}) IN COMM. VCDU increment is: {frame_delta}', end="\r", flush=True)

    elif frame_delta == 0:

        # If we have previously been in comm, in_comm_counter will be > 0
        if in_comm_counter > 0:

            critical_msidlist = ['2SHEV1RT', '2PRBSCR', '2FHTRMZT']
            critical_msids = fetch.get_telem(
                critical_msidlist, quiet=True, unit_system='eng')

            shield_rate = critical_msids['2SHEV1RT'].vals[-1]
            if shield_rate > 0:
                shield_state = 'UP'
            elif shield_rate == 0:
                shield_state = 'DOWN'
            bus_current = np.round(critical_msids['2PRBSCR'].vals[-1], 2)
            fea_temp = np.round(critical_msids['2FHTRMZT'].vals[-1], 2)

            message = f'Comm appears to have ENDED at `{now.strftime("%d/%m/%Y %H:%M:%S")}`. LAST Telemetry: \n *Shields were {shield_state}* with a count rate of `{shield_rate} cps`. \n *Bus Current* was `{bus_current} A` (warning limit is 2.3 A). \n *FEA Temperature* was `{fea_temp} C`'

        # then reset the comm counter
        in_comm_counter = 0
        print(
            f'({now.strftime("%m/%d/%Y %H:%M:%S")}) Chandra is not in Comm.', end="\r", flush=True)
