#!/usr/bin/env/python

import os
import time
import argparse

import matplotlib.pyplot as plt
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from astropy import units as u

from cheta import fetch_sci as fetch
from cxotime import CxoTime
from Chandra.Time import DateTime as chandraDateTime
from chandratime import convert_to_doy
import datetime as dt

import event_times
from plot_helpers import scp_file_to_hrcmonitor
import traceback

from heartbeat import are_we_in_comm, timestamp_string, force_timeout, TimeoutException
from Ska.Matplotlib import cxctime2plotdate as cxc2pd
from chandratime import cxctime_to_datetime


def format_dates(cheta_dates):
    return np.array([dt.datetime.strptime(d, '%Y:%j:%H:%M:%S.%f') for d in CxoTime(cheta_dates).date])


def make_interactives(telem_start):

    msidlist = ['2P15VAVL', '2N15VAVL', '2P05VAVL',
                '2FHTRMZT', '2CHTRPZT', '2CEAHVPT', '2LVPLATM', '2DTSTATT', '2SPINATM']
    telem = fetch.MSIDset(msidlist, start=telem_start)

    fig = make_subplots()

    for msid in msidlist[:3]:
        fig.add_trace(go.Scatter(
            x=cxctime_to_datetime((telem[msid].times)), y=telem[msid].vals, name=msid))

    fig.update_layout(
        title=f'Interactive Voltages | Updated {dt.datetime.now().strftime("%b %d %H:%M:%S")}',
        xaxis_title="Date",
        yaxis_title="Bus Voltages (V)",
        font=dict(size=12),
        template="ggplot2",
        yaxis_range=[-16, 30],
        # legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    out_html_file = '/Users/grant/Desktop/voltages.html'

    fig.write_html(out_html_file, auto_open=True, full_html=False)
    # scp_file_to_hrcmonitor(file_to_scp=out_html_file)

    fig2 = make_subplots()

    for msid in msidlist[3:]:
        fig.add_trace(go.Scatter(
            x=cxctime_to_datetime((telem[msid].times)), y=telem[msid].vals, name=msid))

    fig2.update_layout(
        title=f'Interactive Temperatures | Updated {dt.datetime.now().strftime("%b %d %H:%M:%S")}',
        xaxis_title="Date",
        yaxis_title="Temperatures (C)",
        font=dict(size=12),
        template="ggplot2",
        yaxis_range=[-15, 15],
        legend=dict(yanchor="top", y=1, xanchor="right", x=1)
    )

    out_html_file = '/Users/grant/Desktop/temperatures.html'
    fig2.write_html(out_html_file, auto_open=True, full_html=False)
    # scp_file_to_hrcmonitor(file_to_scp=out_html_file)


def parse_args():

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--show_once', action='store_true')

    args = argparser.parse_args()

    return args


def main():

    args = parse_args()

    fetch.data_source.set('maude allow_subset=False')

    one_day_ago = dt.datetime.now() - dt.timedelta(days=1)
    telem_start = convert_to_doy(one_day_ago)

    iteration_counter = 0
    sleep_period_seconds = 30

    if args.show_once is True:
        make_interactives(telem_start)

    elif args.show_once is False:

        while True:

            iteration_counter += 1

            try:
                with force_timeout(600):  # this shouldn't take longer than 10 minutes
                    print(
                        f'({timestamp_string()}) Refreshing interactive plots (iteration {iteration_counter})... ', end="\r", flush=True)
                    make_interactives(telem_start)

                    for i in range(0, sleep_period_seconds):
                        print('Refreshing Plotly plots in {} seconds...'.format(
                            sleep_period_seconds-i), end="\r", flush=True)
                        time.sleep(1)  # sleep for 1 second per iteration

            except TimeoutException:
                print(
                    f"({timestamp_string()}) Funtion timed out! Pressing on...                             ", end="\r", flush=True)
                continue

            except Exception as e:
                print(
                    f"({timestamp_string()}) ERROR on iteration {iteration_counter}: {e}")
                print("Heres the traceback:")
                print(traceback.format_exc())
                print(f"({timestamp_string()}) Pressing on...")
                continue


if __name__ == '__main__':
    main()
