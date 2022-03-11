#!/usr/bin/env/python

import os
import matplotlib.pyplot as plt
from cheta import fetch_sci as fetch
from kadi import events, cmds

from cxotime import CxoTime
from Chandra.Time import DateTime as chandraDateTime
from chandratime import convert_to_doy
import datetime as dt

import event_times
from plot_helpers import scp_file_to_hrcmonitor

import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def format_dates(cheta_dates):
    return np.array([dt.datetime.strptime(d, '%Y:%j:%H:%M:%S.%f') for d in CxoTime(cheta_dates).date])


def main():

    sideb_reset_2020 = chandraDateTime(event_times.time_of_cap_1543)

    old_N15 = fetch.MSID('2N15VBVL', start=convert_to_doy(event_times.time_of_cap_1543),
                         stop=convert_to_doy(event_times.time_of_cap_1543 + dt.timedelta(days=2)))

    old_P15 = fetch.MSID('2P15VBVL', start=convert_to_doy(event_times.time_of_cap_1543),
                         stop=convert_to_doy(event_times.time_of_cap_1543 + dt.timedelta(days=2)))

    old_cea_temp = fetch.MSID('2CHTRPZT', start=convert_to_doy(event_times.time_of_cap_1543),
                              stop=convert_to_doy(event_times.time_of_cap_1543 + dt.timedelta(days=2)))

    old_fea_temp = fetch.MSID('2FHTRMZT', start=convert_to_doy(event_times.time_of_cap_1543),
                              stop=convert_to_doy(event_times.time_of_cap_1543 + dt.timedelta(days=2)))

    times_old = (old_N15.times - sideb_reset_2020.secs) / 3600

    # t_ref_2022 = DateTime(760799927.93)
    # t_ref_2020 = DateTime('2020:237:03:45:28.577')
    # fetch.data_source.set('maude allow_subset=False highrate=True')
    # old_cea = fetch.MSID('2CEAHVPT', '2020:235', '2020:240')
    # old_fea = fetch.MSID('2FHTRMZT', '2020:235', '2020:240')

    # old_N15 = fetch.MSID('2N15VAVL', '2020:235', '2020:240')
    # old_P15 = fetch.MSID('2P15VAVL', '2020:235', '2020:240')
    # fetch.data_source.set('maude')
    # new_cea = fetch.MSID('2CEAHVPT', '2022:039', '2022:041')
    # new_fea = fetch.MSID('2FHTRMZT', '2022:039', '2022:041')

    # new_N15 = fetch.MSID('2N15VBVL', '2022:039', '2022:041')
    # new_P15 = fetch.MSID('2P15VBVL', '2022:039', '2022:041')

    fig = make_subplots()
    # ts_new = new_cea.times - t_ref_2022.secs
    # ts_old = old_cea.times - t_ref_2020.secs

    fig.add_trace(go.Scatter(x=times_old, y=old_N15.vals,
                             name='+15 V 2020 Behavior', line=dict(color='gray', width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=times_old, y=old_P15.vals,
                             name='-15V 2020 Behavior', line=dict(color='gray', width=2)), secondary_y=False)
    # fig.add_trace(go.Scatter(x=ts_old, y=old_cea.vals,
    #                          name='2020 2CEAHVPT', line=dict(width=4)), secondary_y=False)

    fig.update_layout(
        title="Interactive Voltages (updates every ~20 seconds)",
        xaxis_title="Hours Relative to start of CAP",
        yaxis_title="Bus Volgages (V)",
        font=dict(size=12),
        template="plotly",
        xaxis_range=[-0.5, 3],
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    fig.add_vline(x=0, line_width=1, line_color="gray")

    fig.add_vline(x=2.9, line_width=1, line_color="gray")

    fig.add_annotation(x=2.9, y=-5,
                       text="Deadman",
                       showarrow=False)

    out_html_file = '/Users/grant/Desktop/cap1603_plotly_voltages.html'

    fig.write_html(out_html_file, auto_open=True, full_html=False)
    scp_file_to_hrcmonitor(file_to_scp=out_html_file)

    fig2 = make_subplots()
    # ts_new = new_cea.times - t_ref_2022.secs
    # ts_old = old_cea.times - t_ref_2020.secs

    fig2.add_trace(go.Scatter(x=times_old, y=old_cea_temp.vals,
                              name='CEA 2020 Behavior', line=dict(color='gray', width=2)), secondary_y=False)
    fig2.add_trace(go.Scatter(x=times_old, y=old_fea_temp.vals,
                              name='FEA 2020 Behavior', line=dict(color='gray', width=2)), secondary_y=False)
    # fig.add_trace(go.Scatter(x=ts_old, y=old_cea.vals,
    #                          name='2020 2CEAHVPT', line=dict(width=4)), secondary_y=False)

    fig2.add_vline(x=0, line_width=1, line_color="gray")

    fig2.add_vline(x=2.9, line_width=1, line_color="gray")

    fig2.add_annotation(x=2.9, y=-5,
                        text="Deadman",
                        showarrow=False)

    fig2.update_layout(
        title="Interactive Temperatures",
        xaxis_title="Hours Relative to start of CAP",
        yaxis_title="Temperatures (C)",
        font=dict(size=12),
        template="plotly",
        xaxis_range=[-0.5, 3],
        yaxis_range=[-10, 25],
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    out_html_file = '/Users/grant/Desktop/cap1603_plotly_temperatures.html'
    fig2.write_html(out_html_file, auto_open=True, full_html=False)
    scp_file_to_hrcmonitor(file_to_scp=out_html_file)


if __name__ == '__main__':
    main()
