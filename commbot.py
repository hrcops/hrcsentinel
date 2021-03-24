#!/usr/bin/env python

import sys
import requests
import json
import traceback
import argparse
import socket

from Ska.engarchive import fetch

import numpy as np

import time
from cxotime import CxoTime
import datetime as dt
from chandratime import convert_chandra_time, convert_to_doy

import astropy.units as u

from heartbeat import are_we_in_comm


def send_slack_message(message, channel='#comm_passes', blocks=None):

    # I run this on both the HEAD LAN and my home machine
    # Make sure it's readable only to you, i.e. chmod og-rwx slackbot_oauth_token
    if socket.gethostname() == 'han-v.cfa.harvard.edu':
        slackbot_token_path = '/home/tremblay/.slackbot/slackbot_oauth_token'
    elif socket.gethostname() == 'symmetry.local':
        slackbot_token_path = '/Users/grant/.slackbot/slackbot_oauth_token'
    else:
        sys.exit('I do not recognize the hostname {}. Exiting.'.format(
            socket.gethostname()))

    # Never push the token to github!
    with open(slackbot_token_path, 'r') as tokenfile:
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
    bus_current_in_amps = np.round(critical_msids['2PRBSCR'].vals[-1], 2)
    bus_current_in_dn = convert_bus_current_to_dn(bus_current_in_amps)

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
             'Bus Current (DN)': bus_current_in_dn, 'Bus Current (A)': bus_current_in_amps, 'FEA Temp': fea_temp, 'HRC-I Voltage Steps': hrc_i_voltage, 'HRC-S Voltage Steps': hrc_s_voltage, 'TE Rate': te_rate, 'VE Rate': ve_rate}

    return telem


def convert_bus_current_to_dn(bus_current_in_amps):
    '''
    The DN-to-Current (Amps) conversion for 2PRBSCR is just a linear
    offset in the form I = (m * DN) + b, from here: https://icxc.cfa.harvard.edu/hrcops/msid/hrc.msid.html
    '''

    # bus_current_in_amps = (m * DN) + b, were m=0.0682 and b=-8.65
    # DN = (bus_current_in_amps - b) / m

    b = -8.65
    m = 0.0682

    # Needs to be a whole integer
    dn = int(round((bus_current_in_amps - b) / m))

    return dn


def get_args():
    '''Fetch command line args, if given'''

    parser = argparse.ArgumentParser(
        description='Monitor the VCDU telemetry stream, and send a message to the HRC Ops Slack with critical HRC telemetry whenever we are in comm.')

    parser.add_argument("--fake_comm", help="Trick the code to think it's in comm. Useful for testing. ",
                        action="store_true")

    parser.add_argument("--report_errors", help="Print MAUDE exceptions (which are common) to the command line",
                        action="store_true")

    args = parser.parse_args()
    return args


def main():

    fetch.data_source.set('maude allow_subset=True')

    args = get_args()
    fake_comm = args.fake_comm

    if fake_comm:
        bot_slack_channel = '#bot-testing'
    elif not fake_comm:
        bot_slack_channel = bot_slack_channel = '#comm_passes'

    # Initial settings
    recently_in_comm = False
    in_comm_counter = 0

    # Loop infinitely :)
    while True:

        try:
            in_comm = are_we_in_comm(
                verbose=False, cadence=2, fake_comm=fake_comm)

            if not in_comm:
                if recently_in_comm:
                    # then we've JUST been in comm and we need to report its end.
                    telem = grab_critical_telemetry(
                        start=CxoTime.now() - 1800 * u.s)
                    message = f"It appears that COMM has ended as of `{CxoTime.now().strftime('%m/%d/%Y %H:%M:%S')}` \n\n Last telemetry was in `{telem['Format']}` \n\n *Shields were {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps` \n\n *HRC-I* Voltage Steps were (Top/Bottom) = `{telem['HRC-I Voltage Steps'][0]}/{telem['HRC-I Voltage Steps'][1]}` \n *HRC-S* Voltage Steps were (Top/Bottom) = `{telem['HRC-S Voltage Steps'][0]}/{telem['HRC-S Voltage Steps'][1]}`  \n\n *Bus Current* was `{telem['Bus Current (DN)']} DN` (`{telem['Bus Current (A)']} A` warning limit is `2.3 A`)  \n\n *FEA Temperature* was `{telem['FEA Temp']} C`"
                    send_slack_message(message, channel=bot_slack_channel)

                recently_in_comm = False
                in_comm_counter = 0
                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) Not in Comm.                                 ', end='\r\r\r')

            if in_comm:
                if fake_comm:
                    # two days to make sure we grab previous comm
                    start_time = CxoTime.now() - 2 * u.d
                elif not fake_comm:
                    start_time = CxoTime.now() - 300 * u.s  # 300 sec to make the grab really small

                recently_in_comm = True
                in_comm_counter += 1

                time.sleep(5)  # Wait a few seconds for MAUDE to refresh
                latest_vcdu = fetch.Msid(
                    'CVCDUCTR', start=start_time).vals[-1]

                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")} | VCDU {latest_vcdu} | #{in_comm_counter}) In Comm.', end='\r')

                if in_comm_counter == 5:
                    # Now we've waited ~half a minute or so for MAUDE to update
                    telem = grab_critical_telemetry(
                        start=CxoTime.now() - 8 * u.h)

                    # Craft a message string using this latest elemetry
                    message = f"We are now *IN COMM* as of `{CxoTime.now().strftime('%m/%d/%Y %H:%M:%S')}` (_Chandra_ time). \n \n Telemetry Format = `{telem['Format']}` \n *HRC-I* Voltage Steps (Top/Bottom) = `{telem['HRC-I Voltage Steps'][0]}/{telem['HRC-I Voltage Steps'][1]}` \n *HRC-S* Voltage Steps (Top/Bottom) = `{telem['HRC-S Voltage Steps'][0]}/{telem['HRC-S Voltage Steps'][1]}`  \n \n *Total Event* Rate = `{telem['TE Rate']} cps`   \n *Valid Event* Rate = `{telem['VE Rate']} cps`  \n *Shields are {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps` \n \n *Bus Current* is `{telem['Bus Current (DN)']} DN` (`{telem['Bus Current (A)']} A`) \n \n *FEA Temperature* is `{telem['FEA Temp']} C`"
                    # Send the message using our slack bot
                    send_slack_message(message, channel=bot_slack_channel)

        except Exception as e:
            # MAUDE queries fail regularly as TM is streaming in (mismatched array sizes as data is being populated), 404s, etc.
            # The solution is almost always to simply try again. Therefore this script just presses on in the event of an Exception.

            if args.report_errors is True:
                # Then we want a verbose error message, because we're obviously in testing mode
                print(f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) ERROR: {e}')
                print("Heres the traceback:")
                print(traceback.format_exc())
                print("Pressing on...")
            elif args.report_errorsi is False:
                # Then we're likely in operational mode. Ignore the errors on the command line.
                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) MAUDE Error =(                             ', end='\r\r\r')
            if in_comm_counter > 0:
                # Reset the comm counter to make the error "not count"
                in_comm_counter -= 1
            continue


if __name__ == '__main__':
    main()
