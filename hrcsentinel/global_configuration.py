import os
import socket
from heartbeat import timestamp_string

allowed_hosts = {'han-v': '/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/',
                 'entropy': '/proj/web-icxc/htdocs/hrcops/hrcmonitor/plots/',
                 'hrccdp1': '/home/hrc/HRCSentinel/staging_area/',
                 'gravity': '/Users/grant/Desktop/',
                 'gravity-2': '/Users/grant/Desktop/',
                 'symmetry': '/Users/grant/Desktop/',
                 'semaphore': '/Users/grant/Desktop/'}


def determine_fig_save_directory():
    hostname = socket.gethostname().split('.')[0]

    if hostname in allowed_hosts:
        fig_save_directory = allowed_hosts[hostname]
    else:
        # then just revert to the desktop
        print(
            f'({timestamp_string()}) Unrecognized host: {hostname}. Plots will be saved to {fig_save_directory}')
        fig_save_directory = os.path.join(
            os.path.join(os.path.expanduser('~')), 'Desktop')

    return fig_save_directory
