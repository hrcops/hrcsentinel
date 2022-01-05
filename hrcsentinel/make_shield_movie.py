import time
from plot_rates import make_shield_plot

import os
import psutil
process = psutil.Process(os.getpid())


max_time = 259200  # seconds (3 days is 259200 sec)

start_time = time.time()  # remember when we started
i = 0

while (time.time() - start_time) < max_time:
    print(f"Making shield plot number {i+1}...")
    make_shield_plot(
        custom_save_name=f'/Users/grant/Science/temp/shield_{i}', save_dpi=300, figure_size=(18, 8))
    i += 1
    sleep_period_seconds = 2
    time.sleep(sleep_period_seconds)
    print("Pausing for a few minutes...")
    print(f"Current memory use: {process.memory_info().rss}")  # in bytes
