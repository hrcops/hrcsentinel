#!/usr/bin/env/python

import os
import sys
import time
import argparse
import socket

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
import pytz

import event_times
from plot_helpers import scp_file_to_hrcmonitor
import traceback

from heartbeat import are_we_in_comm, timestamp_string, force_timeout, TimeoutException
from Ska.Matplotlib import cxctime2plotdate as cxc2pd
from chandratime import cxctime_to_datetime as cxc2dt
from global_configuration import allowed_hosts


def format_dates(cheta_dates, scp=False):
    return np.array([dt.datetime.strptime(d, '%Y:%j:%H:%M:%S.%f') for d in CxoTime(cheta_dates).date])


def make_interactives(telem_start, telem_stop=None, save_dir='/Users/grant/Desktop/', scp=False):

    # Set the MSIDs we want to plot
    voltage_msids = ['2P15VAVL', '2N15VAVL',
                     '2P05VAVL']

    step_msids = ['2IMTPAST', '2SPTPAST']

    rate_msids = ['2TLEV1RT',  # The Total Event Rate
                  '2VLEV1RT',  # VAlie Event Rate
                  '2SHEV1RT',  # Shield Event Rate
                  ]

    # i previously included '2LVPLATM', '2DTSTATT', '2SPINATM'
    temperature_msids = ['2FHTRMZT', '2CHTRPZT', '2CEAHVPT']

    state_msids = ['215PCAST']

    voltage_plot_colors = ["#003f5c", "#bc5090", "#ffa600"]
    rate_plot_colors = ["#edae49", "#d1495b", "#00798c"]
    temperature_plot_colors = ["#fb8b24", "#d90368", "#820263"]

    # Fetch the telemetry
    voltage_telem = fetch.MSIDset(
        voltage_msids, start=telem_start, stop=telem_stop)
    rate_telem = fetch.MSIDset(rate_msids, start=telem_start, stop=telem_stop)
    temperature_telem = fetch.MSIDset(
        temperature_msids, start=telem_start, stop=telem_stop)
    state_telem = fetch.MSIDset(
        state_msids, start=telem_start, stop=telem_stop)
    step_telem = fetch.MSIDset(step_msids, start=telem_start, stop=telem_stop)

    fig_voltages = make_subplots(specs=[[{"secondary_y": True}]])

    for i, msid in enumerate(voltage_msids):
        fig_voltages.add_trace(go.Scatter(
            x=cxc2dt((voltage_telem[msid].times)), y=voltage_telem[msid].vals, name=msid, line=dict(color=voltage_plot_colors[i])))

    for i, msid in enumerate(state_msids):
        fig_voltages.add_trace(go.Scatter(
            x=cxc2dt((state_telem[msid].times)), y=state_telem[msid].vals, name=msid, opacity=0.8, line=dict(color='#4f6d7a', width=0.5)), secondary_y=True)

    fig_steps = make_subplots(specs=[[{"secondary_y": True}]])

    for i, msid in enumerate(step_msids):
        fig_steps.add_trace(go.Scatter(
            x=cxc2dt((step_telem[msid].times)), y=step_telem[msid].vals, name=msid, opacity=0.8))

    fig_rates = make_subplots(specs=[[{"secondary_y": True}]])

    for i, msid in enumerate(rate_msids):
        fig_rates.add_trace(go.Scatter(
            x=cxc2dt((rate_telem[msid].times)), y=rate_telem[msid].vals, name=msid, opacity=0.8, line=dict(color=rate_plot_colors[i])))

    for i, msid in enumerate(state_msids):
        fig_rates.add_trace(go.Scatter(
            x=cxc2dt((state_telem[msid].times)), y=state_telem[msid].vals, name=msid, opacity=0.8, line=dict(color='#4f6d7a', width=0.5)), secondary_y=True)

    # now make the temperatures plot
    fig_temperatures = make_subplots(specs=[[{"secondary_y": True}]])

    for i, msid in enumerate(temperature_msids):
        fig_temperatures.add_trace(go.Scatter(
            x=cxc2dt((temperature_telem[msid].times)), y=temperature_telem[msid].vals, name=msid,  line=dict(color=temperature_plot_colors[i])))

    for i, msid in enumerate(state_msids):
        fig_temperatures.add_trace(go.Scatter(
            x=cxc2dt((state_telem[msid].times)), y=state_telem[msid].vals, name=msid, opacity=0.8, line=dict(color='#4f6d7a', width=0.5)), secondary_y=True)

    # ANNOTATE THE PLOTS

    # Add the critical temperature thresholds as horizontal lines

    if telem_stop is None:
        fig_voltages.add_vline(
            dt.datetime.utcnow(), line_width=1)

        fig_rates.add_vline(dt.datetime.utcnow(), line_width=1)

        fig_temperatures.add_vline(dt.datetime.utcnow(), line_width=1)

        fig_voltages.add_annotation(x=dt.datetime.utcnow(), y=0,
                                    text="Now",
                                    showarrow=True,
                                    arrowhead=1,
                                    xshift=-3)

        fig_rates.add_annotation(x=dt.datetime.utcnow(), y=1000,
                                 text="Now",
                                 showarrow=True,
                                 arrowhead=1,
                                 xshift=-3)

        fig_temperatures.add_annotation(x=dt.datetime.utcnow(), y=0,
                                        text="Now",
                                        showarrow=True,
                                        arrowhead=1,
                                        xshift=-3)

    # fig_rates.add_hrect(y0=40000, y1=60000, fillcolor="orange", opacity=0.3,
    #                     annotation_text="SCS 107 Trip", annotation_position="inside bottom left")
    # fig_rates.add_hrect(y0=60000, y1=100000, fillcolor="red", opacity=0.3,
    #                     annotation_text="Background rate warning", annotation_position="inside bottom left")

    fig_rates.add_hline(y=60000, line_width=1, line_color="red")

    fig_temperatures.add_hrect(y0=10, y1=12, fillcolor="orange", opacity=0.3,
                               annotation_text="2CEAHVPT Planning Limit", annotation_position="inside bottom left")
    fig_temperatures.add_hrect(y0=12, y1=100, fillcolor="red", opacity=0.3,
                               annotation_text="2CEAHVPT Warning Limit", annotation_position="inside bottom left")

    # FIDDLE WITH PLOT LABELS AND LAYOUT

    fig_voltages.update_layout(
        title=f'Interactive <b>Bus Voltages</b> | Last Five Days | Updated {dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")} EST<br><sup>Updated every three minutes | This plot is interactive; use your mouse to zoom & pan</sup>',
        xaxis_title="Date",
        yaxis_title="<b>Bus Voltages</b> (V)",
        font=dict(size=12),
        template="ggplot2",
        yaxis_range=[-16, 16],
        xaxis_range=[dt.datetime.utcnow()-dt.timedelta(days=6),
                     dt.datetime.utcnow() + dt.timedelta(hours=2)],
        # legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    fig_rates.update_layout(
        title=f'Interactive <b>Event Counts</b> | Last Five Days | Updated {dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")} EST<br><sup>Updated every three minutes | This plot is interactive; use your mouse to zoom & pan</sup>',
        xaxis_title="Date",
        yaxis_title="<b>Event Rates</b> (counts / sec)",
        font=dict(size=12),
        template="ggplot2",
        xaxis_range=[dt.datetime.utcnow()-dt.timedelta(days=6),
                     dt.datetime.utcnow() + dt.timedelta(hours=2)],
        # yaxis_range=[1, 80000],
        yaxis=dict(type='log'),
        # legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    fig_temperatures.update_layout(
        title=f'Interactive <b>Temperatures</b> | Last Five Days | Updated {dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")} EST<br><sup>Updated every three minutes | This plot is interactive; use your mouse to zoom & pan</sup>',
        xaxis_title="Date",
        yaxis_title="<b>Temperatures</b> (C)",
        font=dict(size=12),
        template="ggplot2",
        yaxis_range=[-15, 15],
        xaxis_range=[dt.datetime.utcnow()-dt.timedelta(days=5),
                     dt.datetime.utcnow() + dt.timedelta(hours=2)],
        # legend=dict(yanchor="top", y=1, xanchor="right", x=1)
    )

    # fiddle with the secondary y (counts) axis
    # fig_voltages.update_yaxes(
    #     title_text="<b>Event Rates</b> (counts / sec)", secondary_y=True)
    fig_voltages.update_yaxes(
        title_text="<b>+15V State</b> (on / off)", secondary_y=True, showgrid=False)
    fig_rates.update_yaxes(
        title_text="<b>+15V State</b> (on / off)", secondary_y=True, showgrid=False)

    fig_temperatures.update_yaxes(
        title_text="<b>+15V State</b> (on / off)", secondary_y=True, showgrid=False)

    # SAVE THE PLOTS

    # Set the paths of the HTML files we'll create
    voltages_plot_file = os.path.join(save_dir, 'voltages.html')
    rates_plot_file = os.path.join(save_dir, 'rates.html')
    temperatures_plot_file = os.path.join(save_dir, 'temperatures.html')
    steps_plot_file = os.path.join(save_dir, 'steps.html')

    # Save the plots to HTML files
    fig_voltages.write_html(
        voltages_plot_file, auto_open=True, full_html=False, config=dict(displaylogo=False))
    fig_rates.write_html(
        rates_plot_file, auto_open=True, full_html=False, config=dict(displaylogo=False))
    fig_temperatures.write_html(
        temperatures_plot_file, auto_open=True, full_html=False, config=dict(displaylogo=False))

    fig_steps.write_html(
        steps_plot_file, auto_open=True, full_html=False, config=dict(displaylogo=False))

    if scp is True:
        if os.path.exists('/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/'):
            # then we are either on the HEAD lan or the drive is already mounted; no need to SCP!
            print(f'({timestamp_string()}) You have selected --scp but there is no need, I already see the directory /proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/ on this machine.')

        else:
            scp_file_to_hrcmonitor(file_to_scp=voltages_plot_file)
            scp_file_to_hrcmonitor(file_to_scp=rates_plot_file)
            scp_file_to_hrcmonitor(file_to_scp=temperatures_plot_file)


