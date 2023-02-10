#!/usr/bin/env conda run -n ska3 python
import os
import argparse
import datetime as dt
import json
import socket
import sys
import time
import urllib.request
from urllib.error import HTTPError

import matplotlib.dates as mdate
import numpy as np
import pytz
import requests
import yaml
from astropy.table import Table
from astropy.time import Time
from Chandra.Time import DateTime as cxcDateTime
from cheta import fetch
from kadi import events
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
from Ska.Matplotlib import cxctime2plotdate as cxc2pd

from global_configuration import allowed_hosts
import plot_stylers
from chandratime import cxctime_to_datetime, convert_to_doy
from goes_proxy import get_goes_proxy
from plot_helpers import drawnow

from heartbeat import timestamp_string


def grab_orbit_metadata(plot_start=dt.date.today() - dt.timedelta(days=5)):
    '''
    Use the web-Kadi API to grab orbit metadata.
    This allows us to query Kadi and avoid the events.db3 update hiccup

    See here for web-Kadi: https://kadi.cfa.harvard.edu/api/
    '''
    orbit_metadata = {}

    for event in ("orbits", "dsn_comms"):

        request_string = f"https://kadi.cfa.harvard.edu/api/ska_api/kadi/events/{event}/filter?start={convert_to_doy(plot_start)}&stop={convert_to_doy(dt.date.today() + dt.timedelta(days=3))}"

        with urllib.request.urlopen(request_string, timeout=40) as url:
            orbit_metadata[event] = json.load(url)

        time.sleep(10)

    return orbit_metadata


