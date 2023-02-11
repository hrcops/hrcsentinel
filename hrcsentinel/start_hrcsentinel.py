#!/usr/bin/env python

'''
A convenience script to start all components of
HRCSentinel at once, within separate terminal windows.

I'm lazy, so this is only meant to work on the HEAD LAN.

If you're running HRCSentinel on a self-managed mac, just run it
the old fashioned way, i.e.: python monitor_comms.py; python monitor_telemetry.py
'''

import os
import sys

HRCSENTINEL_DIRECTORY = '/home/tremblay/HRCOps/hrcsentinel/hrcsentinel'
SKAINIT_STRING = 'source /proj/sot/ska3/flight/bin/ska_envs.sh'

scripts_to_run = ['monitor_comms.py', 'monitor_telemetry.py']
terminal_window_titles = ['Comm Pass Monitor | HRCSentinel',
                          'Telemetry Monitor | HRCSentinel']


if not os.path.exists(HRCSENTINEL_DIRECTORY):
    print("This script is meant to run from the HEAD LAN. \n If you're running HRCSentinel on a self-managed mac, just run it the old fashioned way, i.e.: \n python monitor_comms.py python monitor_telemetry.py")
else:
    print('Starting HRCSentinel...')
    for title, script in zip(terminal_window_titles, scripts_to_run):
        print(f'Launching {script} in a new terminal window...')
        os.system(
            f'gnome-terminal --title "{title}" -- bash -c "{SKAINIT_STRING}; cd {HRCSENTINEL_DIRECTORY}; python {script}"')
