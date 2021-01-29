#!/usr/bin/env python

import sys
import requests
import json

from Ska.engarchive import fetch

import numpy as np

import time
from cxotime import CxoTime
import datetime as dt
from chandratime import convert_chandra_time, convert_to_doy

import astropy.units as u


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


def grab_critical_telemetry():

    # Repeating myself because now needs to be re-established whenever this is called vOv
    now = CxoTime.now() - 300 * u.s

    critical_msidlist = ['CCSDSTMF', '2SHEV1RT', '2PRBSCR', '2FHTRMZT']
    critical_msids = fetch.get_telem(
        critical_msidlist, start=now, quiet=True, unit_system='eng')

    tm_format = critical_msids['CCSDSTMF']
    shield_rate = critical_msids['2SHEV1RT'].vals[-1]
    if shield_rate > 0:
        shield_state = 'UP'
    elif shield_rate == 0:
        shield_state = 'DOWN'
    bus_current = np.round(critical_msids['2PRBSCR'].vals[-1], 2)
    fea_temp = np.round(critical_msids['2FHTRMZT'].vals[-1], 2)

    telem = {'Format': tm_format, 'Shield Rate': shield_rate, 'Shield State': shield_state,
             'Bus Current': bus_current, 'FEA Temp': fea_temp}

    return telem


def main():

    fetch.data_source.set('maude allow_subset=True')

    recently_in_comm = False
    in_comm_counter = 0

    while True:

        # Just grab the last 60 seconds of data to keep the request small and fast
        now = CxoTime.now() - 60 * u.s

        # If there are new, time-tagged VCDU frame values within the last 60 seconds, this will not be empty
        ref_vcdu = fetch.Msid('CVCDUCTR', start=now)

        time.sleep(2)  # These fetches are really fast. Slow it down a bit.

        if len(ref_vcdu) == 0:
            # Then we clearly are not in comm.

            if recently_in_comm is True:
                # then we've JUST been in comm and we need to report the end of comm
                telem = grab_critical_telemetry()
                message = f"It appears that COMM has ended as of `{now.strftime('% m/%d/%Y % H: % M: % S')}`. Last telemetry was in {telem['Format']}: \n *Shields were {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps`. \n *Bus Current* was `{telem['Bus Current']} A` (warning limit is 2.3 A). \n *FEA Temperature* was `{telem['FEA Temp']} C`"

            recently_in_comm = False
            in_comm_counter = 0
            print(f'({now.strftime("%m/%d/%Y %H:%M:%S")}) Not in Comm.',
                  end="\r", flush=True)

        if len(ref_vcdu) > 0:
            # Then it looks like we're in comm.
            recently_in_comm = True
            in_comm_counter += 1

            time.sleep(5)  # Wait a few seconds for MAUDE to refresh
            latest_vcdu = fetch.Msid('CVCDUCTR', start=now)

            print(
                f'({now.strftime("%m/%d/%Y %H:%M:%S")} | VCDU {latest_vcdu} | #{in_comm_counter}) IN COMM!', end="\r", flush=True)

            if in_comm_counter == 5:
                # Now we've waited ~half a minute or so for MAUDE to update
                telem = grab_critical_telemetry()
                # Craft a message string using this latest elemetry
                message = f"We are now *IN COMM* as of `{now.strftime('% m/%d/%Y % H: % M: % S')}`. \n Telemetry Format = *{telem['Format']}* \n *Shields are {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps`. \n *Bus Current* is `{telem['Bus Current']} A` (warning limit is 2.3 A). \n *FEA Temperature* is `{telem['FEA Temp']} C`"
                # Send the message using our slack bot
                send_slack_message(message)


if __name__ == '__main__':
    main()
