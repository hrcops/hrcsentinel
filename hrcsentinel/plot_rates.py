#!/usr/bin/env conda run -n ska3 python

from matplotlib import pyplot as plt


import socket
from kadi import events
from Ska.engarchive import fetch_sci as fetch
import datetime as dt

from chandratime import convert_chandra_time, convert_to_doy
import plot_stylers


def make_shield_plot(fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/', plot_start=dt.date.today() - dt.timedelta(days=5), plot_stop=dt.date.today() - dt.timedelta(days=5)):

    fetch.data_source.set('maude allow_subset=False')

    msidlist = ['2TLEV1RT', '2VLEV1RT', '2SHEV1RT']
    namelist = ['Total Event Rate', 'Valid Event Rate', 'AntiCo Shield Rate']

    fig, ax = plt.subplots(figsize=(16, 8))

    for i, msid in enumerate(msidlist):
        data = fetch.get_telem(msid, start=convert_to_doy(
            plot_start), sampling='full', max_fetch_Mb=100000, max_output_Mb=100000, quiet=True)
        # ax.plot(data[msid].times, data[msid].vals, label=msid)
        ax.plot_date(convert_chandra_time(
            data[msid].times), data[msid].vals, marker='o', markersize=1.5, label=namelist[i])

    ax.set_ylabel(r'Event Rates (counts s$^{-1}$)', fontsize=10)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_yscale('symlog')
    ax.set_ylim(0, 2000000)
    ax.set_title('Recent Shield & Detector Rates',
                 color='slategray', loc='center')
    ax.axhline(60000, color=plot_stylers.red, linestyle='-',
               linewidth=2, label='SCS 107 Limit')
    ax.legend(prop={'size': 12}, loc=2)
    ax.legend(markerscale=6)

    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)

    hostname = socket.gethostname().split('.')[0]
    if hostname == 'han-v':
        from kadi import events
        orbits = events.orbits.filter(start=convert_to_doy(plot_start)).table
        radzone_start = orbits['start_radzone']  # in 2021:347:17:35:14.442
        radzone_stop = orbits['stop_radzone']  # in 2021:347:17:35:14.442

    fig.savefig(fig_save_directory + 'events.png',
                dpi=300, bbox_inches='tight')
    fig.savefig(fig_save_directory + 'events.pdf',
                dpi=300, bbox_inches='tight')
    plt.close('all')
    fetch.data_source.set('cxc')


if __name__ == "__main__":
    print('Updating Shield Plot...')
    make_shield_plot()
    plt.show()
    print('Done')
