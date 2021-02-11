#!/usr/bin/env python

import sys
import requests
import json
import traceback
import argparse

from Ska.engarchive import fetch

import numpy as np

import time
from cxotime import CxoTime
import datetime as dt
from chandratime import convert_chandra_time, convert_to_doy

import astropy.units as u


def send_slack_message(message, channel='#comm_passes', blocks=None):

    # Never push the token to github!
    with open('/Users/grant/.slackbot/slackbot_oauth_token', 'r') as tokenfile:
        # .splitlines()[0] is needed to strip the \n character from the token file
        slack_token = tokenfile.read().splitlines()[0]

    slack_channel = channel
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
                         '2FHTRMZT', '2IMTPAST', '2IMBPAST', '2SPTPAST', '2SPBPAST', '2TLEV1RT', '2VLEV1RT']
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
    # HALF voltage for HRC-I is 42/53
    # FULL voltage for HRC-S is 77/89
    hrc_s_voltage = (
        critical_msids['2SPTPAST'].vals[-1], critical_msids['2SPBPAST'].vals[-1])
    # HALF voltage for HRC-S is 43/54 (top/bottom)
    # FULL voltage is 93/105 (top/bottom)

    te_rate = critical_msids['2TLEV1RT'].vals[-1]
    ve_rate = critical_msids['2VLEV1RT'].vals[-1]

    telem = {'Format': tm_format, 'Shield Rate': shield_rate, 'Shield State': shield_state,
             'Bus Current': bus_current, 'FEA Temp': fea_temp, 'HRC-I Voltage Steps': hrc_i_voltage, 'HRC-S Voltage Steps': hrc_s_voltage, 'TE Rate': te_rate, 'VE Rate': ve_rate}

    return telem


def get_args():
    '''Fetch command line args, if given'''

    parser = argparse.ArgumentParser(
        description='Monitor the VCDU telemetry stream, and send a message to the HRC Ops Slack with critical HRC telemetry whenever we are in comm.')

    parser.add_argument("--fake_comm", help="Trick the code to think it's in comm. Useful for testing. ",
                        action="store_true")

    args = parser.parse_args()
    return args


def main():

    fetch.data_source.set('maude allow_subset=True')

    args = get_args()

    # Just some initial settings
    recently_in_comm = False
    in_comm_counter = 0
    fake_comm = args.fake_comm  # Boolean

    # Loop infinitely :)
    while True:

        try:
            # If there VCDU frame values within the last 60 seconds, this will not be empty
            ref_vcdu = fetch.Msid('CVCDUCTR', start=CxoTime.now() - 60 * u.s)

            # These fetches are really fast. Slow the cadence a bit.
            time.sleep(2)

            if len(ref_vcdu) == 0:
                # Then we clearly are not in comm.

                if recently_in_comm is True:
                    # then we've JUST been in comm and we need to report its end.
                    telem = grab_critical_telemetry(
                        start=CxoTime.now() - 1800 * u.s)
                    message = f"It appears that COMM has ended as of `{CxoTime.now().strftime('%m/%d/%Y %H:%M:%S')}` \n\n Last telemetry was in `{telem['Format']}` \n\n *Shields were {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps` \n\n *Bus Current* was `{telem['Bus Current']} A` (warning limit is 2.3 A)  \n\n *FEA Temperature* was `{telem['FEA Temp']} C`"
                    send_slack_message(message)

                recently_in_comm = False
                in_comm_counter = 0
                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) Not in Comm.                                 ', end='\r\r\r')

            if len(ref_vcdu) > 0:
                # Then it looks like we're in comm.
                recently_in_comm = True
                in_comm_counter += 1

                time.sleep(5)  # Wait a few seconds for MAUDE to refresh
                latest_vcdu = fetch.Msid(
                    'CVCDUCTR', start=CxoTime.now() - 300 * u.s).vals[-1]

                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")} | VCDU {latest_vcdu} | #{in_comm_counter}) IN COMM!', end='\r')

                if in_comm_counter == 5:
                    # Now we've waited ~half a minute or so for MAUDE to update
                    telem = grab_critical_telemetry(
                        start=CxoTime.now() - 300 * u.s)
                    # Craft a message string using this latest elemetry
                    message = f"We are now *IN COMM* as of `{CxoTime.now().strftime('%m/%d/%Y %H:%M:%S')}` (_Chandra_ time). \n \n Telemetry Format = `{telem['Format']}` \n *HRC-I* Voltage Steps (Top/Bottom) = `{telem['HRC-I Voltage Steps'][0]}/{telem['HRC-I Voltage Steps'][1]}` \n *HRC-S* Voltage Steps (Top/Bottom) = `{telem['HRC-S Voltage Steps'][0]}/{telem['HRC-S Voltage Steps'][1]}`  \n \n *Total Event* Rate = `{telem['TE Rate']} cps`   \n *Valid Event* Rate = `{telem['VE Rate']} cps`  \n *Shields are {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps` \n \n *Bus Current* is `{telem['Bus Current']}`\n \n *FEA Temperature* is `{telem['FEA Temp']} C`"
                    # Send the message using our slack bot
                    send_slack_message(message)

        except Exception as e:

            print(f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) ERROR: {e}')
            print("Heres the traceback:")
            print(traceback.format_exc())
            print("Pressing on...")
            if in_comm_counter > 0:
                in_comm_counter -= 1
            continue


if __name__ == '__main__':
    main()
