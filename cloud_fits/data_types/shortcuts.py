import base64
import logging
import json
import operator
import requests
import time
import multiprocessing
import typing

import numpy as np

from astropy.io import fits

from cloud_fits.auth import aws as aws_auth
from cloud_fits.data_types import utils

from datetime import datetime

logger = logging.getLogger(__name__)

def test_cutout(filename: str) -> fits.HDUList:
    cutout = utils.create_hdu_list()
    cutout[1].data = fits.open(filename)[1].data[:250, :250, 50, 0]
    return cutout

def local_cutout(filename: str, ranges: typing.List[typing.Tuple[int, int]], shape: typing.Tuple[int], dtype: np.dtype) -> fits.HDUList:
    datas: typing.List[bytes] = []
    with open(filename, 'rb') as stream:
        for (start, stop) in ranges:
            stream.seek(start)
            diff: int = stop - start
            datas.append(stream.read(diff))

    # data_arr = np.frombuffer(b''.join(datas), dtype=dtype).reshape(shape)
    data_arr = np.frombuffer(b''.join(datas), dtype='>f4').reshape(shape)
    cutout = utils.create_hdu_list()
    cutout[1].data = data_arr
    return cutout

def _load_byte_range(process_count, start: int, stop: int, child_conn, url: str):
    max_retry = 0
    while max_retry < 3:
        try:
            response = requests.get(url, headers={
                'Range': f'bytes={start}-{stop}',
                'Accept': 'application/octet-stream'
            }, auth=aws_auth.AWSAuth(True), stream=False)
        except Exception as err:
            time.sleep(.1)

        else:
            if response.status_code == 206:
                child_conn.send([
                    json.dumps([
                        process_count,
                        base64.b64encode(response.content).decode('ascii')
                    ])
                ])
                return None

        max_retry = max_retry + 1
        if max_retry >= 3:
            child_conn.send([
                json.dumps([
                    process_count,
                    base64.b64encode(b'noop').decode('ascii')
                ])
            ])
            return None

def remote_cutout(url: str, ranges: typing.List[typing.Tuple[int, int]], shape: typing.Tuple[int]):
    workers = 250
    processes = []
    process_results = []
    process_count: int = 0
    while len(processes) > 0 or len(ranges) > 0:
        for idx, (parent_conn, proc) in enumerate(processes):
            if proc.is_alive() == False:
                result = json.loads(parent_conn.recv()[0])
                content = base64.b64decode(result[1].encode('ascii'))
                if content == 'noop':
                    process_results.append([result[0], 'noop'])

                else:
                    value = base64.b64decode(result[1].encode('ascii'))
                    if value == 'noop':
                        raise Exception

                    process_results.append([
                        result[0],
                        value,
                    ])

                proc.join()
                processes.pop(idx)

        if len(processes) > 3:
            time.sleep(.1)
            continue

        logger.info(f'Process Count: {len(processes)}')
        logger.info(f'Range Count: {len(ranges)}')
        logger.info(f'Worker Count: {workers}')
        logger.info(f'Result Count: {len(process_results)}')
        for idx in range(0, workers - len(processes)):
            try:
                next_range = ranges.pop(0)
            except IndexError:
                continue

            parent_conn, child_conn = multiprocessing.Pipe()
            proc = multiprocessing.Process(target=_load_byte_range, args=(process_count, next_range[0], next_range[1], child_conn, url))
            proc.daemon = True
            proc.start()
            processes.append([parent_conn, proc])
            process_count = process_count + 1

    datas = [re[1] for re in sorted(process_results, key=operator.itemgetter(0))]
    data_arr = np.frombuffer(b''.join(datas), dtype='>f4').reshape(shape)
    cutout = utils.create_hdu_list()
    cutout[1].data = data_arr
    return cutout

