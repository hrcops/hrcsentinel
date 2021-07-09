
![HRC Sentinel Logo](misc/hrcsentinel_logo.png)

### HRCSentinel

This code will run either on `han-v@cfa.haarvard.edu`


![Screenshots](misc/screenshots.png)

__This code must be run in a Ska Environment!__


It talks to both `maude` (for real-time telemetry) and the `ska/cheta` arvhive (for long-term monitoring).

I do this on `han-v` by first

`source /proj/sot/ska3/flight/bin/ska_envs.sh`
then,

`python hrcmonitor.py`

You can get help with:

```python
❯ python hrcmonitor.py --help
usage: hrcmonitor.py [-h] [--fake_comm] [--force_ska] [--report_errors] [--show_in_gui]

Monitor the VCDU telemetry stream, and update critical status plots whenever we are in comm.

optional arguments:
  -h, --help       show this help message and exit
  --fake_comm      Trick the code to think it's in comm. Useful for testing.
  --force_ska      Trick the code pull from Ska/CXC instead of MAUDE with a switch to fetch.data_source.set()
  --report_errors  Print MAUDE exceptions (which are common) to the command line
  --show_in_gui    Show plots with plt.show()
```

```python
❯ python commbot.py --help
usage: commbot.py [-h] [--fake_comm] [--report_errors]

Monitor the VCDU telemetry stream, and send a message to the HRC Ops Slack with critical HRC telemetry whenever we are in comm.

optional arguments:
  -h, --help       show this help message and exit
  --fake_comm      Trick the code to think it's in comm. Useful for testing.
  --report_errors  Print MAUDE exceptions (which are common) to the command line
```


### CommBot

