Cloud Optimized Fits
====================

`cloud-fits` provides the means to index large FITS files and have them served over HTTP for efficient access. A 
scientist or team can index the FITS file-directory, then upload the file-directory to A Static Cloud Provider. Static
Cloud Providers are Amazon WebServices, Google Cloud, Digital Ocean Spaces, or Microsoft Blob Storage. The FITS Cloud
Index can than be checked into a Github Repository, shared, or uploaded to a Static Cloud Provider

`cloud-fits` returns Astropy Datatypes as much as possible


Lets index a few FITS files and extract Metadata from them
----------------------------------------------------------

Accessing the Data
******************

Registry of Open Data on AWS provides a bucket called `stpubdata`. It contains data uploaded from the `Transiting 
Exoplanet Survey Satellite`_. The type of data files we'll be working with in this tutorial are
about 44GB. It'll cost about $1.05 to download and index one of these 352 files from the Registry. To save time and
money, we'll only download one and index it

.. _`Transiting Exoplanet Survey Satellite`: https://tess.mit.edu


Prerequisite
************

Before we can download data off the Registry. Setup an AWS account and configure your credentials file. Then install
`aws-cli`

* https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/
* https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
* https://pypi.org/project/awscli/


Tutorial
********

Lets create our environment and download one data-file from the Registry


.. code-block:: bash

    $ mkdir -p /tmp/tess-data
    $ cd /tmp/tess-data
    $ aws s3 cp s3://stpubdata/tess/public/mast/ . --recursive --exclude "*" --include "tess-s0022-4-4-cube.fits" --request-payer



With our data downloaded, its time to create a bucket that'll hold our FITS Cloud Index. In some cases, we might not
have write access to the data we're indexing. In this case, we want to generate the index from a public data-set. Then
well store the index in a Static Cloud Provider of our choosing. `cloud-fits` can then provide a Pythonic API
augmenting this abstraction

Lets create a bucket on AWS S3 and upload the index there


.. code-block:: bash

    $ AWS_DEFAULT_REGION=us-east-1 aws s3api create-bucket --bucket tess-fits-cloud-index
    $ pip install cloud-fits -U
    $ cloud-fits-index --index-bucket-name tess-fits-cloud-index --fits-files-directory /tmp/tess-data/ --data-bucket-path s3://stpubdata/tess/public/mast


The arguments `--index-bucket-name` and `--fits-file-directory` are intended to be straight forward with the naming. 
`--data-bucket-path` is used to arugment the file-structure difference between `--fits-file-directory` and `--data-bucket-path`. 
For example, the data-cubes are located in `tess/public/mast`, but this data isn't captured in `--fits-file-directory`. So,
`--data-bucket-path` was introduced to augment the paths used to download sections of the file

Okay, great. We have everything we need. Now lets do some science. Start python and enter the following,

.. code-block:: python

    from cloud_fits.bucket_operations import download_index
    from cloud_fits.datatypes import FitsCloudIndex

    from pprint import pprint

    BUCKET_NAME: str = 'tess-fits-cloud-index'

    index: FitsCloudIndex = download_index(BUCKET_NAME)
    bintable_index = index.headers[2]
    print(bintable_index[0, 10])

Keep in mind, everytime data is accessed from `s3://stpubdata`. You'll be paying Amazon Web Services for access

* https://docs.aws.amazon.com/AmazonS3/latest/dev/RequesterPaysBuckets.html

Feature Map
-----------

* Amazon Web Services S3
* Pythonic API Refinement ( Planned Update )
* Remote Indexing for all Static Cloud Providers ( Planned Support )
* Digital Ocean Spaces ( Planned Support )
* Google Object Storage ( Planned Support )
* Microsoft Azure ( Planned Support )


..  toctree::
    :maxdepth: 1

    pythonic_api
    static_cloud_providers
