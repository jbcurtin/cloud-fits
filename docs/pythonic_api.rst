Pythonic API
============

Astropy BinTable
----------------

Loading a FITS BinTable from AWS S3 using `cloud-fits`, into Astropy

.. code-block:: python

    from cloud_fits.bucket_operations import download_index
    from cloud_fits.datatypes import FitsCloudIndex

    from pprint import pprint

    BUCKET_NAME: str = 'tess-fits-cloud-index'

    index: FitsCloudIndex = download_index(BUCKET_NAME)
    bintable_index = index.headers[2]
    cutout = bintable_index[0, 10]
    pprint(cutout)


    <Table length=10>
    XTENSION BITPIX NAXIS ... IMAGTYPE     CHECKSUM                       FFI_FILE
      str5   int32  int32 ...   str3        str16                          str44
    -------- ------ ----- ... -------- ---------------- --------------------------------------------
       IMAGE    -32     2 ...      cal 6AUa82RZ69Ra69RW tess2018206192942-s0001-1-1-0120-s_ffic.fits
       IMAGE    -32     2 ...      cal FADjF7AiFAAiF5Ai tess2018206195942-s0001-1-1-0120-s_ffic.fits
       IMAGE    -32     2 ...      cal DAmGF4jDDAjDD3jD tess2018206202942-s0001-1-1-0120-s_ffic.fits
       IMAGE    -32     2 ...      cal 9AQkIANi9ANiGANi tess2018206205942-s0001-1-1-0120-s_ffic.fits
       IMAGE    -32     2 ...      cal 3BKTA9JT4AJTA9JT tess2018206212942-s0001-1-1-0120-s_ffic.fits
       IMAGE    -32     2 ...      cal mJXdoGWZmGWbmGWZ tess2018206215942-s0001-1-1-0120-s_ffic.fits
       IMAGE    -32     2 ...      cal gEA5iD84gDA4gD54 tess2018206222942-s0001-1-1-0120-s_ffic.fits
       IMAGE    -32     2 ...      cal 6ZS38XR06XR06XR0 tess2018206225942-s0001-1-1-0120-s_ffic.fits
       IMAGE    -32     2 ...      cal QlM4QjL3QjL3QjL3 tess2018206232942-s0001-1-1-0120-s_ffic.fits
       IMAGE    -32     2 ...      cal Q6ACR50BQ57BQ57B tess2018206235942-s0001-1-1-0120-s_ffic.fits



Details


..  toctree::
    :maxdepth: 2

