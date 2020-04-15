import argparse
import os
import types
import typing
import _io

import numpy as np

from astropy.io import fits

from cloud_fits import exceptions, data_types

BLOCK_SIZE: int = 2880
END_CARD: bytes = b'END' + b' ' * 77

def scan_for_all_fits_files(options: argparse.Namespace) -> types.GeneratorType:
    for root, directories, filenames in os.walk(options.fits_files_directory):
        for filename in filenames:
            if filename.endswith('.fits'):
                yield options.fits_files_directory, os.path.join(root, filename)

def _load_header_rest(stream: _io.BufferedReader) -> typing.Tuple[typing.List[str], int]:
    header_parts: typing.List[str] = []
    offset: int = 0
    while True:
        block: bytes = stream.read(BLOCK_SIZE)
        if not block:
            break

        header_parts.append(block)
        if END_CARD in block:
            break

        offset = offset + BLOCK_SIZE

    if not END_CARD in header_parts[-1]:
        raise NotImplementedError(f'Invalid FITS file')

    return header_parts, offset


def build_fits_cloud_index(relative_path: str, fits_filepath: str) -> data_types.FitsFileIndex:
    with open(fits_filepath, 'rb') as stream:
        header_offset: int = None
        header_length: int = None
        data_offset: int = None
        data_lengeth: int = None

        headers: typing.List[data_types.FitsFileHeader] = []
        header_parts: typing.List[str] = []
        offset: int = 0
        previous_header_whole: bytes = None
        previous_header_offset: int = None
        previous_data_offset: int = None
        while True:
            block: bytes = stream.read(BLOCK_SIZE)
            if not block:
                break

            if block.startswith(b'SIMPLE') or block.startswith(b'XTENSION'):
                if previous_header_whole:
                    if offset - len(previous_header_whole) == previous_header_offset:
                        data_length = 0
                        data_offset = 0
                        data_stop = 0

                    else:
                        data_offset = previous_header_offset + len(previous_header_whole)
                        data_length = offset - data_offset + BLOCK_SIZE
                        data_stop = offset + BLOCK_SIZE

                    headers.append(data_types.FitsFileHeader(
                        previous_header_offset,
                        len(previous_header_whole),
                        previous_header_offset + len(previous_header_whole),
                        data_offset,
                        data_length,
                        data_stop,
                        previous_header_whole))

                    header_parts = []
                    previous_header_whole = None
                    previous_header_offset = None
                    previous_data_offset = None

                header_offset = offset
                header_parts.append(block)
                if not b'END' in block:
                    header_rest, header_offset = _load_header_rest(stream)
                    header_parts.extend(header_rest)

                    previous_header_whole = b''.join(header_parts)
                    previous_header_offset = offset


                    offset = offset + header_offset + BLOCK_SIZE
                    continue

                else:
                    previous_header_whole = b''.join(header_parts)
                    previous_header_offset = offset

            else:
                if previous_data_offset is None:
                    previous_data_offset = offset + BLOCK_SIZE

            offset = offset + BLOCK_SIZE

        if not previous_header_whole is None:
            data_offset = previous_header_offset + len(previous_header_whole)
            data_length = offset - data_offset + BLOCK_SIZE
            data_stop = offset + BLOCK_SIZE
            headers.append(data_types.FitsFileHeader(
                previous_data_offset,
                len(previous_header_whole),
                previous_header_offset + len(previous_header_whole),
                data_offset,
                data_length,
                data_stop,
                previous_header_whole))

    fits_filename: str = os.path.basename(fits_filepath)
    index_name: str = fits_filename.split('.', 1)[0]
    cloud_filepath: str = fits_filepath.replace(relative_path, '').strip('/')
    return data_types.FitsFileIndex(cloud_filepath, fits_filename, index_name, headers)
