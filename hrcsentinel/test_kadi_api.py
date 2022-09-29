import urllib.request
import json

from chandratime import convert_to_doy
import datetime as dt


start = plot_start = dt.date.today() - dt.timedelta(days=5)
stop = plot_start = dt.date.today()

with urllib.request.urlopen(f"https://kadi.cfa.harvard.edu/api/ska_api/kadi/events/orbits/filter?start={convert_to_doy(start)}&stop={convert_to_doy(stop)}") as url:
    data = json.load(url)

    print(data)
    print(data[0]['tstop'])


def get_radzones():
    """
    Constuct a list of complete radiation zones using kadi events
    """
    radzones = events.rad_zones.filter(start=cxcDateTime() - 5, stop=None)
    return [(x.start, x.stop) for x in radzones]
