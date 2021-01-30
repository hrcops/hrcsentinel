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

    # KEEP YO TOKEN PRIVATE!
    with open('/Users/grant/.slackbot/slackbot_oauth_token', 'r') as tokenfile:
        # you need to do this to strip the \n
        slack_token = tokenfile.read().splitlines()[0]

    slack_channel = '#comm_passes'
    slack_icon_url = 'https://avatars.slack-edge.com/2021-01-28/1695804235940_26ef808c676830611f43_512.png'
    slack_user_name = 'HRC CommBot'

    # Populate a JSON to push to the Slack API.
    return requests.post('https://slack.com/api/chat.postMessage', {
        'token': slack_token,
        'channel': slack_channel,
        'text': message,
        'icon_url': slack_icon_url,
        'username': slack_user_name,
        'blocks': json.dumps(blocks) if blocks else None}).json()


def grab_critical_telemetry(start=CxoTime.now() - 60 * u.s):

    critical_msidlist = ['CCSDSTMF', '2SHEV1RT', '2PRBSCR',
                         '2FHTRMZT', '2IMTPAST', '2IMBPAST', '2SPTPAST', '2SPBPAST']
    critical_msids = fetch.get_telem(
        critical_msidlist, start=start, quiet=True, unit_system='eng')

    tm_format = critical_msids['CCSDSTMF'].vals[-1]
    shield_rate = critical_msids['2SHEV1RT'].vals[-1]
    if shield_rate > 0:
        shield_state = 'UP'
    elif shield_rate == 0:
        shield_state = 'DOWN'
    bus_current = np.round(critical_msids['2PRBSCR'].vals[-1], 2)
    fea_temp = np.round(critical_msids['2FHTRMZT'].vals[-1], 2)
    hrc_i_voltage = (
        critical_msids['2IMTPAST'].vals[-1], critical_msids['2IMBPAST'].vals[-1])
    hrc_s_voltage = (
        critical_msids['2SPTPAST'].vals[-1], critical_msids['2SPBPAST'].vals[-1])

    telem = {'Format': tm_format, 'Shield Rate': shield_rate, 'Shield State': shield_state,
             'Bus Current': bus_current, 'FEA Temp': fea_temp, 'HRC-I Voltage Steps': hrc_i_voltage, 'HRC-S Voltage Steps': hrc_s_voltage}

    return telem


def main():

    fetch.data_source.set('maude allow_subset=True')

    # Just some initial settings
    recently_in_comm = False
    in_comm_counter = 0

    # Loop infinitely :)
    while True:

        # If there VCDU frame values within the last 60 seconds, this will not be empty
        ref_vcdu = fetch.Msid('CVCDUCTR', start=CxoTime.now() - 60 * u.s)

        time.sleep(2)  # These fetches are really fast. Slow the cadence a bit.

        if len(ref_vcdu) == 0:
            # Then we clearly are not in comm.

            if recently_in_comm is True:
                # then we've JUST been in comm and we need to report its end.
                telem = grab_critical_telemetry(
                    start=CxoTime.now() - 1800 * u.s)
                message = f"It appears that COMM has ended as of `{CxoTime.now().strftime('%m/%d/%Y %H:%M:%S')}`. Last telemetry was in {telem['Format']}: \n *Shields were {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps`. \n *Bus Current* was `{telem['Bus Current']} A` (warning limit is 2.3 A). \n *FEA Temperature* was `{telem['FEA Temp']} C`"

            recently_in_comm = False
            in_comm_counter = 0
            print(f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) Not in Comm.',
                  end="\r", flush=True)

        if len(ref_vcdu) > 0:
            # Then it looks like we're in comm.
            recently_in_comm = True
            in_comm_counter += 1

            time.sleep(5)  # Wait a few seconds for MAUDE to refresh
            latest_vcdu = fetch.Msid(
                'CVCDUCTR', start=CxoTime.now() - 300 * u.s).vals[-1]

            print(
                f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")} | VCDU {latest_vcdu} | #{in_comm_counter}) IN COMM!', end="\r", flush=True)

            if in_comm_counter == 5:
                # Now we've waited ~half a minute or so for MAUDE to update
                telem = grab_critical_telemetry(
                    start=CxoTime.now() - 300 * u.s)
                # Craft a message string using this latest elemetry
                message = f"We are now *IN COMM* as of `{CxoTime.now().strftime('%m/%d/%Y %H:%M:%S')}` (_Chandra_ time). \n \n  Telemetry Format = *{telem['Format']}* \n *HRC-I* Voltage Steps (Top/Bottom) = *{telem['HRC-I Voltage Steps'][0]}/{telem['HRC-I Voltage Steps'][1]}* \n *HRC-S* Voltage Steps (Top/Bottom) = *{telem['HRC-S Voltage Steps'][0]}/{telem['HRC-S Voltage Steps'][1]}* \n \n *Shields are {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps`. \n *Bus Current* is `{telem['Bus Current']} A` (warning limit is 2.3 A). \n *FEA Temperature* is `{telem['FEA Temp']} C`"
                # Send the message using our slack bot
                send_slack_message(message)


if __name__ == '__main__':
    main()
