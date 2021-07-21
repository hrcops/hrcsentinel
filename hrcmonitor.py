#!/usr/bin/env conda run -n ska3 python


import time
import sys
import argparse

import matplotlib
import datetime as dt
import Ska.engarchive.fetch as fetch
import socket
import traceback

import plot_stylers
from plot_dashboard import make_realtime_plot, make_ancillary_plots

from cxotime import CxoTime

from heartbeat import are_we_in_comm

import matplotlib.pyplot as plt
plot_stylers.styleplots()

# Use the new Matplotlib 3.X constrained_layout solver in lieu of tight_layout()
# plt.rcParams['figure.constrained_layout.use'] = True


def comm_status_stamp(comm_status, code_start_time, hostname, fig_save_directory='/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/'):

    if comm_status is True:
        commreport = f'In Comm!'
        subtext = f'Comm appears to have started at {dt.datetime.now().strftime("%H:%M:%S")}'
        textcolor = 'steelblue'
    elif comm_status is False:
        commreport = 'Not in Comm'
        subtext = f'Out of Comm since {dt.datetime.now().strftime("%H:%M:%S")}'
        textcolor = 'slategray'

    code_uptime = dt.datetime.now() - code_start_time

    fig = plt.figure(figsize=(8, 2))
    plt.axis('off')
    plt.tight_layout()
    fig.patch.set_facecolor('white')

    text = plt.text(0.001, 0.2, commreport, color=textcolor, fontsize=50)
    subtext = plt.text(
        0.004, 0.08, subtext, color=textcolor, fontsize=12)
    uptime_text = plt.text(
        0.004, 0.0001, 'HRCMonitor has been running on {} since {} ({} days)'.format(hostname, code_start_time.strftime("%Y %b %d %H:%M:%S"), code_uptime.days), color='slategray', fontsize=9)

    plt.savefig(fig_save_directory + 'comm_status.png', dpi=300)
    plt.close()


def get_args():
    '''Fetch command line args, if given'''

    parser = argparse.ArgumentParser(
        description='Monitor the VCDU telemetry stream, and update critical status plots whenever we are in comm.')

    parser.add_argument("--fake_comm", help="Trick the code to think it's in comm. Useful for testing. ",
                        action="store_true")

    parser.add_argument("--force_ska", help="Trick the code pull from Ska/CXC instead of MAUDE with a switch to fetch.data_source.set() ",
                        action="store_true")

    parser.add_argument("--report_errors", help="Print MAUDE exceptions (which are common) to the command line",
                        action="store_true")

    parser.add_argument("--show_in_gui", help="Show plots with plt.show()",
                        action="store_true")

    args = parser.parse_args()
    return args


