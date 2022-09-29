#!/usr/bin/env python

import datetime as dt

import matplotlib.pyplot as plt
import matplotlib.dates as mdate

from chandratime import cxctime_to_datetime, convert_to_doy

# GENERAL TIMES

# Use today's date, plus 2 days
today_plus_two_days = dt.date.today() + dt.timedelta(days=2)

# THE FIRST ANOMALY
oneweek_pre_anomaly = dt.datetime(2020, 8, 18, 0)
oneday_pre_anomaly = dt.datetime(2020, 8, 23, 0)

sunday_pass = dt.datetime(2020, 8, 24, 2, 30)
sunday_pass_end = dt.datetime(2020, 8, 24, 3, 27, 34)

morning_pass_time = dt.datetime(2020, 8, 24, 13, 45)
fa6_heater_poweroff = dt.datetime(2020, 8, 24, 14, 38)
hrc_poweroff_date = dt.datetime(2020, 8, 24, 15, 7, 26)
evening_pass_time = dt.datetime(2020, 8, 24, 21, 20)

tuesday_community_brief = dt.datetime(2020, 8, 25, 13, 0)
wednesday_community_brief = dt.datetime(2020, 8, 26, 13, 0)

sideA_reset = dt.datetime(2020, 8, 27, 0, 00)
cap_step_2 = dt.datetime(2020, 8, 27, 0, 13)
cap_step_5 = dt.datetime(2020, 8, 27, 0, 24)
cap_step_8 = dt.datetime(2020, 8, 27, 0, 40)

# The famous 6am pass in which everything looked fine
thursday_early_pass = dt.datetime(2020, 8, 27, 10, 0)
thursday_early_pass_end = dt.datetime(2020, 8, 27, 11, 0)

# I got the time of second anomaly from the first bad frame in the data. That is the Chandra time stamp below.
time_of_second_anomaly = cxctime_to_datetime(714916399.97800004)
time_of_second_shutdown = cxctime_to_datetime(714951463.18)

# B-side swap
time_of_cap_1543 = dt.datetime(2020, 8, 31, 17, 50)
time_of_cap_1545a = dt.datetime(2020, 9, 7, 23, 54)

# B-side anomaly =(
b_side_anomaly_time = dt.datetime(2022, 2, 9, 13, 17, 38)
