import numpy as np
import matplotlib.pyplot as plt

from Ska.tdb import msids
from cheta import fetch

dat = fetch.get_telem(['CCSDSTMF', '2SPINATM', '2IMINATM'],
                      start='2010:001', stop='2020:001', sampling='5min')

hrc_is_selected = dat['CCSDSTMF'].vals == 'FMT1'
hrc_not_selected = np.logical_not(hrc_is_selected)


observing = dat['2IMINATM'].means[hrc_is_selected]
not_observing = dat['2IMINATM'].means[hrc_not_selected]

fig, ax = plt.subplots(figsize=(12, 12))
ax.hist(observing, alpha=0.6,
        label=f'HRC observing ({len(observing)} 5min means 2010-2020)', density=True)
ax.hist(not_observing, alpha=0.6,
        label=f'HRC not observing ({len(not_observing)} 5min means 2010-2020)', density=True)

ax.set_xlabel('HRC-I Detector Temperature')

ax.legend()
plt.show()
