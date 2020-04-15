import argparse
import logging
import os
import tempfile
import requests
import typing
import yaml

from cloud_fits import data_types
from cloud_fits.auth import aws as aws_auth

AWS_REGION: str = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
ENCODING: str = 'utf-8'
INDEX_KEY: str = 'cloud-fits.yaml'
logger = logging.getLogger(__name__)


def upload_index(options: argparse.Namespace, cloud_indices: typing.List[data_types.FitsFileIndex]) -> None:
    index_filepath: str = tempfile.NamedTemporaryFile().name
    configuration: typing.Dict[str, typing.Any] = {
        'version': '0.1.0',
        'aws-default-region': AWS_REGION,
        'indicies': [],
        'index-bucket-name': options.index_bucket_name,
        'data-bucket-path': options.data_bucket_path,
    }
    for cloud_index in cloud_indices:
        configuration['indicies'].append(cloud_index.index)

    logger.info(f'Writing Index to Filepath[{index_filepath}]')
    with open(index_filepath, 'w', encoding=ENCODING) as stream:
        stream.write(yaml.dump(configuration, indent=4, canonical=False))

    logger.info(f'Updating Cloud Index in AWS Bucket[{options.index_bucket_name}]')
    url: str = f'https://s3.{AWS_REGION}.amazonaws.com/{options.index_bucket_name}/{INDEX_KEY}'
    with open(index_filepath, 'r') as stream:
        response = requests.put(url, data=stream.read(), auth=aws_auth.AWSAuth())
        if response.status_code != 200:
            raise NotImplementedError

def download_index(bucket_name: str) -> data_types.FitsCloudIndex:
    index_filepath: str = tempfile.NamedTemporaryFile().name
    logger.info(f'Downloading Cloud Index from AWS Bucket[{bucket_name}]')
    url: str = f'https://s3.{AWS_REGION}.amazonaws.com/{bucket_name}/{INDEX_KEY}'
    response = requests.get(url, auth=aws_auth.AWSAuth())
    if response.status_code != 200:
        raise NotImplementedError

    return data_types.FitsCloudIndex(yaml.load(response.content.decode(ENCODING)))