def main():
    '''
    The main event loop. Sets plotting parameters and data sources, and makes
    both plots. Saves them to preferred directories. Pauses the loop for a few
    minutes of sleep to avoid overwhelming MAUDE and wasting cycles.
    '''

    hostname = socket.gethostname().split('.')[0] # split is to get rid of .local or .cfa.harvard.edu

    args = get_args()
    fake_comm = args.fake_comm

    if hostname == 'han-v':
        print('Recognized host: {}'.format(hostname))
        fig_save_directory = '/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/'
    elif hostname == 'symmetry':
        if args.report_errors is True:
            print('Recognized host: {}'.format(hostname))
        fig_save_directory = '/Users/grant/Desktop/'
    else:
        sys.exit('Hostname {} is not recognized. Exiting.'.format(
            hostname))

    if args.show_in_gui is False:
        # Then we're on a headless machine and you should use agg
        backend = 'agg'
    elif args.show_in_gui is True:
        backend = 'MacOSX'
    matplotlib.use(backend, force=True)

    from matplotlib import gridspec
    import matplotlib.dates as mdate
    import matplotlib.pyplot as plt
    if args.report_errors is True:
        print("Using Matplotlib backend:", matplotlib.get_backend())

    # Initial settings
    recently_in_comm = False
    in_comm_counter = 0
    out_of_comm_refresh_counter = 0
    iteration_counter = 0

    # Loop infinitely :)
    while True:

        try:

            in_comm = are_we_in_comm(
                verbose=False, cadence=2, fake_comm=fake_comm)

            # Generate the first comm status stamp and create code start date
            if iteration_counter == 0:
                code_start_time = dt.datetime.now()
                comm_status_stamp(comm_status=in_comm, fig_save_directory=fig_save_directory,
                                  code_start_time=code_start_time, hostname=hostname)

            if not in_comm:

                if recently_in_comm:
                    # Then update the text stamp
                    comm_status_stamp(comm_status=in_comm, code_start_time=code_start_time,
                                      fig_save_directory=fig_save_directory, hostname=hostname)

                    make_ancillary_plots(
                        iteration_counter, fig_save_directory)

                    plt.close('all')

                recently_in_comm = False
                in_comm_counter = 0
                out_of_comm_refresh_counter += 1
                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) Not in Comm.                                 ', end='\r\r\r')

                if out_of_comm_refresh_counter == 20:
                    # Refresh the plots every 20th iteration out-of-comm
                    print("Performing out-of-comm plot refresh at {}".format(
                        dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), flush=True)
                    sys.stdout.write("\033[K")
                    five_days_ago = dt.date.today() - dt.timedelta(days=5)
                    two_days_hence = dt.date.today() + dt.timedelta(days=2)

                    make_realtime_plot(plot_start=five_days_ago, fig_save_directory=fig_save_directory,
                                       plot_stop=two_days_hence, sampling='full', date_format=mdate.DateFormatter('%m-%d'), force_limits=True, show_in_gui=args.show_in_gui)

                    make_ancillary_plots(fig_save_directory=fig_save_directory)
                    plt.close('all')

                    # Reset the refresh counter
                    out_of_comm_refresh_counter = 0

            if in_comm:

                recently_in_comm = True
                in_comm_counter += 1

                if in_comm_counter == 1:
                    # Then update the text stamp
                    comm_status_stamp(comm_status=in_comm, code_start_time=code_start_time,
                                      fig_save_directory=fig_save_directory, hostname=hostname)

                if in_comm_counter == 5:
                    # Then create the mission-wide status plots
                    print("Refreshing longviews (Iteration {}) at {}".format(
                        iteration_counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), flush=True)
                    make_ancillary_plots(
                        iteration_counter, fig_save_directory)
                    plt.close('all')

                # Explicitly set maude each time, because ancillary plots use CXC
                fetch.data_source.set('maude allow_subset=False')
                if args.force_ska:
                    fetch.data_source.set('cxc')

                print("Refreshing dashboard (Iteration {}) at {}".format(
                    iteration_counter, dt.datetime.now().strftime("%Y-%b-%d %H:%M:%S")), flush=True)

                five_days_ago = dt.date.today() - dt.timedelta(days=5)
                two_days_hence = dt.date.today() + dt.timedelta(days=2)

                make_realtime_plot(plot_start=five_days_ago, fig_save_directory=fig_save_directory,
                                   plot_stop=two_days_hence, sampling='full', date_format=mdate.DateFormatter('%m-%d'), force_limits=True, show_in_gui=args.show_in_gui)

                print('Saved Current Status Plots to {}'.format(
                    fig_save_directory), end="\r", flush=True)
                # Clear the command line manually
                sys.stdout.write("\033[K")

                plt.close('all')

                sleep_period_seconds = 3

                for i in range(0, sleep_period_seconds):
                    # you need to flush this print statement
                    print('Refreshing plots in {} seconds...'.format(
                        sleep_period_seconds-i), end="\r", flush=True)
                    time.sleep(1)  # sleep for 1 second per iteration

            iteration_counter += 1

        except Exception as e:
            if args.report_errors is True:
                print("ERROR on Iteration {}: {}".format(iteration_counter, e))
                print("Heres the traceback:")
                print(traceback.format_exc())
                print("Pressing on...")
            elif args.report_errors is False:
                print(
                    f'({CxoTime.now().strftime("%m/%d/%Y %H:%M:%S")}) ERROR encountered! Use --report_errors to display them.                              ', end='\r\r\r')
            continue


if __name__ == "__main__":
    main()
