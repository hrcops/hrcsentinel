#!/usr/bin/env conda run -n ska3 python

'''
Open three gnome terminals, each with a different conda environment.
'''


def open_gnome_terminal(conda_env):
    import subprocess
    subprocess.Popen(['gnome-terminal', '--', 'conda',
                     'run', '-n', conda_env, 'python'])
