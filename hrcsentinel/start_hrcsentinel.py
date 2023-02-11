#!/usr/bin/env python

import os

hrcsentinel_directory = '/home/tremblay/HRCOps/hrcsentinel/hrcsentinel'
skainit_string = 'source /proj/sot/ska3/flight/bin/ska_envs.sh'
script_to_run = 'monitor_comms.py'


os.system(
    f'gnome-terminal -- bash -c "{skainit_string}; cd {hrcsentinel_directory}; python {script_to_run}"')
