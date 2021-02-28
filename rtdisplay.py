#!/usr/bin/env python

import os
from shutil import copyfile
from astropy.io import fits

import datetime as dt

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


def scpimage(user='gtremblay', server='hrc15.cfa.harvard.edu', imagefile='/d0/hrc/rtcads/src/PSD/i0.fits', destination='/Users/grant/Desktop/'):
    '''
    SCP the image from HRC15 (or whatever server). I have setup an SSH key pair for that machine.
    '''
    os.system(f'scp {user}@{server}:{imagefile} {destination}')
    print(f"Copying latest {imagefile.split('/')[-1]} from {server}")


def main():
    '''
    Copy i0.fits from HRC15, make a difference image, and load it up (or refresh it) in JS9/Voyager
    '''

    iteration = 0

    working_dir = '/Users/grant/Desktop/'
    image = working_dir + 'i0.fits'
    refimage = working_dir + 'i0_ref.fits'

    fig, axs = plt.subplots(1, 2, figsize=(18, 10), sharex=True, sharey=True)

    while True:

        if iteration == 1:
            # Load the image in Vger/JS9 only once
            os.system(f'vger {image} &')

        scpimage(destination=working_dir)
        copyfile(image, refimage)

        imgdata = fits.getdata(image)
        refimgdata = fits.getdata(refimage)

        diffimg = refimgdata - imgdata

        axs[0].imshow(imgdata, origin='lower', cmap='magma')
        axs[1].imshow(diffimg, origin='lower', cmap='magma')

        axs[0].set_title(f'Latest Image (Iteration {iteration})')
        axs[1].set_title('Difference Since Last Frame')

        fig.suptitle(
            f"Last update: {dt.datetime.now().strftime('%H:%M:%S')}", fontsize=12)

        iteration += 1

        os.system('js9 refresh')  # Reresh the image in ds9, preserving regions and view state

        plt.draw()
        plt.pause(5)


if __name__ == '__main__':
    main()
