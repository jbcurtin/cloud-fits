def test_generate_ranges():
    api_aligned_cViews = [slice(0, 250), slice(0, 250), slice(0, 1), slice(0, 1)]

    # New
    print('Building new Ranges')
    ranges_make = []
    def _generate_ranges(cView: slice, cViews: typing.List[slice], ranges: typing.List[typing.Any], strides: typing.Tuple[int], index_strides: typing.List[int] = []) -> None:
        for idx in range(cView.start, cView.stop, cView.step or 1):
            idx_stride = idx * strides[-1]
            try:
                next_cView = cViews[-1]
                next_cViews = cViews[:-1]
                next_strides = strides[:-1]
            except IndexError:
                _range = sum(index_strides) + idx_stride
                ranges.append(_range)

            else:
                index_strides.append(idx_stride)
                _generate_ranges(next_cView, next_cViews, ranges, next_strides, index_strides)
                index_strides = index_strides[:-1]

    _generate_ranges(api_aligned_cViews[-2], api_aligned_cViews[:-2], ranges_make, self.data_strides[:-1], [])
    ranges_new = [
        [
            self.data_offset + _range + api_aligned_cViews[-1].start * self.data_strides[-1],
            self.data_offset + _range + api_aligned_cViews[-1].stop * self.data_strides[-1] - 1,
        ] for _range in ranges_make]

    # Old
    print('Building old Ranges')
    start, end = api_aligned_cViews[3].start, api_aligned_cViews[3].stop
    i_stride_1 = start * self.data_strides[3]
    i_stride_2 = end * self.data_strides[3]
    ranges = []
    for j in range(
        api_aligned_cViews[2].start,
        api_aligned_cViews[2].stop,
        api_aligned_cViews[2].step or 1):
        j_stride = j * self.data_strides[2]

        for k in range(
            api_aligned_cViews[1].start,
            api_aligned_cViews[1].stop,
            api_aligned_cViews[1].step or 1):
            k_stride = k * self.data_strides[1]

            for m in range(
                api_aligned_cViews[0].start,
                api_aligned_cViews[0].stop,
                api_aligned_cViews[0].step or 1):
                m_stride = m * self.data_strides[0]

                range_start = self.data_offset + i_stride_1 + j_stride + k_stride + m_stride
                range_end = self.data_offset + i_stride_2 + j_stride + k_stride + m_stride - 1
                ranges.append([range_start, range_end])

    for idx, _range in enumerate(ranges):
        assert _range[0] == ranges_new[idx][0], f'\nOld[{_range[0]}], \nNew[{ranges_new[idx][0]}], \nIDX[{idx}], \nDiff[{_range[0] - ranges_new[idx][0]}]'
        assert _range[1] == ranges_new[idx][1], f'\nOld[{_range[1]}], \nNew[{ranges_new[idx][1]}], \nIDX[{idx}], \nDiff[{_range[1] - ranges_new[idx][1]}]'


# Used to test the cutout, by making a real cutout image

# cube_filepath: str = 'data/data-cube/tess-s0001-1-1-cube.fits'
# datas = []
# with open(cube_filepath, 'rb') as stream:
#     for idx, _range in enumerate(ranges):
#         stream.seek(_range[0])
#         datas.append(stream.read(_range[1] - _range[0] + 1))

# data_arr = np.frombuffer(b''.join(datas), dtype='>f4').reshape(250, 250, 1, 1)[:, :, 0, 0]
# cutout = _create_hdu_list()
# cutout[1].data = data_arr
# cutout_name = '/tmp/test.fits'
# os.remove(cutout_name)
# cutout.writeto(cutout_name)

# import pdb; pdb.set_trace()
# import sys; sys.exit(1)

