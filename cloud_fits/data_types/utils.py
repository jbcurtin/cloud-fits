import collections
import enum
import functools
import logging
import operator
import os
import requests
import tempfile
import typing

import numpy as np

from astropy.io import fits
from astropy.table import Table as Astropy_Table

from cloud_fits import exceptions
from cloud_fits.auth import aws as aws_auth

BLOCK_SIZE: int = 2880
PWN: typing.TypeVar = typing.TypeVar('PWN')
logger = logging.getLogger(__name__)

FitsCloudIndexContext = collections.namedtuple('FitsCloudIndexContext', [
    'region', 'version', 'bucket_name', 'data_bucket_path'])

class ExtensionType(enum.Enum):
    BinTable: str = 'bintable'
    Image: str = 'image'
    Primary: str = 'primary'

def create_primary_header() -> fits.PrimaryHDU:
    header = fits.Header()
    # Primary Header mandatory keywords
    # https://fits.gsfc.nasa.gov/standard30/fits_standard30aa.pdf
    header['SIMPLE'] = True
    header['BITPIX'] = 8
    header['NAXIS'] = 0
    header['EXTNAME'] = 'Primary '
    header['ORIGIN'] = 'https://cloud-fits.readthedocs.io/'
    header['MESSAGE'] = 'Generated header from cloud-fits'
    return fits.PrimaryHDU(header=header)

def create_image_header() -> fits.ImageHDU:
    header = fits.Header()
    header['XTENSION'] = 'IMAGE'
    header['BITPIX'] = '-32'
    header['NAXIS'] = 2
    header['NAXIS1'] = 2136
    header['NAXIS2'] = 2078
    header['PCOUNT'] = 0
    header['GCOUNT'] = 1
    return fits.ImageHDU(header=header)

def create_hdu_list() -> fits.HDUList():
    hdu_list = fits.HDUList([
        create_primary_header(),
        create_image_header()
    ])
    return hdu_list

def image__find_byte_length_of_data(header: fits.Header, itemsize: np.dtype) -> None:
    # https://ui.adsabs.harvard.edu/abs/1994A%26AS..105...53P/abstract
    B: int = itemsize
    G: int = header['GCOUNT']
    P: int = header['PCOUNT']
    N: typing.List[int] = [header[f'NAXIS{idx}'] for idx in range(1, header['NAXIS'] + 1)]
    S: int = B * G * (P + np.prod(N))
    return S

def image__validate_fits_format(header: fits.Header) -> None:
    # https://docs.astropy.org/en/stable/io/fits/api/images.html
    # Implemented the validators that are aligned with the FITS Spec
    # http://articles.adsabs.harvard.edu/pdf/1994A%26AS..105...53P
    B: int = abs(header['BITPIX'])
    G: int = header['GCOUNT']
    P: int = header['PCOUNT']
    N: typing.List[int] = [header[f'NAXIS{idx}'] for idx in range(1, header['NAXIS'] + 1)]
    assert len(N) > 2
    assert G == 1

def image__validate_python_inputs(nViews: typing.List[typing.Union[slice, int]], shape: typing.Tuple[int]) -> None:
    for idx, nView in enumerate(nViews):
        if isinstance(nView, slice):
            if not nView.start is None:
                assert isinstance(nView.start, int)
                assert nView.start > -1
                assert nView.start <= shape[idx]

            if not nView.stop is None:
                assert isinstance(nView.stop, int)
                assert nView.stop > -1
                assert nView.stop <= shape[idx]

            if not nView.step is None:
                assert isinstance(nView.step, int)
                assert nView.step > 0

        elif isinstance(nView, int):
            assert nView > -1
            assert nView <= shape[idx]

        else:
            raise NotImplementedError

def _image___generate_ranges_visitor(nView: slice, nViews: typing.List[slice], strides: typing.List[int], ranges: typing.List[int], index_strides: typing.List[int]) -> None:
    for idx in range(nView.start, nView.stop, nView.step or 1):
        idx_stride = idx * strides[-1]
        try:
            next_nView = nViews[-1]
            next_nViews = nViews[:-1]
            next_strides = strides[:-1]
        except IndexError:
            _range = sum(index_strides) + idx_stride
            ranges.append(_range)

        else:
            index_strides.append(idx_stride)
            _image___generate_ranges_visitor(next_nView, next_nViews, next_strides, ranges, index_strides)
            index_strides = index_strides[:-1]

def image__generate_ranges(nViews: typing.List[slice], strides: typing.Tuple[int], offset: int = 0, stop_variance: int = 0) -> None:
    ranges: typing.List[int] = []
    _image___generate_ranges_visitor(nViews[-2], nViews[:-2], strides[:-1], ranges, [])
    return [
        [
            offset + _range + nViews[-1].start * strides[-1],
            offset + _range + nViews[-1].stop * strides[-1] + stop_variance,
        ] for _range in ranges]

def image__generate_ranges__validate(nViews: typing.List[slice], strides: typing.Tuple[int], offset: int = 0, stop_variance: int = 0, ranges_new: typing.List[typing.Any] = []) -> None:
    start, end = nViews[3].start, nViews[3].stop
    i_stride_1 = start * strides[3]
    i_stride_2 = end * strides[3]
    ranges = []
    for j in range(
        nViews[2].start,
        nViews[2].stop,
        nViews[2].step or 1):
        j_stride = j * strides[2]

        for k in range(
            nViews[1].start,
            nViews[1].stop,
            nViews[1].step or 1):
            k_stride = k * strides[1]

            for m in range(
                nViews[0].start,
                nViews[0].stop,
                nViews[0].step or 1):
                m_stride = m * strides[0]

                range_start = offset + i_stride_1 + j_stride + k_stride + m_stride
                range_end = offset + i_stride_2 + j_stride + k_stride + m_stride + stop_variance
                ranges.append([range_start, range_end])

    for idx, _range in enumerate(ranges):
        assert _range[0] == ranges_new[idx][0], f'\nOld[{_range[0]}], \nNew[{ranges_new[idx][0]}], \nIDX[{idx}], \nDiff[{_range[0] - ranges_new[idx][0]}]'
        assert _range[1] == ranges_new[idx][1], f'\nOld[{_range[1]}], \nNew[{ranges_new[idx][1]}], \nIDX[{idx}], \nDiff[{_range[1] - ranges_new[idx][1]}]'

    return ranges

def calculate_shape_from_nViews(nViews: typing.List[slice]) -> typing.Tuple[int]:
    shape: typing.List[int] = []
    for nView in nViews:
        shape.append(nView.stop - nView.start)

    return tuple(shape)

def convert_nViews_to_slices(nViews: typing.List[typing.Union[slice, int]], shape: typing.Tuple[int]) -> typing.List[slice]:
    calc_nViews: typing.List[slice] = []
    for idx, nView in enumerate(nViews):
        if isinstance(nView, slice):
            calc_nViews.append(slice(
                nView.start or 0,
                nView.stop or shape[idx],
                nView.step or None))

        elif isinstance(nView, int):
            calc_nViews.append(slice(nView, nView + 1, None))

        else:
            raise NotImplementedError

    return calc_nViews

