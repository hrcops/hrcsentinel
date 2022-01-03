#!/usr/bin/env conda run -n ska3 python
import sys
from matplotlib import pyplot as plt

import socket
from kadi import events
from cheta import fetch
import datetime as dt
import pytz

from chandratime import convert_chandra_time, convert_to_doy
import plot_stylers



def grab_orbit_metadata(plot_start=dt.date.today() - dt.timedelta(days=5), plot_stop=dt.date.today() + dt.timedelta(days=3)):

    # Grab the metadata (orbit, obsid, and radzone info) for the specified time period
    orbits = events.orbits.filter(start=convert_to_doy(plot_start), stop=(plot_stop)).table
    # obsids = events.obsids.filter(start=convert_to_doy(plot_start), stop=(plot_stop)).table
    comms = events.dsn_comms.filter(start=convert_to_doy(plot_start), stop=(plot_stop)).table

    # orbit_start_times = convert_chandra_time(orbits['tstart'])
    # orbit_stop_times = convert_chandra_time(orbits['tstop'])

    # Radzone t_start is with respect to t_perigee, not t_start!
    radzone_start_times = convert_chandra_time(orbits['t_perigee'] + orbits['dt_start_radzone'])
    radzone_stop_times = convert_chandra_time(orbits['t_perigee'] + orbits['dt_stop_radzone'])

    comm_start_times = convert_chandra_time(comms['tstart'])

    return orbits, comms, comm_start_times, radzone_start_times, radzone_stop_times


def make_shield_plot(fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/', plot_start=dt.date.today() - dt.timedelta(days=5), plot_stop=dt.date.today() + dt.timedelta(days=3), show_plot=False):

    fetch.data_source.set('maude allow_subset=False')

    msidlist = ['2TLEV1RT', '2VLEV1RT', '2SHEV1RT']
    namelist = ['Total Event Rate', 'Valid Event Rate', 'AntiCo Shield Rate']

    orbits, comms, comm_start_times, radzone_start_times, radzone_stop_times = grab_orbit_metadata(plot_start, plot_stop)

    fig, ax = plt.subplots(figsize=(16, 8))

    for i, msid in enumerate(msidlist):
        data = fetch.get_telem(msid, start=convert_to_doy(
            plot_start), sampling='full', max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
        # ax.plot(data[msid].times, data[msid].vals, label=msid)
        ax.plot_date(convert_chandra_time(
            data[msid].times), data[msid].vals, marker='o', markersize=1.5, label=namelist[i])

    ax.set_ylabel(r'Event Rates (counts s$^{-1}$)', fontsize=10)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_yscale('log')  # symlog will show zero but it's kinda not needed
    ax.set_ylim(10, 2000000)
    ax.set_xlim(plot_start, plot_stop)
    ax.set_title('Shield & Detector Rates as of {} EST'.format(
        dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), color='slategray', size=10)
    ax.axhline(60000, color=plot_stylers.red, linestyle='-',
               linewidth=2, label='SCS 107 Limit')
    ax.legend(prop={'size': 12}, loc=2)
    ax.legend(markerscale=6)

    ax.text(dt.datetime.now(pytz.utc), ax.get_ylim()[1],
            'Now', fontsize=12, color='slategray', zorder=3, ha='center')
    ax.axvline(dt.datetime.now(pytz.utc), color='gray', alpha=0.5)

    for i, (radzone_start, radzone_stop) in enumerate(zip(radzone_start_times, radzone_stop_times)):
        ax.axvspan(radzone_start, radzone_stop, alpha=0.3, color='slategray', zorder=1)
        ax.text((radzone_start + radzone_stop) / 2, 300000, 'Radzone for \n Orbit {}'.format(orbits['orbit_num'][i]), color='slategray', fontsize=6, ha='center', clip_on=True)

    for i, comm in enumerate(comms):
        plt.vlines(x=comm_start_times[i], ymin=80000, ymax=110000, color='cornflowerblue', alpha=1, zorder=2)
        ax.text(comm_start_times[i], 120000, 'Comm \n {}'.format(comm['station']), color='cornflowerblue', fontsize=6, ha='center', clip_on=True)

    # print(comms)

    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    fig.savefig(fig_save_directory + 'events.png',
                dpi=300, bbox_inches='tight')
    fig.savefig(fig_save_directory + 'events.pdf',
                dpi=300, bbox_inches='tight')

    if show_plot is True:
        plt.show()
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