def parse_args():

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--show_once', action='store_true')

    argparser.add_argument('--test_anomaly', action='store_true')

    argparser.add_argument('--scp', action='store_true')

    argparser.add_argument('--verbose', action='store_true')

    args = argparser.parse_args()

    return args


def main():

    args = parse_args()

    print('\033[1mHRCSentinel\033[0m | Interactive Plot Generator')

    hostname = socket.gethostname().split('.')[0]
    if hostname in allowed_hosts:
        fig_save_directory = allowed_hosts[hostname]
        if args.verbose:
            print(
                f'({timestamp_string()}) Recognized host: {hostname}. Plots will be saved to {fig_save_directory}')

    fetch.data_source.set('maude allow_subset=False')

    five_days_ago = dt.datetime.now() - dt.timedelta(days=5)
    telem_start = convert_to_doy(five_days_ago)
    telem_stop = None

    if args.test_anomaly is True:
        telem_start = '2020:236'
        telem_stop = '2020:240'
        make_interactives(
            telem_start=telem_start, telem_stop=telem_stop, save_dir=fig_save_directory, scp=args.scp)
        sys.exit()

    iteration_counter = 0
    sleep_period_seconds = 300

    if args.show_once is True:
        make_interactives(telem_start)

    elif args.show_once is False:

        while True:

            iteration_counter += 1

            try:
                with force_timeout(600):  # this shouldn't take longer than 10 minutes
                    print(
                        f'({timestamp_string()}) Refreshing interactive plots (iteration {iteration_counter})... ', end="\r", flush=True)
                    make_interactives(
                        telem_start, telem_stop=telem_stop, save_dir=fig_save_directory, scp=args.scp)

                    for i in range(0, sleep_period_seconds):
                        print('Refreshing interactive plots in {} seconds...                                    '.format(
                            sleep_period_seconds-i), end="\r", flush=True)
                        sys.stdout.write("\033[K")
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
