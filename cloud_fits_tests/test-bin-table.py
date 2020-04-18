#!/usr/bin/env python

from astropy.io import fits

from cloud_fits import bucket_operations

from pprint import pprint

BUCKET_NAME: str = 'dispatch-bucket'
BUCKET_NAME: str = 'tess-fits-cloud-index'
ENCODING: str = 'utf-8'

fits_index = bucket_operations.download_index(BUCKET_NAME)
bintable_index = fits_index.headers[2]
cutout = bintable_index[0: 10, ]

awe = fits.open('data/data-cube/tess-s0001-1-1-cube.fits')
with open('/tmp/hop.txt', 'wb') as stream:
    with open('/tmp/simple.txt', 'rb') as simple_stream:
        stream.write(simple_stream.read())

    with open('/tmp/bin-data.txt', 'rb') as bin_stream:
        stream.write(bin_stream.read())

other = fits.open('/tmp/hop.txt')

image_index = fits_index.headers[1]

import ipdb; ipdb.set_trace()
pass