def make_shield_plot(fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/', plot_start=dt.date.today() - dt.timedelta(days=5), plot_stop=dt.date.today() + dt.timedelta(days=3), custom_ylims=None, show_plot=False, custom_save_name=None, figure_size=(16, 8), save_dpi=300, debug_prints=False):
    '''
    Create a shield plot. Fix this.
    '''

    # Get the orbit metadata. Don't die if it fails. Try three times.
    attempts = 0
    max_attempts = 4  # how many times to try to get the metadata
    while attempts <= max_attempts:
        try:
            orbit_metadata = grab_orbit_metadata(
                plot_start=plot_start)
            # Save that successfully fetched orbit metadata as a json file for loading just in case
            with open("last_orbit_metadata.json", "w") as orbit_metadata_json_file:
                json.dump(orbit_metadata, orbit_metadata_json_file)
            using_stale_orbit_metadata = False
            # print(
            #     f'Successfully fetched orbit metadata and saved it as last_orbit_metadata.json.')
            break

        except HTTPError as shit:
            attempts += 1
            time.sleep(10)  # give the server a few to chill...
            print(
                f'Got 500 Error from Kadi server ({shit}). Trying again...')

    if attempts > max_attempts:
        # then give up and try to load the json file
        try:
            with open("last_orbit_metadata.json", "r") as orbit_metadata_json_file:
                orbit_metadata = json.load(orbit_metadata_json_file)
            using_stale_orbit_metadata = True

        except Exception as e:
            print(f'Could not load orbit metadata from json file: {e}')
            orbit_metadata = None

    fetch.data_source.set('maude allow_subset=False')

    msidlist = ['2TLEV1RT', '2VLEV1RT', '2SHEV1RT']
    namelist = ['Total Event Rate', 'Valid Event Rate', 'AntiCo Shield Rate']

    fig, ax = plt.subplots(figsize=figure_size)

    for i, msid in enumerate(msidlist):
        data = fetch.get_telem(msid, start=convert_to_doy(
            plot_start), sampling='full', max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
        # ax.plot(data[msid].times, data[msid].vals, label=msid)
        ax.plot_date(cxctime_to_datetime(
            data[msid].times), data[msid].vals, marker='o', fmt="", markersize=1.5, label=namelist[i])

    # Try to plot the GOES proxy rates. Don't die if it fails.
    try:
        goes_times, goes_rates = get_goes_proxy()
        ax.plot_date(goes_times, goes_rates, marker=None, fmt="",
                     alpha=0.8, zorder=1, label='GOES-16 Proxy')
    except Exception as e:
        # This is bad practice but I don't give a !@#$%
        print('Error grabbing GOES proxy: {}'.format(e))

    ax.set_ylabel(r'Event Rates (counts s$^{-1}$)', fontsize=10)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_yscale('log')  # symlog will show zero but it's kinda not needed
    if custom_ylims is None:
        ax.set_ylim(10, 2000000)
    elif custom_ylims is not None:
        ax.set_ylim(custom_ylims[0], custom_ylims[1])
    ax.set_xlim(plot_start, plot_stop)
    if using_stale_orbit_metadata:
        ax.set_title("Shield & Detector Rates as of {} EST | Orbit metadata is out-of-date".format(dt.datetime.now(tz=pytz.timezone(
            'US/Eastern')).strftime('%Y-%b-%d %H:%M:%S')), color='slategray', size=12, pad=20)
    else:
        ax.set_title("Shield & Detector Rates as of {} EST".format(dt.datetime.now(tz=pytz.timezone(
            'US/Eastern')).strftime('%Y-%b-%d %H:%M:%S')), color='slategray', size=12, pad=20)
    ax.axhline(60000, color=plot_stylers.red,
               linewidth=2, label='SCS 107 Limit')

    ax.text(dt.datetime.now(tz=pytz.timezone('US/Eastern')), ax.get_ylim()[1],
            'Now', fontsize=12, color='slategray', zorder=3, ha='center')
    ax.axvline(dt.datetime.now(tz=pytz.timezone(
        'US/Eastern')), color='gray', alpha=0.5)

    if orbit_metadata is not None:

        for i, comm in enumerate(orbit_metadata["dsn_comms"]):

            comm_start_raw = comm['tstart'] + 3600
            comm_stop_raw = comm['tstop']

            comm_start = cxctime_to_datetime(comm_start_raw)
            comm_stop = cxctime_to_datetime(comm_stop_raw)
            comm_midpoint = cxctime_to_datetime(
                (comm_stop_raw + comm_start_raw) / 2)

            # comm_midpoint = mdate.num2date((cxc2pd(cxcDateTime(
            #     comm['tstart']).secs) + cxc2pd(cxcDateTime(comm['tstop']).secs)) / 2)

            # we assume call-up to bot is 1 hour here. rough.
            comm_duration = np.round((comm['dur'] - 3600) / 3600, 1)

            ax.axvspan(comm_start, comm_stop, ymin=0.65, ymax=0.76,
                       alpha=0.3, color='cornflowerblue', zorder=2)

            # ax.add_patch(Rectangle((1, 1), 2, 6))

            ax.text(comm_midpoint, 120000, f"Comm \n {comm['station'][:6]} \n ~{comm_duration} hr",
                    color='cornflowerblue', fontsize=6, ha='center', clip_on=True)

        for i, orbit in enumerate(orbit_metadata["orbits"]):

            # # Radzone t_start is with respect to t_perigee, not t_start!

            radzone_start_raw = orbit['t_perigee'] + orbit['dt_start_radzone']
            radzone_stop_raw = orbit['t_perigee'] + orbit['dt_stop_radzone']

            radzone_start = cxctime_to_datetime(radzone_start_raw)
            radzone_stop = cxctime_to_datetime(radzone_stop_raw)

            radzone_midpoint = cxctime_to_datetime(
                (radzone_stop_raw + radzone_start_raw) / 2)

            ax.axvspan(radzone_start, radzone_stop,
                       alpha=0.3, color='slategray', zorder=1)
            ax.text(radzone_midpoint, 300000, f"Radzone for \n Orbit {orbit['orbit_num']}", color='slategray',
                    fontsize=6, ha='center', clip_on=True)

    ax.legend(prop={'size': 12}, loc='lower left')
    ax.legend(markerscale=6)

    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    if custom_save_name is None:
        fig.savefig(fig_save_directory + 'events.png',
                    dpi=save_dpi, bbox_inches='tight')
        fig.savefig(fig_save_directory + 'events.pdf',
                    dpi=save_dpi, bbox_inches='tight')
    elif custom_save_name is not None:
        fig.savefig(custom_save_name, dpi=save_dpi, bbox_inches='tight')

    if show_plot is True:
        plt.show()


def parse_args():

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--monitor', action='store_true')
    argparser.add_argument('--verbose', action='store_true')

    args = argparser.parse_args()

    return args


if __name__ == "__main__":

    args = parse_args()

    hostname = socket.gethostname().split('.')[0]

    if hostname in allowed_hosts:
        fig_save_directory = allowed_hosts[hostname]
        print('Recognized host: {}. Plots will be saved to {}'.format(
            hostname, fig_save_directory))
    else:
        sys.exit('Error: Hostname {} not recognized'.format(hostname))

    if args.monitor is False:
        print('Creating a single Shield Plot...')
        make_shield_plot(fig_save_directory=fig_save_directory,
                         show_plot=True, debug_prints=args.verbose)
        plt.show()
        print('Done')
    elif args.monitor is True:

        plot_kwargs = {'fig_save_directory': fig_save_directory,
                       'show_plot': False,
                       'plot_start': dt.date.today() - dt.timedelta(days=1),
                       'custom_ylims': (2000, 7000)
                       }
        plt.ion()
        while True:
            drawnow(make_shield_plot, **plot_kwargs)
