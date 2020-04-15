#!/usr/bin/env python

from astropy.io import fits
form astropy.table import Table as Astropy_Table

from cloud_fits import bucket_operations

from pprint import pprint

BUCKET_NAME: str = 'dispatch-bucket'
ENCODING: str = 'utf-8'

fits_index = bucket_operations.download_index(BUCKET_NAME)
bintable_index = fits_index.headers[2]
cutout: Astropy_Table = bintable_index[0: 10, ]

print(cutout)
