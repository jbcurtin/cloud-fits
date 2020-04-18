import collections
import enum
import logging
import os
import requests
import tempfile
import typing

import numpy as np

from astropy.io import fits
from astropy.table import Table as Astropy_Table

from cloud_fits import exceptions
from cloud_fits.auth import aws as aws_auth

PWN: typing.TypeVar = typing.TypeVar('PWN')
logger = logging.getLogger(__name__)

FitsCloudIndexContext = collections.namedtuple('FitsCloudIndexContext', [
    'region', 'version', 'bucket_name', 'data_bucket_path'])

class ExtensionType(enum.Enum):
    BinTable: str = 'bintable'
    Image: str = 'image'
    Primary: str = 'primary'

class FitsCloudIndexHeader:
    def __init__(self: PWN,
        header: typing.Dict[str, typing.Any],
        primary_header: typing.Dict[str, typing.Any],
        cloudpath: str,
        context: FitsCloudIndexContext) -> None:

        self._context = context
        self._header = header
        self._primary_header = primary_header
        self._cloudpath = cloudpath

        for header_name in ['SIMPLE', 'XTENSION']:
            value: str = self.fits.get(header_name, None)
            if value is True:
                self.type = ExtensionType.Primary

            elif value:
                for member_name, member_value in ExtensionType.__members__.items():
                    if value.lower() == member_value.value.lower():
                        self.type = member_value
                        break

        if getattr(self, 'type', None) is None:
            raise NotImplementedError

    def _slice_bintable(self: PWN, nViews: typing.List[slice]) -> Astropy_Table:
        def __validate_bintable_fits_format(header: fits.Header) -> None:
            # https://github.com/astropy/astropy/blob/master/astropy/io/fits/hdu/table.py#L548
            # Implemented the validators that are aligned with the FITS Spec
            # http://articles.adsabs.harvard.edu/pdf/1995A%26AS..113..159C
            assert header['NAXIS'] == 2
            assert header['BITPIX'] == 8
            assert header['TFIELDS'] > 0 and header['TFIELDS'] < 1000
            for idx in range(1, header['TFIELDS'] + 1):
                t_form: str = header.get(f'TFORM{idx}', None)
                assert not t_form is None
                t_type: str = header.get(f'TTYPE{idx}', None)
                assert not t_type is None

            else:
                if idx > 999:
                    raise NotImplementedError(f'Invalid FITS Format')

        def __validate_bintable_python_inputs(header: fits.Header, nViews: typing.List[slice]) -> None:
            assert len(nViews) == 1

        __validate_bintable_fits_format(self.fits)
        __validate_bintable_python_inputs(self.fits, nViews)
        path: str = f'{self._context.data_bucket_path[5:].strip("/")}/{self._cloudpath}'
        url: str = f'https://s3.{self._context.region}.amazonaws.com/{path}'

        # NAXIS1 = number of bytes per row
        # NAXIS2 = number of rows in the table
        start: int = nViews[0].start * self.fits['NAXIS1'] + self.data_offset
        stop: int = nViews[0].stop * self.fits['NAXIS1'] + self.data_offset
        response = requests.get(url, headers={
            'Range': f'bytes={start}-{stop}',
        }, auth=aws_auth.AWSAuth(True), stream=True)
        cutout_name: str = tempfile.NamedTemporaryFile().name
        with open(cutout_name, 'wb') as stream:
            stream.write(self._primary_header['header']['whole'])
            new_header: fits.Header = self.fits
            new_header['NAXIS2'] = nViews[0].stop - nViews[0].start
            stream.write(new_header.tostring().encode('ascii'))
            for chunk in response.iter_content(1024):
                stream.write(chunk)

        return Astropy_Table(fits.open(cutout_name)[1].data)

    def __getitem__(self: PWN, nViews: typing.Union[slice, typing.Tuple[slice]]) -> typing.Any:
        if isinstance(nViews, tuple):
            nViews = list(nViews)

        elif isinstance(nViews, slice):
            nViews = [nViews]

        else:
            raise NotImplementedError

        if self.type == ExtensionType.BinTable:
            return self._slice_bintable(nViews)

        raise NotImplementedError(f'Fits Datatype[{header.type}] Not supported yet')

    def __getattr__(self: PWN, name: str) -> typing.Any:
        if name.startswith('data_'):
            return self._header['data'][name[5:]]

        elif name.startswith('header_'):
            return self._header['header'][name[7:]]

        return super(FitsCloudIndexHeader, self).__getattr__(name)

    @property
    def fits(self: PWN) -> fits.Header:
        return fits.Header.fromstring(self._header['header']['whole'])

    def __repr__(self: PWN) -> str:
        return f'FitsCloudIndexHeader: {self.type.name}'

