#!/usr/bin/env python

import sys
import requests
import json
import traceback
import argparse
import socket
import time

import numpy as np
import astropy.units as u

from cheta import fetch
from cxotime import CxoTime


import datetime as dt
from chandratime import convert_chandra_time, convert_to_doy
from heartbeat import are_we_in_comm


def audit_telemetry(start, channel=None):
    # Want to implement this!!!

    print(f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) TELEMETRY AUDIT', end='\r')


    critical_msidlist = {'2C05PALV': (4.9, 5.1),
                         '2C15PALV': (14.9, 15.1),
                         '2C15NALV': (-14.8, -14.6),
                         '2C24PALV': (24.1, 24.3),
                         }

    values_since_comm_start = fetch.get_telem(
        list(critical_msidlist.keys()), start=start, quiet=True, unit_system='eng')

    for msid in list(critical_msidlist.keys()):
        out_of_limit_mask = (values_since_comm_start[msid].vals < critical_msidlist[msid][0]) or (values_since_comm_start[msid].vals > critical_msidlist[msid][1])
        if sum(out_of_limit_mask) > 3:
            send_slack_message(f'{msid} shows out-of-green-range values: {values_since_comm_start[out_of_limit_mask][0]}. This is beyond CAUTION/WARN limit of {critical_msidlist[msid]}', channel=channel)



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
    # FULL voltage for HRC-S is 79/91
    hrc_s_voltage = (
        critical_msids['2SPTPAST'].vals[-1], critical_msids['2SPBPAST'].vals[-1])
    # HALF voltage for HRC-S is 43/54 (top/bottom)
    # FULL voltage is 95/107 (top/bottom)

    # Set statuses

    if tm_format == 'FMT1':
        hrc_observing_status = 'OBSERVING'
    else:
        hrc_observing_status = 'NOT observing'

    # in order of off, half, full
    expected_hrc_i_states = [(0, 0), (42, 53), (79, 91)]
    # in order of off, half, full
    expected_hrc_s_states = [(0, 0), (43, 54), (95, 107)]

    expected_status = ['OFF', 'at HALF voltage', 'at FULL voltage']

    hrc_telem_status = None
    hrc_i_status = None
    hrc_s_status = None

    try:
        hrc_i_status = expected_status[expected_hrc_i_states.index(
            hrc_i_voltage)]
    except ValueError:
        hrc_i_status = 'in a POTENTIALLY UNEXPECTED state ({}). CHECK THIS!'.format(
            hrc_i_voltage)

    try:
        hrc_s_status = expected_status[expected_hrc_s_states.index(
            hrc_s_voltage)]
    except ValueError:
        hrc_s_status = 'in a POTENTIALLY UNEXPECTED state ({}). CHECK THIS!'.format(
            hrc_s_voltage)

    te_rate = critical_msids['2TLEV1RT'].vals[-1]
    ve_rate = critical_msids['2VLEV1RT'].vals[-1]

    telem = {'HRC observing status': hrc_observing_status, 'Format': tm_format, 'Shield Rate': shield_rate, 'Shield State': shield_state,
             'Bus Current (DN)': bus_current_in_dn, 'Bus Current (A)': bus_current_in_amps, 'FEA Temp': fea_temp, 'HRC-I Voltage Steps': hrc_i_voltage, 'HRC-I Status': hrc_i_status, 'HRC-S Voltage Steps': hrc_s_voltage, 'HRC-S Status': hrc_s_status, 'TE Rate': te_rate, 'VE Rate': ve_rate}

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

    parser.add_argument("--fake_comm", help="Trick the code to think we are in comm. Useful for testing. ",
                        action="store_true")

    parser.add_argument("--report_errors", help="Print MAUDE exceptions (which are common) to the command line",
                        action="store_true")

    args = parser.parse_args()
    return args


