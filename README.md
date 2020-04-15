# Cloud Optimized Fits


## Create Cloud Index

```
$ PYTHONPATH='.' python cloud_fits/fits-index.py -f data/data-cube -b dispatch-bucket
```

## Load a binary table from s3

```
from astropy.table import Table
from cloudfits import bucket_operations

BUCKET_NAME:str = 'dispatch-bucket'

fits_index = bucket_operations.download_index(BUCKET_NAME)
cutout: Astropy_Table = fits_index.headers[2][0: 10]
print(cutout)
```
