#!/usr/bin/env python

import os

hrcsentinel_directory = '/home/tremblay/HRCOps/hrcsentinel/hrcsentinel'
skainit_string = 'source /proj/sot/ska3/flight/bin/ska_envs.sh'

scripts_to_run = ['monitor_comms.py', 'monitor_telemetry.py']
terminal_window_titles = ['Comm Pass Monitor | HRCSentinel',
                          'Telemetry Monitor | HRCSentinel']

for title, script in zip(terminal_window_titles, scripts_to_run):
    print(f'Launching {script} in a new terminal window...')
    os.system(
        f'gnome-terminal --title "{title}" -- bash -c "{skainit_string}; cd {hrcsentinel_directory}; python {script}"')
