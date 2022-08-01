#!/usr/bin/env conda run -n ska3 python
import collections
import datetime as dt
import socket
import sys
import time
import yaml
import subprocess

import numpy as np
import pytz
import requests
from astropy.table import Table
from astropy.time import Time
from Chandra.Time import DateTime as cxcDateTime
from cheta import fetch
from matplotlib import pyplot as plt
import matplotlib.dates as mdate
from Ska.Matplotlib import cxctime2plotdate as cxc2pd

import argparse

import plot_stylers
from plot_helpers import drawnow
from chandratime import convert_chandra_time, convert_to_doy
from goes_proxy import get_goes_proxy


def get_comms(DSN_COMMS_FILE='/proj/sot/ska/data/dsn_summary/dsn_summary.yaml'):
    """
    Get the list of comm passes from the DSN summary file. SCP it if necessary.
    """
    try:
        comms_table = yaml.safe_load(open(DSN_COMMS_FILE, 'r'))
    except FileNotFoundError:
        print('DSN summary file not found. SCPing from SOT...')

        subprocess.run(
            ["scp", "tremblay@kady.cfa.harvard.edu:/proj/sot/ska/data/dsn_summary/dsn_summary.yaml", "./dsn_summary.yaml"])
        comms_table = yaml.safe_load(open('dsn_summary.yaml', 'r'))
    return comms_table


def grab_orbit_metadata(plot_start=dt.date.today() - dt.timedelta(days=5)):

    # Grab the metadata (orbit, obsid, and radzone info) for the specified time period
    # This may well fail. You should wrap this in a try/except block.
    # from kadi import events
    # orbits = events.orbits.filter(
    #     start=convert_to_doy(plot_start)).table

    comms = get_comms()
    try:
        from kadi import events
        orbits = events.orbits.filter(start=convert_to_doy(plot_start)).table
        radzone_start_times = convert_chandra_time(
            orbits['t_perigee'] + orbits['dt_start_radzone'])
        radzone_stop_times = convert_chandra_time(
            orbits['t_perigee'] + orbits['dt_stop_radzone'])
    except Exception as e:
        radzone_start_times = None
        radzone_stop_times = None

    return comms, radzone_start_times, radzone_stop_times

    # # Radzone t_start is with respect to t_perigee, not t_start!
    # radzone_start_times = convert_chandra_time(
    #     orbits['t_perigee'] + orbits['dt_start_radzone'])
    # radzone_stop_times = convert_chandra_time(
    #     orbits['t_perigee'] + orbits['dt_stop_radzone'])

    # # comm_start_times = convert_chandra_time(comms['tstart'] + 3600)

    # return orbits, comms, comm_start_times, radzone_start_times, radzone_stop_times


def make_shield_plot(fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/', plot_start=dt.date.today() - dt.timedelta(days=5), plot_stop=dt.date.today() + dt.timedelta(days=3), custom_ylims=None, show_plot=False, custom_save_name=None, figure_size=(16, 8), save_dpi=300, debug_prints=False):

    fetch.data_source.set('maude allow_subset=False')

    msidlist = ['2TLEV1RT', '2VLEV1RT', '2SHEV1RT']
    namelist = ['Total Event Rate', 'Valid Event Rate', 'AntiCo Shield Rate']

    try:
        # orbits, comms, comm_start_times, radzone_start_times, radzone_stop_times = grab_orbit_metadata(
        #     plot_start=plot_start)
        comms, radzone_start_times, radzone_stop_times = grab_orbit_metadata()
    except OSError as e:
        comms = None
        radzone_start_times = None
        radzone_stop_times = None
        if debug_prints:
            print(e)

    fig, ax = plt.subplots(figsize=figure_size)

    for i, msid in enumerate(msidlist):
        data = fetch.get_telem(msid, start=convert_to_doy(
            plot_start), sampling='full', max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
        # ax.plot(data[msid].times, data[msid].vals, label=msid)
        ax.plot_date(convert_chandra_time(
            data[msid].times), data[msid].vals, marker='o', fmt="", markersize=1.5, label=namelist[i])

    # Try to plot the GOES proxy rates. Don't die if it fails.
    try:
        goes_times, goes_rates = get_goes_proxy()
        ax.plot_date(goes_times, goes_rates, marker=None, fmt="",
                     alpha=0.8, zorder=1, label='GOES-16 Proxy')
    except Exception as e:
        # this is very bad practice
        if debug_prints:
            print(e)
        pass

    ax.set_ylabel(r'Event Rates (counts s$^{-1}$)', fontsize=10)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_yscale('log')  # symlog will show zero but it's kinda not needed
    if custom_ylims is None:
        ax.set_ylim(10, 2000000)
    elif custom_ylims is not None:
        ax.set_ylim(custom_ylims[0], custom_ylims[1])
    ax.set_xlim(plot_start, plot_stop)
    ax.set_title('Shield & Detector Rates as of {} EST'.format(dt.datetime.now(
    ).strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=10, pad=20)
    ax.axhline(60000, color=plot_stylers.red,
               linewidth=2, label='SCS 107 Limit')
    ax.legend(prop={'size': 12}, loc=2)
    ax.legend(markerscale=6)

    ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1],
            'Now', fontsize=12, color='slategray', zorder=3, ha='center')
    ax.axvline(dt.datetime.now(pytz.utc), color='gray', alpha=0.5)

    if comms is not None:
        if radzone_start_times is not None:
            for i, (radzone_start, radzone_stop) in enumerate(zip(radzone_start_times, radzone_stop_times)):
                ax.axvspan(radzone_start, radzone_stop,
                           alpha=0.3, color='slategray', zorder=1)
                ax.text((radzone_start + radzone_stop) / 2, 300000, 'Radzone for \n Orbit {}'.format(
                    orbits['orbit_num'][i]), color='slategray', fontsize=6, ha='center', clip_on=True)

        for i, comm in enumerate(comms):
            x = mdate.num2date(
                cxc2pd(cxcDateTime(comm['bot_date']['value']).secs))

            plt.vlines(x=x, ymin=80000, ymax=110000,
                       color='cornflowerblue', alpha=1, zorder=2)
            ax.text(x, 120000, 'Comm \n {}'.format(
                comm['station']['value'][:6]), color='cornflowerblue', fontsize=6, ha='center', clip_on=True)

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

    # # Cleanup
    # args = parse_args()
    # if args.monitor is False:
    #     plt.close('all')
    #     fetch.data_source.set('cxc')


def parse_args():

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--monitor', action='store_true')
    argparser.add_argument('--verbose', action='store_true')

    args = argparser.parse_args()

    return args


if __name__ == "__main__":

    args = parse_args()

    hostname = socket.gethostname().split('.')[0]

    allowed_hosts = {'han-v': '/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/',
                     'symmetry': '/Users/grant/Desktop/',
                     'semaphore': '/Users/grant/Desktop/',
                     'MacBook-Pro': '/Users/grant/Desktop/'}

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
