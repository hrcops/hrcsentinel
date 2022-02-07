#!/usr/bin/env/python

import time
from datetime import datetime
from chandratime import calc_time_to_next_comm


while True:
    print(
        f'Attempting calculation at {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    response = calc_time_to_next_comm(debug_prints=True)
    print(f'Return value is: {response}')
    time.sleep(120)
    print('Waiting for 2 minutes...')
