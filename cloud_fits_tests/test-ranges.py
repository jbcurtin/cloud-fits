#!/usr/bin/env python

import typing

import numpy as np

from cloud_fits.data_types import utils, shortcuts

nViews: typing.List[slice] = [
  slice(0, 250, 1),
  slice(0, 250, 1),
  slice(50, 51, 1),
  slice(0, 2, 1)
]
shape: typing.Tuple[int] = (2078, 2136, 1282, 2)
offset: int = 0
strides: typing.List[int] = (21906816, 10256, 8, 4)
ranges = utils.image__generate_ranges(nViews, strides, offset, 0)

consolidated_ranges = []
for idx, _range in enumerate(ranges):
    if idx == 0:
        consolidated_ranges.append(_range)
        continue

    elif _range[0] == consolidated_ranges[-1][1]:
        consolidated_ranges[-1][1] = _range[0]

    else:
        consolidated_ranges.append(_range)

for idx, _range in enumerate(consolidated_ranges):
    if idx == 0:
        continue

    print('Current Range:', _range)
    print('Range Space:', _range[0] - consolidated_ranges[idx - 1][1])

