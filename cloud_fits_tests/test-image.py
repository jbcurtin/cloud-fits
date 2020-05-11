#!/usr/bin/env python

import os
import tempfile

from astropy.io import fits

from cloud_fits import bucket_operations

from pprint import pprint

import numpy as np

BUCKET_NAME: str = 'dispatch-bucket'
BUCKET_NAME: str = 'tess-fits-cloud-index'
ENCODING: str = 'utf-8'

cube = fits.open('data/data-cube/tess-s0001-1-1-cube.fits')

fits_index = bucket_operations.download_index(BUCKET_NAME)
# bintable_index = fits_index.headers[2]
# cutout = bintable_index[0: 10, ]

# image_index = fits_index.headers[1][:, :, 50, 0]
# image_index = fits_index.headers[1][0:250, 0:250, 50, 0]
# image_index = fits_index.headers[1][0:10, 0:10, 50, 0]
# image_index = fits_index.headers[1][:, :, 50, 0]
# image_index = fits_index.headers[1][:, :, 0, 0]

cutout = fits_index.headers[1][0:250, 0:250, 50, 0]
cutout[1].data = np.transpose(cutout[1].data[:, :, 0, 0])
cutout.writeto('/tmp/out.fits', overwrite=True)
import ipdb; ipdb.set_trace()
pass

