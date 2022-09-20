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

    msidlist = ['2P15VAVL', '2N15VAVL', '2P05VAVL',
                '2FHTRMZT', '2CHTRPZT', '2CEAHVPT', '2LVPLATM', '2DTSTATT', '2SPINATM']
    telem = fetch.MSIDset(msidlist, start=telem_start)

    fig = make_subplots()
    # ts_new = new_cea.times - t_ref_2022.secs
    # ts_old = old_cea.times - t_ref_2020.secs

    if old_telem is not None:
        sideb_reset_2020 = chandraDateTime(event_times.time_of_cap_1543)
        fig.add_trace(go.Scatter(x=(old_telem['old_N15'].times - sideb_reset_2020.secs) / 3600, y=old_telem['old_N15'].vals,
                                 name='+15 V 2020 Behavior', line=dict(color='gray', width=2)), secondary_y=False)
        fig.add_trace(go.Scatter(x=(old_telem['old_P15'].times - sideb_reset_2020.secs) / 3600, y=old_telem['old_P15'].vals,
                                 name='-15V 2020 Behavior', line=dict(color='gray', width=2)), secondary_y=False)

    fig.add_trace(go.Scatter(x=(telem['2P15VAVL'].times - time_zero.secs) /
                  3600, y=telem['2P15VAVL'].vals, name='+15V 2P15VAVL (Now)'))

    fig.add_trace(go.Scatter(x=(telem['2N15VAVL'].times - time_zero.secs) /
                  3600, y=telem['2N15VAVL'].vals, name='-15V DWELL RATE 2N15VAVL'))

    fig.add_trace(go.Scatter(x=(telem['2P05VAVL'].times - time_zero.secs) /
                  3600, y=telem['2P05VAVL'].vals, name='+5 V'))
    # fig.add_trace(go.Scatter(x=ts_old, y=old_cea.vals,
    #                          name='2020 2CEAHVPT', line=dict(width=4)), secondary_y=False)

    fig.update_layout(
        title=f'Interactive Voltages | Updated {dt.datetime.now().strftime("%b %d %H:%M:%S")}',
        xaxis_title="Hours Relative to start of CAP",
        yaxis_title="Bus Voltages (V)",
        font=dict(size=12),
        template="plotly",
        xaxis_range=[-0.5, 4],
        yaxis_range=[-16, 30],
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    fig.add_vline(x=0, line_width=1, line_color="gray")

    fig.add_vline(x=2.9, line_width=1, line_color="gray")

    fig.add_annotation(x=2.9, y=26,
                       text="End",
                       showarrow=False)

    out_html_file = '/Users/grant/Desktop/cap1631_plotly_voltages.html'

    fig.write_html(out_html_file, auto_open=True, full_html=False)
    scp_file_to_hrcmonitor(file_to_scp=out_html_file)

    fig2 = make_subplots()
    # ts_new = new_cea.times - t_ref_2022.secs
    # ts_old = old_cea.times - t_ref_2020.secs

    if old_telem is not None:
        fig2.add_trace(go.Scatter(x=(old_telem['old_cea_temp'].times - sideb_reset_2020.secs) / 3600, y=old_telem['old_cea_temp'].vals,
                                  name='CEA 2020 Behavior', line=dict(color='gray', width=2)), secondary_y=False)
        fig2.add_trace(go.Scatter(x=(old_telem['old_fea_temp'].times - sideb_reset_2020.secs) / 3600, y=old_telem['old_fea_temp'].vals,
                                  name='FEA 2020 Behavior', line=dict(color='gray', width=2)), secondary_y=False)
    # fig.add_trace(go.Scatter(x=ts_old, y=old_cea.vals,
    #                          name='2020 2CEAHVPT', line=dict(width=4)), secondary_y=False)

    fig2.add_trace(go.Scatter(x=(telem['2CEAHVPT'].times - time_zero.secs) /
                              3600, y=telem['2CEAHVPT'].vals, name='2CEAHVPT'))

    fig2.add_trace(go.Scatter(x=(telem['2CHTRPZT'].times - time_zero.secs) /
                              3600, y=telem['2CHTRPZT'].vals, name='2CHTRPZT'))

    fig2.add_trace(go.Scatter(x=(telem['2FHTRMZT'].times - time_zero.secs) /
                              3600, y=telem['2FHTRMZT'].vals, name='2FTRMZT'))

    fig2.add_trace(go.Scatter(x=(telem['2LVPLATM'].times - time_zero.secs) /
                              3600, y=telem['2LVPLATM'].vals, name='2LVPLATM'))

    fig2.add_trace(go.Scatter(x=(telem['2DTSTATT'].times - time_zero.secs) /
                              3600, y=telem['2DTSTATT'].vals, name='2DTSTATT'))

    fig2.add_trace(go.Scatter(x=(telem['2SPINATM'].times - time_zero.secs) /
                              3600, y=telem['2SPINATM'].vals, name='2SPINATM'))

    fig2.add_vline(x=0, line_width=1, line_color="gray")

    fig2.add_vline(x=2.9, line_width=1, line_color="gray")

    fig2.add_hline(y=10, line_width=4, line_color="red")

    fig2.add_annotation(x=2.9, y=11,
                        text="End",
                        showarrow=False)

    fig2.update_layout(
        title=f'Interactive Temperatures | Updated {dt.datetime.now().strftime("%b %d %H:%M:%S")}',
        xaxis_title="Hours Relative to start of CAP",
        yaxis_title="Temperatures (C)",
        font=dict(size=12),
        template="plotly",
        xaxis_range=[-0.5, 4],
        yaxis_range=[-15, 15],
        legend=dict(yanchor="top", y=1, xanchor="right", x=1)
    )

    out_html_file = '/Users/grant/Desktop/cap1631_plotly_temperatures.html'
    fig2.write_html(out_html_file, auto_open=True, full_html=False)
    scp_file_to_hrcmonitor(file_to_scp=out_html_file)


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

    telem_start = '2022:237'
    # time_zero = CxoTime.now()  # fake for testing
    time_zero = CxoTime('2022:237:18:50:01.000')  # CAP start

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
