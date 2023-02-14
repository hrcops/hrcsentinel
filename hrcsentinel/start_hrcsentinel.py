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
import argparse


def parse_args():

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--iterm', action='store_true')

    args = argparser.parse_args()

    return args


scripts_to_run = ['monitor_comms.py', 'monitor_telemetry.py']
terminal_window_titles = ['Comm Pass Monitor | HRCSentinel',
                          'Telemetry Monitor | HRCSentinel']

HRCSENTINEL_DIRECTORY_HEAD = '/home/tremblay/HRCOps/hrcsentinel/hrcsentinel'
SKAINIT_STRING = 'source /proj/sot/ska3/flight/bin/ska_envs.sh'

args = parse_args()

if os.path.exists(HRCSENTINEL_DIRECTORY_HEAD):

    print('Starting HRCSentinel using the HEAD LAN...')
    for title, script in zip(terminal_window_titles, scripts_to_run):
        print(f'Launching {script} in a new terminal window...')
        os.system(
            f'gnome-terminal --title "{title}" -- bash -c "{SKAINIT_STRING}; cd {HRCSENTINEL_DIRECTORY_HEAD}; python {script}"')

elif sys.platform == 'darwin':
    # then you are on macOS and presumably on a self-managed machine
    # See if you're on one of Grant's machines, which will have iTerm2 (and its python package) installed

    if args.iterm is True:

        import iterm2
        print('Starting HRCSentinel using iTerm2...')

        async def iterm_main(connection, scripts_to_run=scripts_to_run, terminal_window_titles=terminal_window_titles):
            '''
            The first argument is a connection that holds the
            link to a running iTerm2 process. This function gets called only after
            a connection is established. If the connection terminates
            (e.g., if you quit iTerm2) then any attempt to use it will
            raise an exception and terminate your script.
            '''
            app = await iterm2.async_get_app(connection)
            await app.async_activate()
            # window = app.current_terminal_window

            for title, script in zip(terminal_window_titles[0], scripts_to_run[0]):
                await iterm2.Window.async_create(connection, command=f"cd /Users/tremblay/HRCOps/hrcsentinel/hrcsentinel; skainit")
                window = app.current_terminal_window

                if window is not None:
                    session = app.current_terminal_window.current_tab.current_session

                # await session.async_send_text(f'python {script}\n')

                # await session.async_split_pane(vertical=True)
                # session = app.current_terminal_window.current_tab.current_session
                # await session.async_send_text('skainit\n')
                # await session.async_send_text(f'python {script}\n')

        iterm2.run_until_complete(iterm_main)

    elif args.iterm is False:
        for title, script in zip(terminal_window_titles, scripts_to_run):
            os.system(
                f"osascript -e 'tell app \"Terminal\" to do script \"skainit && cd /Users/grant/HRCOps/hrcsentinel/hrcsentinel && clear  && python {script}\"'")