def main():

    fetch.data_source.set('maude allow_subset=True')

    args = get_args()
    fake_comm = args.fake_comm
    chatty = args.report_errors  # Will be True if user set --report_errors

    if fake_comm:
        bot_slack_channel = '#bot-testing'
    elif not fake_comm:
        bot_slack_channel = bot_slack_channel = '#comm_passes'

    # Initial settings
    recently_in_comm = False
    in_comm_counter = 0
    telemetry_audit_counter = 0

    # Loop infinitely :)
    while True:

        try:
            in_comm = are_we_in_comm(
                verbose=False, cadence=2, fake_comm=fake_comm)

            if not in_comm:
                if recently_in_comm:
                    # We might have just had a loss in telemetry. Try again after waiting for a minute
                    time.sleep(60)
                    in_comm = are_we_in_comm(verbose=False, cadence=2)
                    if in_comm:
                        continue

                    # Assuming the end of comm is real, then comm has recently ended and we need to report that.
                    telem = grab_critical_telemetry(
                        start=CxoTime.now() - 1800 * u.s)
                    message = f"It appears that COMM has ended as of `{CxoTime.now().strftime('%m/%d/%Y %H:%M:%S')}` \n\n HRC was *{telem['HRC observing status']}* \n Last telemetry was in `{telem['Format']}` \n\n *HRC-I* was {telem['HRC-I Status']} \n *HRC-S* was {telem['HRC-S Status']} \n\n *Shields were {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps` \n\n *HRC-I* Voltage Steps were (Top/Bottom) = `{telem['HRC-I Voltage Steps'][0]}/{telem['HRC-I Voltage Steps'][1]}` \n *HRC-S* Voltage Steps were (Top/Bottom) = `{telem['HRC-S Voltage Steps'][0]}/{telem['HRC-S Voltage Steps'][1]}`  \n\n *Bus Current* was `{telem['Bus Current (DN)']} DN` (`{telem['Bus Current (A)']} A`)  \n\n *FEA Temperature* was `{telem['FEA Temp']} C`"
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

                if in_comm_counter == 0:
                    # Then start the clock on the comm pass
                    comm_start_timestamp = CxoTime.now()

                recently_in_comm = True
                in_comm_counter += 1
                telemetry_audit_counter += 1

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
                    message = f"We are now *IN COMM* as of `{CxoTime.now().strftime('%m/%d/%Y %H:%M:%S')}` (_Chandra_ time). \n\n HRC is *{telem['HRC observing status']}*  \n Telemetry Format = `{telem['Format']}` \n\n *HRC-I* is {telem['HRC-I Status']} \n *HRC-S* is {telem['HRC-S Status']} \n\n *Shields are {telem['Shield State']}* with a count rate of `{telem['Shield Rate']} cps` \n\n *HRC-I* Voltage Steps (Top/Bottom) = `{telem['HRC-I Voltage Steps'][0]}/{telem['HRC-I Voltage Steps'][1]}` \n *HRC-S* Voltage Steps (Top/Bottom) = `{telem['HRC-S Voltage Steps'][0]}/{telem['HRC-S Voltage Steps'][1]}`  \n \n *Total Event* Rate = `{telem['TE Rate']} cps`   \n *Valid Event* Rate = `{telem['VE Rate']} cps`  \n \n *Bus Current* is `{telem['Bus Current (DN)']} DN` (`{telem['Bus Current (A)']} A`) \n \n *FEA Temperature* is `{telem['FEA Temp']} C`"
                    # Send the message using our slack bot
                    send_slack_message(message, channel=bot_slack_channel)
                    # do a first audit of the telemetry upon announcement

                if telemetry_audit_counter == 10:
                    # Reset the audit counter
                    telemetry_audit_counter = 0
                    # Now we've waited a minute. Let's audit the telemetry and send amessage.
                    # Check starting from the beginning of comm. We always check an ever-expanding
                    # chunk of telemetry. This is a BIT redundant, but not bad.
                    audit_telemetry(start=comm_start_timestamp,
                                    channel=bot_slack_channel)


        except Exception as e:
            # MAUDE queries fail regularly as TM is streaming in (mismatched array sizes as data is being populated), 404s, etc.
            # The solution is almost always to simply try again. Therefore this script just presses on in the event of an Exception.

            if chatty:
                # Then we want a verbose error message, because we're obviously in testing mode
                print(f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) ERROR: {e}')
                print("Heres the traceback:")
                print(traceback.format_exc())
                print(f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) Pressing on ...')
            elif not chatty:
                # Then we're likely in operational mode. Ignore the errors on the command line.
                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) ERROR encountered! Use --report_errors to display them.                             ', end='\r\r\r')
            if in_comm_counter > 0:
                # Reset the comm counter to make the error "not count"
                in_comm_counter -= 1
            continue


if __name__ == '__main__':
    main()
