#!/usr/bin/env python

import argparse
import enum
import logging
import os
import sys
import typing

import numpy as np

from cloud_fits import exceptions, data_types, local_index, bucket_operations

class ScanMode(enum.Enum):
    Local: str = 'local'
    AWSBucket: str = 'aws-bucket'

logger = logging.getLogger(__name__)

PWN: typing.TypeVar = typing.TypeVar('PWN')

def capture_options() -> argparse.Namespace:
    options = argparse.ArgumentParser()
    options.add_argument('-f', '--fits-files-directory', type=str, required=True)
    options.add_argument('-i', '--index-bucket-name', type=str, required=True, help="""
Sometimes the bucket you're trying to index is publically hosted and doesn't provide write access.
Use --index-bucket-name to designate where to write the Cloud Fits Index to
""")
    options.add_argument('-d', '--data-bucket-path', type=str, required=True, help="""
Full s3://<bucket-name>/<data>/<path> to the contents
""")
    options.add_argument('-m', '--mode', type=ScanMode, default=ScanMode.Local, help="""
Scan an s3 bucket, local directory, or another resource to generate the Cloud Fits Index 
""")

    return options.parse_args()

def _validate_options(options: argparse.Namespace) -> None:
    if not options.data_bucket_path.startswith('s3://'):
        raise NotImplementedError('BucketPath input is not valid s3 path.')

def run_fits_index() -> None:
    options: argparse.Namespace = capture_options()
    _validate_options(options)
    cloud_indices: typing.List[data_types.FitsFileCloudIndex] = []
    if options.mode is ScanMode.Local:
        for relative_path, fits_filepath in local_index.scan_for_all_fits_files(options):
            logger.info(f'Scanning File[{fits_filepath}]')
            cloud_indices.append(local_index.build_fits_cloud_index(relative_path, fits_filepath))
            logger.warn(f"Write logic that'll validate the size of the two files[local|remote] to be the same.")
    else:
        raise NotImplementedError

    bucket_operations.upload_index(options, cloud_indices)

def run_from_cli() -> None:
    sys.path.append(os.getcwd())
    options = capture_options()
    run_fits_index()

if __name__ == '__main__':
    run_from_cli()

