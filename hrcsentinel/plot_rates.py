#!/usr/bin/env conda run -n ska3 python
import collections
import datetime as dt
import socket
import sys
import time

import numpy as np
import pytz
import requests
from astropy.table import Table
from astropy.time import Time
from Chandra.Time import DateTime
from cheta import fetch
from kadi import events
from matplotlib import pyplot as plt

import plot_stylers
from chandratime import (calc_time_to_next_comm, convert_chandra_time,
                         convert_to_doy)
from goes_proxy import get_goes_proxy


def grab_orbit_metadata(plot_start=dt.date.today() - dt.timedelta(days=5)):

    # Grab the metadata (orbit, obsid, and radzone info) for the specified time period
    # This may well fail. You should wrap this in a try/except block.

    orbits = events.orbits.filter(
        start=convert_to_doy(plot_start)).table
    comms = events.dsn_comms.filter(
        start=convert_to_doy(plot_start)).table

    # Radzone t_start is with respect to t_perigee, not t_start!
    radzone_start_times = convert_chandra_time(
        orbits['t_perigee'] + orbits['dt_start_radzone'])
    radzone_stop_times = convert_chandra_time(
        orbits['t_perigee'] + orbits['dt_stop_radzone'])

    comm_start_times = convert_chandra_time(comms['tstart'] + 3600)

    return orbits, comms, comm_start_times, radzone_start_times, radzone_stop_times


def make_shield_plot(fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/', plot_start=dt.date.today() - dt.timedelta(days=5), plot_stop=dt.date.today() + dt.timedelta(days=3), show_plot=False, custom_save_name=None, figure_size=(16, 8), save_dpi=300):

    fetch.data_source.set('maude allow_subset=False')

    msidlist = ['2TLEV1RT', '2VLEV1RT', '2SHEV1RT']
    namelist = ['Total Event Rate', 'Valid Event Rate', 'AntiCo Shield Rate']

    try:
        orbits, comms, comm_start_times, radzone_start_times, radzone_stop_times = grab_orbit_metadata(
            plot_start=plot_start)
    except Exception:
        comms = None

    fig, ax = plt.subplots(figsize=figure_size)

    for i, msid in enumerate(msidlist):
        data = fetch.get_telem(msid, start=convert_to_doy(
            plot_start), sampling='full', max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
        # ax.plot(data[msid].times, data[msid].vals, label=msid)
        ax.plot_date(convert_chandra_time(
            data[msid].times), data[msid].vals, marker='o', markersize=1.5, label=namelist[i])

    # Try to plot the GOES proxy rates. Don't die if it fails.
    try:
        goes_times, goes_rates = get_goes_proxy()
        ax.plot_date(goes_times, goes_rates, marker=None, linestyle='-',
                     alpha=0.8, zorder=0, label='GOES-16 Proxy')
    except Exception:
        # this is very bad practice
        pass

    ax.set_ylabel(r'Event Rates (counts s$^{-1}$)', fontsize=10)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_yscale('log')  # symlog will show zero but it's kinda not needed
    ax.set_ylim(10, 2000000)
    ax.set_xlim(plot_start, plot_stop)
    ax.set_title('Shield & Detector Rates as of {} EST | Next Comm is expected in {}'.format(
        dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S"), calc_time_to_next_comm()), color='slategray', size=12, pad=20)
    ax.axhline(60000, color=plot_stylers.red, linestyle='-',
               linewidth=2, label='SCS 107 Limit')
    ax.legend(prop={'size': 12}, loc=2)
    ax.legend(markerscale=6)

    ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1],
            'Now', fontsize=12, color='slategray', zorder=3, ha='center')
    ax.axvline(dt.datetime.now(pytz.utc), color='gray', alpha=0.5)

    if comms is not None:
        for i, (radzone_start, radzone_stop) in enumerate(zip(radzone_start_times, radzone_stop_times)):
            ax.axvspan(radzone_start, radzone_stop,
                       alpha=0.3, color='slategray', zorder=1)
            ax.text((radzone_start + radzone_stop) / 2, 300000, 'Radzone for \n Orbit {}'.format(
                orbits['orbit_num'][i]), color='slategray', fontsize=6, ha='center', clip_on=True)

        for i, comm in enumerate(comms):
            plt.vlines(x=comm_start_times[i], ymin=80000, ymax=110000,
                       color='cornflowerblue', alpha=1, zorder=2)
            ax.text(comm_start_times[i], 120000, 'Comm \n {}'.format(
                comm['station']), color='cornflowerblue', fontsize=6, ha='center', clip_on=True)

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

    # Cleanup
    del data, goes_times, goes_rates
    plt.close('all')
    fetch.data_source.set('cxc')


if __name__ == "__main__":

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

    print('Updating Shield Plot...')
    make_shield_plot(fig_save_directory=fig_save_directory, show_plot=True)
    plt.show()
    print('Done')
