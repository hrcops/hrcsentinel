#!/usr/bin/env/python

import os
import time
import argparse

import matplotlib.pyplot as plt
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots


from cheta import fetch_sci as fetch
from cxotime import CxoTime
from Chandra.Time import DateTime as chandraDateTime
from chandratime import convert_to_doy
import datetime as dt

import event_times
from plot_helpers import scp_file_to_hrcmonitor


def format_dates(cheta_dates):
    return np.array([dt.datetime.strptime(d, '%Y:%j:%H:%M:%S.%f') for d in CxoTime(cheta_dates).date])


def make_interactives(telem_start, time_zero, old_telem=None):

    msidlist = [
        "2FE00ATM",  # Front-end Temperature (c)
        "2LVPLATM",  # LVPS Plate Temperature (c)
        "2IMHVATM",  # Imaging Det HVPS Temperature (c)
        "2IMINATM",  # Imaging Det Temperature (c)
        "2SPHVATM",  # Spectroscopy Det HVPS Temperature (c)
        "2SPINATM",  # Spectroscopy Det Temperature (c)
        "2PMT1T",  # PMT 1 EED Temperature (c)
        "2PMT2T",  # PMT 2 EED Temperature (c)
        "2DCENTRT",  # Outdet2 EED Temperature (c)
        "2FHTRMZT",  # FEABox EED Temperature (c)
        "2CHTRPZT",  # CEABox EED Temperature (c)
        "2FRADPYT",  # +Y EED Temperature (c)
        "2CEAHVPT",  # -Y EED Temperature (c)
        "2CONDMXT",  # Conduit Temperature (c)
        "2UVLSPXT",  # Snout Temperature (c)
        # # CEA Temperature 1 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
        "2CE00ATM",
        # # CEA Temperature 2 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
        "2CE01ATM",
        "2FEPRATM",  # FEA PreAmp (c)
        # # Selected Motor Temperature (c) THIS IS ALWAYS 5 DEGREES THROUGHOUT ENTIRE MISSION
        "2SMTRATM",
        "2DTSTATT"   # OutDet1 Temperature (c)
    ]

    # msidlist = ['2P24VAVL', '2P15VAVL', '2N15VAVL', '2P05VAVL',
    #             '2C05PALV', '2C15PALV', '2C15NALV']
    telem = fetch.MSIDset(msidlist, start=telem_start)

    fig = make_subplots()

    for msid in msidlist:
        fig.add_trace(go.Scatter(
            x=(telem[msid].times), y=telem[msid].vals, name=msid))

    fig.update_layout(
        title=f'Temperatures | Updated {dt.datetime.now().strftime("%b %d %H:%M:%S")}',
        xaxis_title="Chandra Time (seconds since 1998/01/01)",
        yaxis_title="Bus Voltages (V)",
        font=dict(size=12),
        template="plotly",
        # xaxis_range=[-0.5, 3.5],
        yaxis_range=[-16, 26],
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    # fig.add_vline(x=0, line_width=1, line_color="gray")

    # fig.add_vline(x=2.6, line_width=1, line_color="gray")

    fig.add_annotation(x=2.6, y=26,
                       text="EOT",
                       showarrow=False)

    out_html_file = '/Users/grant/Desktop/ssc_1.html'

    fig.write_html(out_html_file, auto_open=True, full_html=False)
    scp_file_to_hrcmonitor(file_to_scp=out_html_file)

    ssd_temps = ['2P24VAVL', '2P15VAVL', '2N15VAVL', '2P05VAVL',
                 '2C05PALV', '2C15PALV', '2C15NALV', '2C15PALV']

    # fig2 = make_subplots()

    # fig2.add_trace(go.Scatter(x=(telem['2CHTRPZT'].times - time_zero.secs) /
    #                           3600, y=telem['2CHTRPZT'].vals, name='CEA Temp'))

    # fig2.add_trace(go.Scatter(x=(telem['2FHTRMZT'].times - time_zero.secs) /
    #                           3600, y=telem['2FHTRMZT'].vals, name='FEA Temp'))

    # fig2.add_vline(x=0, line_width=1, line_color="gray")

    # fig2.add_vline(x=2.6, line_width=1, line_color="gray")

    # fig2.add_annotation(x=2.6, y=11,
    #                     text="EOT",
    #                     showarrow=False)

    # fig2.update_layout(
    #     title=f'Interactive Temperatures | Updated {dt.datetime.now().strftime("%b %d %H:%M:%S")}',
    #     xaxis_title="Hours Relative to start of CAP",
    #     yaxis_title="Temperatures (C)",
    #     font=dict(size=12),
    #     template="plotly",
    #     xaxis_range=[-0.5, 3.5],
    #     yaxis_range=[-10, 10],
    #     legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    # )

    # out_html_file = '/Users/grant/Desktop/ssc_2.html'
    # fig2.write_html(out_html_file, auto_open=True, full_html=False)
    # scp_file_to_hrcmonitor(file_to_scp=out_html_file)


def get_old_telem():

    sideb_reset_2020 = chandraDateTime(event_times.time_of_cap_1543)
    old_N15 = fetch.MSID('2N15VBVL', start=convert_to_doy(event_times.time_of_cap_1543),
                         stop=convert_to_doy(event_times.time_of_cap_1543 + dt.timedelta(days=1)))
    old_P15 = fetch.MSID('2P15VBVL', start=convert_to_doy(event_times.time_of_cap_1543),
                         stop=convert_to_doy(event_times.time_of_cap_1543 + dt.timedelta(days=1)))
    old_cea_temp = fetch.MSID('2CHTRPZT', start=convert_to_doy(event_times.time_of_cap_1543),
                              stop=convert_to_doy(event_times.time_of_cap_1543 + dt.timedelta(days=1)))
    old_fea_temp = fetch.MSID('2FHTRMZT', start=convert_to_doy(event_times.time_of_cap_1543),
                              stop=convert_to_doy(event_times.time_of_cap_1543 + dt.timedelta(days=1)))
    times_old = (old_N15.times - sideb_reset_2020.secs) / 3600

    old_telem = {'old_N15': old_N15,
                 'old_P15': old_P15,
                 'old_cea_temp': old_cea_temp,
                 'old_fea_temp': old_fea_temp,
                 'times_old': times_old}

    return old_telem


def parse_args():

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--monitor', action='store_true')

    args = argparser.parse_args()

    return args


def main():

    args = parse_args()

    fetch.data_source.set('maude allow_subset=False highrate=True')

    telem_start = '2022:213'
    # time_zero = CxoTime.now()  # fake for testing
    time_zero = CxoTime('2022:213:18:34:55')  # CAP start
    iteration_count = 0

    # old_telem = get_old_telem()
    old_telem = None

    if args.monitor is False:
        make_interactives(telem_start, time_zero, old_telem=old_telem)

    elif args.monitor is True:

        sleep_period_seconds = 30

        while True:
            make_interactives(telem_start, time_zero, old_telem=old_telem)
            time.sleep(30)

            for i in range(0, sleep_period_seconds):
                print('Refreshing Plotly plots in {} seconds...'.format(
                    sleep_period_seconds-i), end="\r", flush=True)
                time.sleep(1)  # sleep for 1 second per iteration


if __name__ == '__main__':
    main()