class FitsCloudIndex:
    def __init__(self: PWN, configuration: typing.Dict[str, typing.Any]) -> None:
        self._context = FitsCloudIndexContext(
            os.environ.get('AWS_DEFAULT_REGION', configuration['aws-default-region']),
            configuration['version'],
            configuration['index-bucket-name'],
            configuration['data-bucket-path'])
        self._index = configuration['indicies'][0]
        self._primary_header = self._index['headers'][0]

        logger.info(f'Loading FitsCloudIndex Version[{self._context.version}]')
        for idx, header in enumerate(self._index['headers']):
            self._index['headers'][idx] = FitsCloudIndexHeader(header, self._primary_header, self._index['cloudpath'], self._context)

    @property
    def index(self: PWN) -> typing.Any:
        return self._index

    @property
    def headers(self: PWN) -> typing.List[FitsCloudIndexHeader]:
        return self._index['headers']


class FitsFileIndex:
    def __init__(self: PWN, cloudpath: str, filename: str, index_name: str, headers: typing.List[str] = []) -> None:
        self._cloudpath = cloudpath
        self._filename = filename
        self._index_name = index_name
        self._headers = headers

    @property
    def index(self: PWN) -> typing.Dict[str, typing.Any]:
        return {
            'cloudpath': self._cloudpath,
            'filename': self._filename,
            'index_name': self._index_name,
            'headers': [header.index for header in self._headers],
        }

class FitsFileHeader:
    def __init__(self: PWN,
        offset: int, length: int, stop: int,
        data_offset: int, data_length: int, data_stop: int,
        header: bytes) -> None:
        self._offset = offset
        self._length = length
        self._stop = stop
        self._data_offset = data_offset
        self._data_length = data_length
        self._data_stop = data_stop
        self._header = header

    @property
    def index(self: PWN) -> typing.Dict[str, typing.Any]:
        return {
            'header': {
                'offset': self._offset,
                'length': self._length,
                'stop': self._stop,
                'whole': self._header,
            },
            'data': {
                'offset': self._data_offset,
                'length': self._data_length,
                'stop': self._data_stop,
                'shape': self.datum_shape,
                # 'size': self.datum_size,
                'data_type': self.datum_data_type.__name__,
                'strides': self.datum_strides,
                'size': self.datum_size,
            }
        }

    @property
    def as_fits(self: PWN) -> fits.Header:
        return fits.Header.fromstring(self._header)

    @property
    def datum_shape(self: PWN) -> fits.Header:
        header: fits.Header = fits.Header.fromstring(self._header)
        shape = tuple([header[f'NAXIS{idx}'] for idx in range(header['NAXIS'], 0, -1)])
        if shape:
            return shape

        return None

    @property
    def datum_data_type(self: PWN) -> typing.List[str]:
        header: fits.Header = fits.Header.fromstring(self._header)
        if header['BITPIX'] == 8:
            return np.uint8

        elif header['BITPIX'] == 16:
            return np.uint16

        elif header['BITPIX'] == 32:
            return np.uint32

        elif header['BITPIX'] == -32:
            return np.float32

        elif header['BITPIX'] == -64:
            return np.float64

        else:
            raise ValueError(f'BITPIX={header["BITPIX"]} not supported')

    @property
    def datum_size(self: PWN) -> int:
        strides: tuple = self.datum_strides
        if strides is None:
            return 0

        return sum(self.datum_strides)

    @property
    def datum_strides(self: PWN) -> tuple:
        itemsize = np.dtype(self.datum_data_type).itemsize
        if self.datum_shape == None:
            return None

        return tuple([length * itemsize for length in self.datum_shape])


