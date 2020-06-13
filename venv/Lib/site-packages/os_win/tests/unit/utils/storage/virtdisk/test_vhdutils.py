#  Copyright 2013 Cloudbase Solutions Srl
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ctypes
import os

import ddt
import mock
import six

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils.storage.virtdisk import vhdutils
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi import wintypes


@ddt.ddt
class VHDUtilsTestCase(test_base.BaseTestCase):
    """Unit tests for the Hyper-V VHDUtils class."""

    _autospec_classes = [
        vhdutils.diskutils.DiskUtils,
        vhdutils.win32utils.Win32Utils,
    ]

    def setUp(self):
        super(VHDUtilsTestCase, self).setUp()
        self._setup_lib_mocks()

        self._fake_vst_struct = self._vdisk_struct.VIRTUAL_STORAGE_TYPE

        self._vhdutils = vhdutils.VHDUtils()

        self._mock_close = self._vhdutils._win32_utils.close_handle
        self._mock_run = self._vhdutils._win32_utils.run_and_check_output
        self._run_args = self._vhdutils._virtdisk_run_args

        self._disk_utils = self._vhdutils._disk_utils

        self.addCleanup(mock.patch.stopall)

    def _setup_lib_mocks(self):
        self._vdisk_struct = mock.Mock()
        self._ctypes = mock.Mock()
        # This is used in order to easily make assertions on the variables
        # passed by reference.
        self._ctypes.byref = lambda x: (x, "byref")
        self._ctypes.c_wchar_p = lambda x: (x, "c_wchar_p")
        self._ctypes.c_ulong = lambda x: (x, "c_ulong")

        self._ctypes_patcher = mock.patch.object(
            vhdutils, 'ctypes', self._ctypes)
        self._ctypes_patcher.start()

        mock.patch.multiple(vhdutils,
                            kernel32=mock.DEFAULT,
                            wintypes=mock.DEFAULT, virtdisk=mock.DEFAULT,
                            vdisk_struct=self._vdisk_struct,
                            create=True).start()

    def _test_run_and_check_output(self, raised_exc=None):
        self._mock_run.side_effect = raised_exc(
            func_name='fake_func_name',
            error_code='fake_error_code',
            error_message='fake_error_message') if raised_exc else None

        if raised_exc:
            self.assertRaises(
                raised_exc,
                self._vhdutils._run_and_check_output,
                mock.sentinel.func,
                mock.sentinel.arg,
                cleanup_handle=mock.sentinel.handle)
        else:
            ret_val = self._vhdutils._run_and_check_output(
                mock.sentinel.func,
                mock.sentinel.arg,
                cleanup_handle=mock.sentinel.handle)
            self.assertEqual(self._mock_run.return_value, ret_val)

        self._mock_run.assert_called_once_with(
            mock.sentinel.func, mock.sentinel.arg, **self._run_args)
        self._mock_close.assert_called_once_with(mock.sentinel.handle)

    def test_run_and_check_output(self):
        self._test_run_and_check_output()

    def test_run_and_check_output_raising_error(self):
        self._test_run_and_check_output(
            raised_exc=exceptions.VHDWin32APIException)

    @mock.patch.object(vhdutils.VHDUtils, '_get_vhd_device_id')
    def test_open(self, mock_get_dev_id):
        fake_vst = self._fake_vst_struct.return_value

        mock_get_dev_id.return_value = mock.sentinel.device_id

        handle = self._vhdutils._open(
            vhd_path=mock.sentinel.vhd_path,
            open_flag=mock.sentinel.open_flag,
            open_access_mask=mock.sentinel.access_mask,
            open_params=mock.sentinel.open_params)

        self.assertEqual(vhdutils.wintypes.HANDLE.return_value, handle)
        self._fake_vst_struct.assert_called_once_with(
            DeviceId=mock.sentinel.device_id,
            VendorId=w_const.VIRTUAL_STORAGE_TYPE_VENDOR_MICROSOFT)

        self._mock_run.assert_called_once_with(
            vhdutils.virtdisk.OpenVirtualDisk,
            self._ctypes.byref(fake_vst),
            self._ctypes.c_wchar_p(mock.sentinel.vhd_path),
            mock.sentinel.access_mask,
            mock.sentinel.open_flag,
            mock.sentinel.open_params,
            self._ctypes.byref(vhdutils.wintypes.HANDLE.return_value),
            **self._run_args)

    def test_close(self):
        self._vhdutils.close(mock.sentinel.handle)
        self._mock_close.assert_called_once_with(
            mock.sentinel.handle)

    @mock.patch.object(vhdutils.VHDUtils, '_get_vhd_device_id')
    def _test_create_vhd(self, mock_get_dev_id, new_vhd_type):
        create_params_struct = (
            self._vdisk_struct.CREATE_VIRTUAL_DISK_PARAMETERS)
        mock_handle = vhdutils.wintypes.HANDLE.return_value

        fake_vst = self._fake_vst_struct.return_value
        fake_create_params = create_params_struct.return_value

        expected_create_vhd_flag = (
            vhdutils.CREATE_VIRTUAL_DISK_FLAGS.get(new_vhd_type, 0))

        self._vhdutils.create_vhd(
            new_vhd_path=mock.sentinel.new_vhd_path,
            new_vhd_type=new_vhd_type,
            src_path=mock.sentinel.src_path,
            max_internal_size=mock.sentinel.max_internal_size,
            parent_path=mock.sentinel.parent_path)

        self._fake_vst_struct.assert_called_once_with(
            DeviceId=mock_get_dev_id.return_value,
            VendorId=w_const.VIRTUAL_STORAGE_TYPE_VENDOR_MICROSOFT)

        self.assertEqual(w_const.CREATE_VIRTUAL_DISK_VERSION_2,
                         fake_create_params.Version)
        self.assertEqual(mock.sentinel.max_internal_size,
                         fake_create_params.Version2.MaximumSize)
        self.assertEqual(mock.sentinel.parent_path,
                         fake_create_params.Version2.ParentPath)
        self.assertEqual(mock.sentinel.src_path,
                         fake_create_params.Version2.SourcePath)
        self.assertEqual(
            vhdutils.VIRTUAL_DISK_DEFAULT_PHYS_SECTOR_SIZE,
            fake_create_params.Version2.PhysicalSectorSizeInBytes)
        self.assertEqual(
            w_const.CREATE_VHD_PARAMS_DEFAULT_BLOCK_SIZE,
            fake_create_params.Version2.BlockSizeInBytes)
        self.assertEqual(
            vhdutils.VIRTUAL_DISK_DEFAULT_SECTOR_SIZE,
            fake_create_params.Version2.SectorSizeInBytes)

        self._mock_run.assert_called_once_with(
            vhdutils.virtdisk.CreateVirtualDisk,
            self._ctypes.byref(fake_vst),
            self._ctypes.c_wchar_p(mock.sentinel.new_vhd_path),
            0,
            None,
            expected_create_vhd_flag,
            0,
            self._ctypes.byref(fake_create_params),
            None,
            self._ctypes.byref(mock_handle),
            **self._run_args)

        self._mock_close.assert_called_once_with(mock_handle)

    def test_create_dynamic_vhd(self):
        self._test_create_vhd(new_vhd_type=constants.VHD_TYPE_DYNAMIC)

    def test_create_fixed_vhd(self):
        self._test_create_vhd(new_vhd_type=constants.VHD_TYPE_FIXED)

    @mock.patch.object(vhdutils.VHDUtils, 'create_vhd')
    def test_create_dynamic_vhd_helper(self, mock_create_vhd):
        self._vhdutils.create_dynamic_vhd(mock.sentinel.path,
                                          mock.sentinel.size)

        mock_create_vhd.assert_called_once_with(
            mock.sentinel.path,
            constants.VHD_TYPE_DYNAMIC,
            max_internal_size=mock.sentinel.size)

    @mock.patch.object(vhdutils.VHDUtils, 'create_vhd')
    def test_create_differencing_vhd_helper(self, mock_create_vhd):
        self._vhdutils.create_differencing_vhd(mock.sentinel.path,
                                               mock.sentinel.parent_path)

        mock_create_vhd.assert_called_once_with(
            mock.sentinel.path,
            constants.VHD_TYPE_DIFFERENCING,
            parent_path=mock.sentinel.parent_path)

    @mock.patch.object(vhdutils.VHDUtils, 'create_vhd')
    def test_convert_vhd(self, mock_create_vhd):
        self._vhdutils.convert_vhd(mock.sentinel.src,
                                   mock.sentinel.dest,
                                   mock.sentinel.vhd_type)

        mock_create_vhd.assert_called_once_with(
            mock.sentinel.dest,
            mock.sentinel.vhd_type,
            src_path=mock.sentinel.src)

    def test_get_vhd_format_found_by_ext(self):
        fake_vhd_path = 'C:\\test.vhd'

        ret_val = self._vhdutils.get_vhd_format(fake_vhd_path)

        self.assertEqual(constants.DISK_FORMAT_VHD, ret_val)

    @mock.patch.object(vhdutils.VHDUtils, '_get_vhd_format_by_signature')
    @mock.patch('os.path.exists')
    def _test_vhd_format_unrecognized_ext(self, mock_exists,
                                          mock_get_vhd_fmt_by_sign,
                                          signature_available=False):
        mock_exists.return_value = True
        fake_vhd_path = 'C:\\test_vhd'
        mock_get_vhd_fmt_by_sign.return_value = (
            constants.DISK_FORMAT_VHD if signature_available else None)

        if signature_available:
            ret_val = self._vhdutils.get_vhd_format(fake_vhd_path)
            self.assertEqual(constants.DISK_FORMAT_VHD, ret_val)
        else:
            self.assertRaises(exceptions.VHDException,
                              self._vhdutils.get_vhd_format,
                              fake_vhd_path)

    def test_get_vhd_format_unrecognised_ext_unavailable_signature(self):
        self._test_vhd_format_unrecognized_ext()

    def test_get_vhd_format_unrecognised_ext_available_signature(self):
        self._test_vhd_format_unrecognized_ext(signature_available=True)

    @mock.patch.object(vhdutils.VHDUtils, 'get_vhd_format')
    def test_get_vhd_device_id(self, mock_get_vhd_fmt):
        mock_get_vhd_fmt.return_value = constants.DISK_FORMAT_VHD

        dev_id = self._vhdutils._get_vhd_device_id(mock.sentinel.vhd_path)

        mock_get_vhd_fmt.assert_called_once_with(mock.sentinel.vhd_path)
        self.assertEqual(w_const.VIRTUAL_STORAGE_TYPE_DEVICE_VHD,
                         dev_id)

    def _mock_open(self, read_data=None, curr_f_pos=0):
        mock_open = mock.mock_open()
        mock.patch.object(vhdutils, 'open', mock_open,
                          create=True).start()

        f = mock_open.return_value
        f.read.side_effect = read_data
        f.tell.return_value = curr_f_pos

        return mock_open

    def test_get_vhd_format_by_sig_vhdx(self):
        read_data = (vhdutils.VHDX_SIGNATURE, )
        self._mock_open(read_data=read_data)

        fmt = self._vhdutils._get_vhd_format_by_signature(
            mock.sentinel.vhd_path)

        self.assertEqual(constants.DISK_FORMAT_VHDX, fmt)

    def test_get_vhd_format_by_sig_vhd(self):
        read_data = ('notthesig', vhdutils.VHD_SIGNATURE)
        mock_open = self._mock_open(read_data=read_data, curr_f_pos=1024)

        fmt = self._vhdutils._get_vhd_format_by_signature(
            mock.sentinel.vhd_path)

        self.assertEqual(constants.DISK_FORMAT_VHD, fmt)
        mock_open.return_value.seek.assert_has_calls([mock.call(0, 2),
                                                      mock.call(-512, 2)])

    def test_get_vhd_format_by_sig_invalid_format(self):
        self._mock_open(read_data='notthesig', curr_f_pos=1024)

        fmt = self._vhdutils._get_vhd_format_by_signature(
            mock.sentinel.vhd_path)

        self.assertIsNone(fmt)

    def test_get_vhd_format_by_sig_zero_length_file(self):
        mock_open = self._mock_open(read_data=('', ''))

        fmt = self._vhdutils._get_vhd_format_by_signature(
            mock.sentinel.vhd_path)

        self.assertIsNone(fmt)
        mock_open.return_value.seek.assert_called_once_with(0, 2)

    @mock.patch.object(vhdutils.VHDUtils, '_open')
    @mock.patch.object(vhdutils.VHDUtils, '_get_vhd_info_member')
    def test_get_vhd_info(self, mock_get_vhd_info_member,
                          mock_open):
        fake_info_member = w_const.GET_VIRTUAL_DISK_INFO_SIZE
        fake_vhd_info = {'VirtualSize': mock.sentinel.virtual_size}

        mock_open.return_value = mock.sentinel.handle
        mock_get_vhd_info_member.return_value = fake_vhd_info

        expected_open_flag = w_const.OPEN_VIRTUAL_DISK_FLAG_NO_PARENTS
        expected_access_mask = (w_const.VIRTUAL_DISK_ACCESS_GET_INFO |
                                w_const.VIRTUAL_DISK_ACCESS_DETACH)

        ret_val = self._vhdutils.get_vhd_info(mock.sentinel.vhd_path,
                                              [fake_info_member])

        self.assertEqual(fake_vhd_info, ret_val)
        mock_open.assert_called_once_with(
            mock.sentinel.vhd_path,
            open_flag=expected_open_flag,
            open_access_mask=expected_access_mask)
        self._vhdutils._get_vhd_info_member.assert_called_once_with(
            mock.sentinel.handle,
            fake_info_member)
        self._mock_close.assert_called_once_with(mock.sentinel.handle)

    @mock.patch.object(vhdutils.VHDUtils, '_parse_vhd_info')
    def test_get_vhd_info_member(self, mock_parse_vhd_info):
        get_vd_info_struct = (
            self._vdisk_struct.GET_VIRTUAL_DISK_INFO)
        fake_params = get_vd_info_struct.return_value
        fake_info_size = self._ctypes.sizeof.return_value

        info_member = w_const.GET_VIRTUAL_DISK_INFO_PARENT_LOCATION

        vhd_info = self._vhdutils._get_vhd_info_member(
            mock.sentinel.vhd_path,
            info_member)

        self._mock_run.assert_called_once_with(
            vhdutils.virtdisk.GetVirtualDiskInformation,
            mock.sentinel.vhd_path,
            self._ctypes.byref(
                self._ctypes.c_ulong(fake_info_size)),
            self._ctypes.byref(fake_params), None,
            ignored_error_codes=[w_const.ERROR_VHD_INVALID_TYPE],
            **self._run_args)

        self.assertEqual(mock_parse_vhd_info.return_value, vhd_info)
        mock_parse_vhd_info.assert_called_once_with(fake_params,
                                                    info_member)

    def test_parse_vhd_info(self):
        fake_info_member = w_const.GET_VIRTUAL_DISK_INFO_SIZE
        fake_info = mock.Mock()
        fake_info.Size._fields_ = [
            ("VirtualSize", vhdutils.wintypes.ULARGE_INTEGER),
            ("PhysicalSize", vhdutils.wintypes.ULARGE_INTEGER)]
        fake_info.Size.VirtualSize = mock.sentinel.virt_size
        fake_info.Size.PhysicalSize = mock.sentinel.phys_size

        ret_val = self._vhdutils._parse_vhd_info(fake_info,
                                                 fake_info_member)
        expected = {'VirtualSize': mock.sentinel.virt_size,
                    'PhysicalSize': mock.sentinel.phys_size}

        self.assertEqual(expected, ret_val)

    def test_parse_vhd_provider_subtype_member(self):
        fake_info_member = w_const.GET_VIRTUAL_DISK_INFO_PROVIDER_SUBTYPE
        fake_info = mock.Mock()
        fake_info.ProviderSubtype = mock.sentinel.provider_subtype

        ret_val = self._vhdutils._parse_vhd_info(fake_info, fake_info_member)
        expected = {'ProviderSubtype': mock.sentinel.provider_subtype}

        self.assertEqual(expected, ret_val)

    @mock.patch.object(vhdutils.VHDUtils, 'get_vhd_info')
    def test_get_vhd_size(self, mock_get_vhd_info):
        ret_val = self._vhdutils.get_vhd_size(mock.sentinel.vhd_path)

        self.assertEqual(mock_get_vhd_info.return_value, ret_val)
        mock_get_vhd_info.assert_called_once_with(
            mock.sentinel.vhd_path,
            [w_const.GET_VIRTUAL_DISK_INFO_SIZE])

    @mock.patch.object(vhdutils.VHDUtils, 'get_vhd_info')
    def test_get_vhd_parent_path(self, mock_get_vhd_info):
        mock_get_vhd_info.return_value = {
            'ParentPath': mock.sentinel.parent_path}

        ret_val = self._vhdutils.get_vhd_parent_path(mock.sentinel.vhd_path)

        self.assertEqual(mock.sentinel.parent_path, ret_val)
        mock_get_vhd_info.assert_called_once_with(
            mock.sentinel.vhd_path,
            [w_const.GET_VIRTUAL_DISK_INFO_PARENT_LOCATION])

    @mock.patch.object(vhdutils.VHDUtils, 'get_vhd_info')
    def test_get_vhd_type(self, mock_get_vhd_info):
        mock_get_vhd_info.return_value = {
            'ProviderSubtype': mock.sentinel.provider_subtype}

        ret_val = self._vhdutils.get_vhd_type(mock.sentinel.vhd_path)

        self.assertEqual(mock.sentinel.provider_subtype, ret_val)
        mock_get_vhd_info.assert_called_once_with(
            mock.sentinel.vhd_path,
            [w_const.GET_VIRTUAL_DISK_INFO_PROVIDER_SUBTYPE])

    @mock.patch.object(vhdutils.VHDUtils, '_open')
    @mock.patch('os.remove')
    def test_merge_vhd(self, mock_remove, mock_open):
        open_params_struct = (
            self._vdisk_struct.OPEN_VIRTUAL_DISK_PARAMETERS)
        merge_params_struct = (
            self._vdisk_struct.MERGE_VIRTUAL_DISK_PARAMETERS)

        fake_open_params = open_params_struct.return_value
        fake_merge_params = merge_params_struct.return_value
        mock_open.return_value = mock.sentinel.handle

        self._vhdutils.merge_vhd(mock.sentinel.vhd_path)

        self.assertEqual(w_const.OPEN_VIRTUAL_DISK_VERSION_1,
                         fake_open_params.Version)
        self.assertEqual(2,
                         fake_open_params.Version1.RWDepth)

        mock_open.assert_called_once_with(
            mock.sentinel.vhd_path,
            open_params=self._ctypes.byref(fake_open_params))

        self.assertEqual(w_const.MERGE_VIRTUAL_DISK_VERSION_1,
                         fake_merge_params.Version)
        self.assertEqual(1,
                         fake_merge_params.Version1.MergeDepth)

        self._mock_run.assert_called_once_with(
            vhdutils.virtdisk.MergeVirtualDisk,
            mock.sentinel.handle,
            0,
            self._ctypes.byref(fake_merge_params),
            None,
            **self._run_args)
        mock_remove.assert_called_once_with(
            mock.sentinel.vhd_path)
        self._mock_close.assert_called_once_with(mock.sentinel.handle)

    @mock.patch.object(vhdutils.VHDUtils, '_open')
    def test_reconnect_parent_vhd(self, mock_open):
        set_vdisk_info_struct = (
            self._vdisk_struct.SET_VIRTUAL_DISK_INFO)
        open_params_struct = (
            self._vdisk_struct.OPEN_VIRTUAL_DISK_PARAMETERS)

        fake_set_params = set_vdisk_info_struct.return_value
        fake_open_params = open_params_struct.return_value
        mock_open.return_value = mock.sentinel.handle

        self._vhdutils.reconnect_parent_vhd(mock.sentinel.vhd_path,
                                            mock.sentinel.parent_path)

        self.assertEqual(w_const.OPEN_VIRTUAL_DISK_VERSION_2,
                         fake_open_params.Version)
        self.assertFalse(fake_open_params.Version2.GetInfoOnly)

        self._vhdutils._open.assert_called_once_with(
            mock.sentinel.vhd_path,
            open_flag=w_const.OPEN_VIRTUAL_DISK_FLAG_NO_PARENTS,
            open_access_mask=0,
            open_params=vhdutils.ctypes.byref(fake_open_params))

        self.assertEqual(w_const.SET_VIRTUAL_DISK_INFO_PARENT_PATH,
                         fake_set_params.Version)
        self.assertEqual(mock.sentinel.parent_path,
                         fake_set_params.ParentFilePath)

        self._mock_run.assert_called_once_with(
            vhdutils.virtdisk.SetVirtualDiskInformation,
            mock.sentinel.handle,
            vhdutils.ctypes.byref(fake_set_params),
            **self._run_args)
        self._mock_close.assert_called_once_with(mock.sentinel.handle)

    @mock.patch.object(vhdutils.VHDUtils, 'get_internal_vhd_size_by_file_size')
    @mock.patch.object(vhdutils.VHDUtils, '_resize_vhd')
    @mock.patch.object(vhdutils.VHDUtils, '_check_resize_needed')
    def _test_resize_vhd(self, mock_check_resize_needed,
                         mock_resize_helper, mock_get_internal_size,
                         is_file_max_size=True, resize_needed=True):
        mock_check_resize_needed.return_value = resize_needed

        self._vhdutils.resize_vhd(mock.sentinel.vhd_path,
                                  mock.sentinel.new_size,
                                  is_file_max_size,
                                  validate_new_size=True)

        if is_file_max_size:
            mock_get_internal_size.assert_called_once_with(
                mock.sentinel.vhd_path, mock.sentinel.new_size)
            expected_new_size = mock_get_internal_size.return_value
        else:
            expected_new_size = mock.sentinel.new_size

        mock_check_resize_needed.assert_called_once_with(
            mock.sentinel.vhd_path, expected_new_size)
        if resize_needed:
            mock_resize_helper.assert_called_once_with(mock.sentinel.vhd_path,
                                                       expected_new_size)
        else:
            self.assertFalse(mock_resize_helper.called)

    def test_resize_vhd_specifying_internal_size(self):
        self._test_resize_vhd(is_file_max_size=False)

    def test_resize_vhd_specifying_file_max_size(self):
        self._test_resize_vhd()

    def test_resize_vhd_already_having_requested_size(self):
        self._test_resize_vhd(resize_needed=False)

    @mock.patch.object(vhdutils.VHDUtils, 'get_vhd_size')
    def _test_check_resize_needed(self, mock_get_vhd_size,
                                  current_size=1, new_size=2):
        mock_get_vhd_size.return_value = dict(VirtualSize=current_size)

        if current_size > new_size:
            self.assertRaises(exceptions.VHDException,
                              self._vhdutils._check_resize_needed,
                              mock.sentinel.vhd_path,
                              new_size)
        else:
            resize_needed = self._vhdutils._check_resize_needed(
                mock.sentinel.vhd_path, new_size)
            self.assertEqual(current_size < new_size, resize_needed)

    def test_check_resize_needed_smaller_new_size(self):
        self._test_check_resize_needed(current_size=2, new_size=1)

    def test_check_resize_needed_bigger_new_size(self):
        self._test_check_resize_needed()

    def test_check_resize_needed_smaller_equal_size(self):
        self._test_check_resize_needed(current_size=1, new_size=1)

    @mock.patch.object(vhdutils.VHDUtils, '_open')
    def test_resize_vhd_helper(self, mock_open):
        resize_vdisk_struct = (
            self._vdisk_struct.RESIZE_VIRTUAL_DISK_PARAMETERS)
        fake_params = resize_vdisk_struct.return_value

        mock_open.return_value = mock.sentinel.handle

        self._vhdutils._resize_vhd(mock.sentinel.vhd_path,
                                   mock.sentinel.new_size)

        self.assertEqual(w_const.RESIZE_VIRTUAL_DISK_VERSION_1,
                         fake_params.Version)
        self.assertEqual(mock.sentinel.new_size,
                         fake_params.Version1.NewSize)

        self._mock_run.assert_called_once_with(
            vhdutils.virtdisk.ResizeVirtualDisk,
            mock.sentinel.handle,
            0,
            vhdutils.ctypes.byref(fake_params),
            None,
            **self._run_args)
        self._mock_close.assert_called_once_with(mock.sentinel.handle)

    @mock.patch.object(vhdutils.VHDUtils, 'get_vhd_info')
    @mock.patch.object(vhdutils.VHDUtils,
                       '_get_internal_vhd_size_by_file_size')
    @mock.patch.object(vhdutils.VHDUtils,
                       '_get_internal_vhdx_size_by_file_size')
    def _test_get_int_sz_by_file_size(
            self, mock_get_vhdx_int_size,
            mock_get_vhd_int_size, mock_get_vhd_info,
            vhd_dev_id=w_const.VIRTUAL_STORAGE_TYPE_DEVICE_VHD,
            vhd_type=constants.VHD_TYPE_DYNAMIC):
        fake_vhd_info = dict(ProviderSubtype=vhd_type,
                             ParentPath=mock.sentinel.parent_path,
                             DeviceId=vhd_dev_id)
        mock_get_vhd_info.side_effect = [fake_vhd_info]
        exppected_vhd_info_calls = [mock.call(mock.sentinel.vhd_path)]
        expected_vhd_checked = mock.sentinel.vhd_path
        expected_checked_vhd_info = fake_vhd_info

        if vhd_type == constants.VHD_TYPE_DIFFERENCING:
            expected_checked_vhd_info = dict(
                fake_vhd_info, vhd_type=constants.VHD_TYPE_DYNAMIC)
            mock_get_vhd_info.side_effect.append(
                expected_checked_vhd_info)
            exppected_vhd_info_calls.append(
                mock.call(mock.sentinel.parent_path))
            expected_vhd_checked = mock.sentinel.parent_path

        is_vhd = vhd_dev_id == w_const.VIRTUAL_STORAGE_TYPE_DEVICE_VHD
        expected_helper = (mock_get_vhd_int_size
                           if is_vhd
                           else mock_get_vhdx_int_size)

        ret_val = self._vhdutils.get_internal_vhd_size_by_file_size(
            mock.sentinel.vhd_path, mock.sentinel.vhd_size)

        mock_get_vhd_info.assert_has_calls(exppected_vhd_info_calls)
        expected_helper.assert_called_once_with(expected_vhd_checked,
                                                mock.sentinel.vhd_size,
                                                expected_checked_vhd_info)
        self.assertEqual(expected_helper.return_value, ret_val)

    def test_get_int_sz_by_file_size_vhd(self):
        self._test_get_int_sz_by_file_size()

    def test_get_int_sz_by_file_size_vhdx(self):
        self._test_get_int_sz_by_file_size(
            vhd_dev_id=w_const.VIRTUAL_STORAGE_TYPE_DEVICE_VHDX)

    def test_get_int_sz_by_file_size_differencing(self):
        self._test_get_int_sz_by_file_size(
            vhd_dev_id=w_const.VIRTUAL_STORAGE_TYPE_DEVICE_VHDX)

    def _mocked_get_internal_vhd_size(self, root_vhd_size, vhd_type):
        fake_vhd_info = dict(ProviderSubtype=vhd_type,
                             BlockSize=2097152,
                             ParentPath=mock.sentinel.parent_path)

        return self._vhdutils._get_internal_vhd_size_by_file_size(
            mock.sentinel.vhd_path, root_vhd_size, fake_vhd_info)

    def test_get_internal_vhd_size_by_file_size_fixed(self):
        root_vhd_size = 1 << 30
        real_size = self._mocked_get_internal_vhd_size(
            root_vhd_size=root_vhd_size,
            vhd_type=constants.VHD_TYPE_FIXED)

        expected_vhd_size = root_vhd_size - 512
        self.assertEqual(expected_vhd_size, real_size)

    def test_get_internal_vhd_size_by_file_size_dynamic(self):
        root_vhd_size = 20 << 30
        real_size = self._mocked_get_internal_vhd_size(
            root_vhd_size=root_vhd_size,
            vhd_type=constants.VHD_TYPE_DYNAMIC)

        expected_md_size = 43008
        expected_vhd_size = root_vhd_size - expected_md_size
        self.assertEqual(expected_vhd_size, real_size)

    @mock.patch.object(vhdutils.VHDUtils, '_get_vhdx_block_size')
    @mock.patch.object(vhdutils.VHDUtils, '_get_vhdx_log_size')
    @mock.patch.object(vhdutils.VHDUtils, '_get_vhdx_metadata_size_and_offset')
    def test_get_vhdx_internal_size(self, mock_get_vhdx_md_sz_and_off,
                                    mock_get_vhdx_log_sz,
                                    mock_get_vhdx_block_size):
        self._mock_open()
        fake_log_sz = 1 << 20
        fake_block_sz = 32 << 20
        fake_md_sz = 1 << 20
        fake_logical_sector_sz = 4096
        new_vhd_sz = 1 << 30
        # We expect less than a block to be reserved for internal metadata.
        expected_max_int_sz = new_vhd_sz - fake_block_sz

        fake_vhd_info = dict(SectorSize=fake_logical_sector_sz)

        mock_get_vhdx_block_size.return_value = fake_block_sz
        mock_get_vhdx_log_sz.return_value = fake_log_sz
        mock_get_vhdx_md_sz_and_off.return_value = fake_md_sz, None

        internal_size = self._vhdutils._get_internal_vhdx_size_by_file_size(
            mock.sentinel.vhd_path, new_vhd_sz, fake_vhd_info)

        self.assertIn(type(internal_size), six.integer_types)
        self.assertEqual(expected_max_int_sz, internal_size)

    def test_get_vhdx_internal_size_exception(self):
        mock_open = self._mock_open()
        mock_open.side_effect = IOError
        func = self._vhdutils._get_internal_vhdx_size_by_file_size
        self.assertRaises(exceptions.VHDException,
                          func,
                          mock.sentinel.vhd_path,
                          mock.sentinel.vhd_size,
                          mock.sentinel.vhd_info)

    def _get_mock_file_handle(self, *args):
        mock_file_handle = mock.Mock()
        mock_file_handle.read.side_effect = args
        return mock_file_handle

    def test_get_vhdx_current_header(self):
        # The current header has the maximum sequence number.
        fake_seq_numbers = [
            bytearray(b'\x01\x00\x00\x00\x00\x00\x00\x00'),
            bytearray(b'\x02\x00\x00\x00\x00\x00\x00\x00')]
        mock_handle = self._get_mock_file_handle(*fake_seq_numbers)

        offset = self._vhdutils._get_vhdx_current_header_offset(mock_handle)

        self.assertEqual(vhdutils.VHDX_HEADER_OFFSETS[1], offset)

    @mock.patch.object(vhdutils.VHDUtils, '_get_vhdx_current_header_offset')
    def test_get_log_size(self, mock_get_vhdx_curr_hd_offset):
        fake_curr_header_offset = vhdutils.VHDX_HEADER_OFFSETS[0]
        fake_log_sz = bytearray(b'\x01\x00\x00\x00')

        mock_get_vhdx_curr_hd_offset.return_value = fake_curr_header_offset
        mock_handle = self._get_mock_file_handle(fake_log_sz)

        log_size = self._vhdutils._get_vhdx_log_size(mock_handle)

        self.assertEqual(log_size, 1)

    def test_get_vhdx_metadata_size(self):
        fake_md_offset = bytearray(b'\x01\x00\x00\x00\x00\x00\x00\x00')
        fake_md_sz = bytearray(b'\x01\x00\x00\x00')

        mock_handle = self._get_mock_file_handle(fake_md_offset,
                                                 fake_md_sz)

        md_sz, md_offset = self._vhdutils._get_vhdx_metadata_size_and_offset(
            mock_handle)

        self.assertEqual(1, md_sz)
        self.assertEqual(1, md_offset)

    @mock.patch.object(vhdutils.VHDUtils,
                       '_get_vhdx_metadata_size_and_offset')
    def test_get_block_size(self, mock_get_md_sz_and_offset):
        mock_get_md_sz_and_offset.return_value = (mock.sentinel.md_sz, 1024)
        fake_block_size = bytearray(b'\x01\x00\x00\x00')
        fake_offset = bytearray(b'\x02\x00\x00\x00')
        mock_handle = self._get_mock_file_handle(fake_offset,
                                                 fake_block_size)

        block_size = self._vhdutils._get_vhdx_block_size(mock_handle)
        self.assertEqual(block_size, 1)

    @mock.patch.object(vhdutils.VHDUtils, 'convert_vhd')
    @mock.patch.object(os, 'unlink')
    @mock.patch.object(os, 'rename')
    def test_flatten_vhd(self, mock_rename, mock_unlink, mock_convert):
        fake_vhd_path = r'C:\test.vhd'
        expected_tmp_path = r'C:\test.tmp.vhd'

        self._vhdutils.flatten_vhd(fake_vhd_path)

        mock_convert.assert_called_once_with(fake_vhd_path, expected_tmp_path)
        mock_unlink.assert_called_once_with(fake_vhd_path)
        mock_rename.assert_called_once_with(expected_tmp_path, fake_vhd_path)

    def test_get_best_supported_vhd_format(self):
        fmt = self._vhdutils.get_best_supported_vhd_format()
        self.assertEqual(constants.DISK_FORMAT_VHDX, fmt)

    @ddt.data({},
              {'read_only': False, 'detach_on_handle_close': True})
    @ddt.unpack
    @mock.patch.object(vhdutils.VHDUtils, '_open')
    def test_attach_virtual_disk(self, mock_open, read_only=True,
                                 detach_on_handle_close=False):
        ret_val = self._vhdutils.attach_virtual_disk(
            mock.sentinel.vhd_path,
            read_only, detach_on_handle_close)

        handle = mock_open.return_value
        self.assertEqual(handle
                         if detach_on_handle_close else None,
                         ret_val)

        exp_access_mask = (w_const.VIRTUAL_DISK_ACCESS_ATTACH_RO
                           if read_only
                           else w_const.VIRTUAL_DISK_ACCESS_ATTACH_RW)
        mock_open.assert_called_once_with(mock.sentinel.vhd_path,
                                          open_access_mask=exp_access_mask)

        self._mock_run.assert_called_once_with(
            vhdutils.virtdisk.AttachVirtualDisk,
            handle,
            None,
            mock.ANY,
            0, None, None,
            **self._run_args)

        if not detach_on_handle_close:
            self._mock_close.assert_called_once_with(handle)
        else:
            self._mock_close.assert_not_called()

        mock_run_args = self._mock_run.call_args_list[0][0]
        attach_flag = mock_run_args[3]

        self.assertEqual(
            read_only,
            bool(attach_flag & w_const.ATTACH_VIRTUAL_DISK_FLAG_READ_ONLY))
        self.assertEqual(
            not detach_on_handle_close,
            bool(attach_flag &
                 w_const.ATTACH_VIRTUAL_DISK_FLAG_PERMANENT_LIFETIME))

    @ddt.data(True, False)
    @mock.patch('os.path.exists')
    @mock.patch.object(vhdutils.VHDUtils, '_open')
    def test_detach_virtual_disk(self, exists, mock_open, mock_exists):
        mock_exists.return_value = exists
        self._mock_run.return_value = w_const.ERROR_NOT_READY

        self._vhdutils.detach_virtual_disk(mock.sentinel.vhd_path)

        mock_exists.assert_called_once_with(mock.sentinel.vhd_path)
        if exists:
            mock_open.assert_called_once_with(
                mock.sentinel.vhd_path,
                open_access_mask=w_const.VIRTUAL_DISK_ACCESS_DETACH)

            self._mock_run.assert_called_once_with(
                vhdutils.virtdisk.DetachVirtualDisk,
                mock_open.return_value,
                0, 0,
                ignored_error_codes=[w_const.ERROR_NOT_READY],
                **self._run_args)
            self._mock_close.assert_called_once_with(mock_open.return_value)
        else:
            mock_open.assert_not_called()

    @ddt.data(True, False)
    @mock.patch('os.path.exists')
    @mock.patch.object(vhdutils.VHDUtils, '_open')
    @mock.patch.object(vhdutils.VHDUtils, 'is_virtual_disk_file_attached')
    def test_detach_virtual_disk_exc(self, is_attached, mock_is_attached,
                                     mock_open, mock_exists):
        # We'll try another approach before erroring out if the image cannot
        # be opened (e.g. attached on a different host).
        mock_exists.return_value = True
        mock_is_attached.return_value = is_attached
        mock_open.side_effect = exceptions.Win32Exception(message='fake exc')

        if is_attached:
            self.assertRaises(exceptions.Win32Exception,
                              self._vhdutils.detach_virtual_disk,
                              mock.sentinel.vhd_path)
        else:
            self._vhdutils.detach_virtual_disk(mock.sentinel.vhd_path)

        mock_is_attached.assert_called_once_with(mock.sentinel.vhd_path)

    @mock.patch.object(vhdutils.VHDUtils, '_open')
    def test_get_virtual_disk_physical_path(self, mock_open):
        self._ctypes_patcher.stop()
        vhdutils.wintypes = wintypes

        fake_drive_path = r'\\.\PhysicialDrive5'

        def fake_run(func, handle, disk_path_sz_p, disk_path, **kwargs):
            disk_path_sz = ctypes.cast(
                disk_path_sz_p, wintypes.PULONG).contents.value
            self.assertEqual(w_const.MAX_PATH, disk_path_sz)

            disk_path.value = fake_drive_path

        self._mock_run.side_effect = fake_run

        ret_val = self._vhdutils.get_virtual_disk_physical_path(
            mock.sentinel.vhd_path)

        self.assertEqual(fake_drive_path, ret_val)
        mock_open.assert_called_once_with(
            mock.sentinel.vhd_path,
            open_flag=w_const.OPEN_VIRTUAL_DISK_FLAG_NO_PARENTS,
            open_access_mask=(w_const.VIRTUAL_DISK_ACCESS_GET_INFO |
                              w_const.VIRTUAL_DISK_ACCESS_DETACH))

        self._mock_run.assert_called_once_with(
            vhdutils.virtdisk.GetVirtualDiskPhysicalPath,
            mock_open.return_value,
            mock.ANY,
            mock.ANY,
            **self._run_args)

    @ddt.data({},
              {'exists': False},
              {'open_fails': True})
    @ddt.unpack
    @mock.patch('os.path.exists')
    @mock.patch.object(vhdutils.VHDUtils, 'get_vhd_info')
    def test_is_virtual_disk_file_attached(self, mock_get_vhd_info,
                                           mock_exists,
                                           exists=True, open_fails=False):
        mock_exists.return_value = exists
        if open_fails:
            mock_get_vhd_info.side_effect = exceptions.Win32Exception(
                message="fake exc")
        else:
            mock_get_vhd_info.return_value = {
                'IsLoaded': mock.sentinel.attached}

        fallback = self._disk_utils.is_virtual_disk_file_attached
        fallback.return_value = True

        ret_val = self._vhdutils.is_virtual_disk_file_attached(
            mock.sentinel.vhd_path)
        exp_ret_val = True if exists else False

        self.assertEqual(exp_ret_val, ret_val)
        if exists:
            mock_get_vhd_info.assert_called_once_with(
                mock.sentinel.vhd_path,
                [w_const.GET_VIRTUAL_DISK_INFO_IS_LOADED])
        else:
            mock_get_vhd_info.assert_not_called()

        if exists and open_fails:
            fallback.assert_called_once_with(mock.sentinel.vhd_path)
        else:
            fallback.assert_not_called()
