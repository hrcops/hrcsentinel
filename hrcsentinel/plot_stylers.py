#!/usr/bin/env python


import matplotlib.pyplot as plt
plt.style.use('ggplot')

# Grab the ggplot colors so you can manually set them


def styleplots():
    plt.style.use('ggplot')
    labelsizes = 8
    # plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['font.size'] = labelsizes

    plt.rcParams['axes.titlesize'] = labelsizes
    plt.rcParams['axes.labelsize'] = labelsizes
    plt.rcParams['xtick.labelsize'] = labelsizes - 2
    plt.rcParams['ytick.labelsize'] = labelsizes - 2


rasterized = True
markersize = 1.8
colortable = plt.rcParams['axes.prop_cycle'].by_key()['color']
red = colortable[0]
blue = colortable[1]
gggray = colortable[3]
yellow = colortable[4]
green = colortable[5]
pink = colortable[6]
purple = colortable[2]
