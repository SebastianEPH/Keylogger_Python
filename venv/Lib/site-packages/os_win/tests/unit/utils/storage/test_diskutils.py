# Copyright 2016 Cloudbase Solutions Srl
# All Rights Reserved.
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

import ddt
import mock

from os_win import _utils
from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils.storage import diskutils


@ddt.ddt
class DiskUtilsTestCase(test_base.OsWinBaseTestCase):

    _autospec_classes = [
        diskutils.pathutils.PathUtils,
        diskutils.win32utils.Win32Utils,
    ]

    def setUp(self):
        super(DiskUtilsTestCase, self).setUp()
        self._diskutils = diskutils.DiskUtils()
        self._diskutils._conn_cimv2 = mock.MagicMock()
        self._diskutils._conn_storage = mock.MagicMock()
        self._mock_run = self._diskutils._win32_utils.run_and_check_output
        self._pathutils = self._diskutils._pathutils

    @ddt.data(True, False)
    def test_get_disk_by_number(self, msft_disk_cls):
        resulted_disk = self._diskutils._get_disk_by_number(
            mock.sentinel.disk_number,
            msft_disk_cls=msft_disk_cls)

        if msft_disk_cls:
            disk_cls = self._diskutils._conn_storage.Msft_Disk
            disk_cls.assert_called_once_with(Number=mock.sentinel.disk_number)
        else:
            disk_cls = self._diskutils._conn_cimv2.Win32_DiskDrive
            disk_cls.assert_called_once_with(Index=mock.sentinel.disk_number)

        mock_disk = disk_cls.return_value[0]
        self.assertEqual(mock_disk, resulted_disk)

    def test_get_unexisting_disk_by_number(self):
        mock_msft_disk_cls = self._diskutils._conn_storage.Msft_Disk
        mock_msft_disk_cls.return_value = []

        self.assertRaises(exceptions.DiskNotFound,
                          self._diskutils._get_disk_by_number,
                          mock.sentinel.disk_number)

        mock_msft_disk_cls.assert_called_once_with(
            Number=mock.sentinel.disk_number)

    def test_get_attached_virtual_disk_files(self):
        disks = [mock.Mock(), mock.Mock()]
        disk_cls = self._diskutils._conn_storage.Msft_Disk
        disk_cls.return_value = disks

        ret_val = self._diskutils.get_attached_virtual_disk_files()
        exp_ret_val = [
            dict(location=disk.Location,
                 number=disk.Number,
                 offline=disk.IsOffline,
                 readonly=disk.IsReadOnly)
            for disk in disks]
        self.assertEqual(exp_ret_val, ret_val)

        disk_cls.assert_called_once_with(
            BusType=diskutils.BUS_FILE_BACKED_VIRTUAL)

    @ddt.data({},
              {'exists': False},
              {'same_file': False})
    @ddt.unpack
    @mock.patch('os.path.exists')
    @mock.patch.object(diskutils.DiskUtils, 'get_attached_virtual_disk_files')
    def test_is_virtual_disk_file_attached(self, mock_get_disks, mock_exists,
                                           exists=True, same_file=True):
        mock_get_disks.return_value = [dict(location=mock.sentinel.other_path)]
        mock_exists.return_value = exists
        self._pathutils.is_same_file.return_value = same_file

        attached = self._diskutils.is_virtual_disk_file_attached(
            mock.sentinel.path)
        self.assertEqual(exists and same_file, attached)

        if exists:
            mock_get_disks.assert_called_once_with()
            self._pathutils.is_same_file.assert_called_once_with(
                mock.sentinel.path, mock.sentinel.other_path)
        else:
            mock_get_disks.assert_not_called()
            self._pathutils.is_same_file.assert_not_called()

    def test_get_disk_by_unique_id(self):
        disk_cls = self._diskutils._conn_storage.Msft_Disk
        mock_disks = disk_cls.return_value

        resulted_disks = self._diskutils._get_disks_by_unique_id(
            mock.sentinel.unique_id,
            mock.sentinel.unique_id_format)

        disk_cls.assert_called_once_with(
            UniqueId=mock.sentinel.unique_id,
            UniqueIdFormat=mock.sentinel.unique_id_format)

        self.assertEqual(mock_disks, resulted_disks)

    def test_get_unexisting_disk_by_unique_id(self):
        mock_msft_disk_cls = self._diskutils._conn_storage.Msft_Disk
        mock_msft_disk_cls.return_value = []

        self.assertRaises(exceptions.DiskNotFound,
                          self._diskutils._get_disks_by_unique_id,
                          mock.sentinel.unique_id,
                          mock.sentinel.unique_id_format)

    @mock.patch.object(diskutils.DiskUtils, '_get_disks_by_unique_id')
    def test_get_disk_number_by_unique_id(self, mock_get_disks):
        mock_disks = [mock.Mock(), mock.Mock()]
        mock_get_disks.return_value = mock_disks

        exp_disk_numbers = [mock_disk.Number for mock_disk in mock_disks]
        returned_disk_numbers = self._diskutils.get_disk_numbers_by_unique_id(
            mock.sentinel.unique_id, mock.sentinel.unique_id_format)

        self.assertEqual(exp_disk_numbers, returned_disk_numbers)
        mock_get_disks.assert_called_once_with(
            mock.sentinel.unique_id, mock.sentinel.unique_id_format)

    @mock.patch.object(diskutils.DiskUtils, '_get_disk_by_number')
    def test_get_disk_uid_and_uid_type(self, mock_get_disk):
        mock_disk = mock_get_disk.return_value

        uid, uid_type = self._diskutils.get_disk_uid_and_uid_type(
            mock.sentinel.disk_number)

        mock_get_disk.assert_called_once_with(mock.sentinel.disk_number)
        self.assertEqual(mock_disk.UniqueId, uid)
        self.assertEqual(mock_disk.UniqueIdFormat, uid_type)

    def test_get_disk_uid_and_uid_type_not_found(self):
        mock_msft_disk_cls = self._diskutils._conn_storage.Msft_Disk
        mock_msft_disk_cls.return_value = []

        self.assertRaises(exceptions.DiskNotFound,
                          self._diskutils.get_disk_uid_and_uid_type,
                          mock.sentinel.disk_number)

    @ddt.data({'disk_path': r'\\?\MPio#disk&ven_fakeVendor',
               'expect_mpio': True},
              {'disk_path': r'\\?\SCSI#disk&ven_fakeVendor',
               'expect_mpio': False})
    @ddt.unpack
    @mock.patch.object(diskutils.DiskUtils, '_get_disk_by_number')
    def test_is_mpio_disk(self, mock_get_disk, disk_path, expect_mpio):
        mock_disk = mock_get_disk.return_value
        mock_disk.Path = disk_path

        result = self._diskutils.is_mpio_disk(mock.sentinel.disk_number)
        self.assertEqual(expect_mpio, result)

        mock_get_disk.assert_called_once_with(mock.sentinel.disk_number)

    @mock.patch.object(diskutils.DiskUtils, '_get_disk_by_number')
    def test_refresh_disk(self, mock_get_disk):
        mock_disk = mock_get_disk.return_value

        self._diskutils.refresh_disk(mock.sentinel.disk_number)

        mock_get_disk.assert_called_once_with(mock.sentinel.disk_number)
        mock_disk.Refresh.assert_called_once_with()

    @mock.patch.object(diskutils.DiskUtils, '_get_disk_by_number')
    def test_get_device_name_by_device_number(self, mock_get_disk):
        dev_name = self._diskutils.get_device_name_by_device_number(
            mock.sentinel.disk_number)

        self.assertEqual(mock_get_disk.return_value.Name, dev_name)

        mock_get_disk.assert_called_once_with(mock.sentinel.disk_number,
                                              msft_disk_cls=False)

    def test_get_dev_number_from_dev_name(self):
        fake_physical_device_name = r'\\.\PhysicalDrive15'
        expected_device_number = '15'

        get_dev_number = self._diskutils.get_device_number_from_device_name
        resulted_dev_number = get_dev_number(fake_physical_device_name)
        self.assertEqual(expected_device_number, resulted_dev_number)

    def test_get_device_number_from_invalid_device_name(self):
        fake_physical_device_name = ''

        self.assertRaises(exceptions.DiskNotFound,
                          self._diskutils.get_device_number_from_device_name,
                          fake_physical_device_name)

    def _get_mocked_wmi_rescan(self, return_value):
        conn = self._diskutils._conn_storage
        rescan_method = conn.Msft_StorageSetting.UpdateHostStorageCache
        rescan_method.return_value = return_value
        return rescan_method

    @ddt.data(0, [0], (0,))
    @mock.patch('time.sleep')
    def test_rescan_disks(self, return_value, mock_sleep):
        mock_rescan = self._get_mocked_wmi_rescan(return_value)

        self._diskutils.rescan_disks()

        mock_rescan.assert_called_once_with()

    @mock.patch.object(diskutils, '_RESCAN_LOCK')
    @mock.patch.object(diskutils.DiskUtils, '_rescan_disks')
    def test_rescan_merge_requests(self, mock_rescan_helper, mock_rescan_lock):
        mock_rescan_lock.locked.side_effect = [False, True, True]

        self._diskutils.rescan_disks(merge_requests=True)
        self._diskutils.rescan_disks(merge_requests=True)
        self._diskutils.rescan_disks(merge_requests=False)

        exp_rescan_count = 2
        mock_rescan_helper.assert_has_calls(
            [mock.call()] * exp_rescan_count)
        mock_rescan_lock.__enter__.assert_has_calls(
            [mock.call()] * exp_rescan_count)

    @mock.patch('time.sleep')
    def test_rescan_disks_error(self, mock_sleep):
        mock_rescan = self._get_mocked_wmi_rescan(return_value=1)
        expected_retry_count = 5

        self.assertRaises(exceptions.OSWinException,
                          self._diskutils.rescan_disks)
        mock_rescan.assert_has_calls([mock.call()] * expected_retry_count)

    @mock.patch.object(diskutils, 'ctypes')
    @mock.patch.object(diskutils, 'kernel32', create=True)
    @mock.patch('os.path.abspath')
    def _test_get_disk_capacity(self, mock_abspath,
                                mock_kernel32, mock_ctypes,
                                raised_exc=None, ignore_errors=False):
        expected_values = ('total_bytes', 'free_bytes')

        mock_params = [mock.Mock(value=value) for value in expected_values]
        mock_ctypes.c_ulonglong.side_effect = mock_params
        mock_ctypes.c_wchar_p = lambda x: (x, 'c_wchar_p')

        self._mock_run.side_effect = raised_exc(
            func_name='fake_func_name',
            error_code='fake_error_code',
            error_message='fake_error_message') if raised_exc else None

        if raised_exc and not ignore_errors:
            self.assertRaises(raised_exc,
                              self._diskutils.get_disk_capacity,
                              mock.sentinel.disk_path,
                              ignore_errors=ignore_errors)
        else:
            ret_val = self._diskutils.get_disk_capacity(
                mock.sentinel.disk_path,
                ignore_errors=ignore_errors)
            expected_ret_val = (0, 0) if raised_exc else expected_values

            self.assertEqual(expected_ret_val, ret_val)

        mock_abspath.assert_called_once_with(mock.sentinel.disk_path)
        mock_ctypes.pointer.assert_has_calls(
            [mock.call(param) for param in mock_params])
        self._mock_run.assert_called_once_with(
            mock_kernel32.GetDiskFreeSpaceExW,
            mock_ctypes.c_wchar_p(mock_abspath.return_value),
            None,
            mock_ctypes.pointer.return_value,
            mock_ctypes.pointer.return_value,
            kernel32_lib_func=True)

    def test_get_disk_capacity_successfully(self):
        self._test_get_disk_capacity()

    def test_get_disk_capacity_ignored_error(self):
        self._test_get_disk_capacity(
            raised_exc=exceptions.Win32Exception,
            ignore_errors=True)

    def test_get_disk_capacity_raised_exc(self):
        self._test_get_disk_capacity(
            raised_exc=exceptions.Win32Exception)

    @mock.patch.object(diskutils.DiskUtils, '_get_disk_by_number')
    def test_get_disk_size(self, mock_get_disk):
        disk_size = self._diskutils.get_disk_size(
            mock.sentinel.disk_number)

        self.assertEqual(mock_get_disk.return_value.Size, disk_size)

        mock_get_disk.assert_called_once_with(mock.sentinel.disk_number)

    def test_parse_scsi_id_desc(self):
        vpd_str = ('008300240103001060002AC00000000000000EA0'
                   '0000869902140004746573740115000400000001')
        buff = _utils.hex_str_to_byte_array(vpd_str)

        identifiers = self._diskutils._parse_scsi_page_83(buff)

        exp_scsi_id_0 = '60002AC00000000000000EA000008699'
        exp_scsi_id_1 = '74657374'
        exp_scsi_id_2 = '00000001'

        exp_identifiers = [
            {'protocol': None,
             'raw_id_desc_size': 20,
             'raw_id': _utils.hex_str_to_byte_array(exp_scsi_id_0),
             'code_set': 1,
             'type': 3,
             'id': exp_scsi_id_0,
             'association': 0},
            {'protocol': None,
             'raw_id_desc_size': 8,
             'raw_id': _utils.hex_str_to_byte_array(exp_scsi_id_1),
             'code_set': 2,
             'type': 4,
             'id': 'test',
             'association': 1},
            {'protocol': None,
             'raw_id_desc_size': 8,
             'raw_id': _utils.hex_str_to_byte_array(exp_scsi_id_2),
             'code_set': 1,
             'type': 5,
             'id': exp_scsi_id_2,
             'association': 1}]

        self.assertEqual(exp_identifiers, identifiers)

    def test_parse_supported_scsi_id_desc(self):
        vpd_str = ('008300240103001060002AC00000000000000EA0'
                   '0000869901140004000003F40115000400000001')
        buff = _utils.hex_str_to_byte_array(vpd_str)

        identifiers = self._diskutils._parse_scsi_page_83(
            buff, select_supported_identifiers=True)

        exp_scsi_id = '60002AC00000000000000EA000008699'
        exp_identifiers = [
            {'protocol': None,
             'raw_id_desc_size': 20,
             'raw_id': _utils.hex_str_to_byte_array(exp_scsi_id),
             'code_set': 1,
             'type': 3,
             'id': exp_scsi_id,
             'association': 0}]
        self.assertEqual(exp_identifiers, identifiers)

    def test_parse_scsi_page_83_no_desc(self):
        # We've set the page length field to 0, so we're expecting an
        # empty list to be returned.
        vpd_str = ('008300000103001060002AC00000000000000EA0'
                   '0000869901140004000003F40115000400000001')
        buff = _utils.hex_str_to_byte_array(vpd_str)

        identifiers = self._diskutils._parse_scsi_page_83(buff)
        self.assertEqual([], identifiers)

    def test_parse_scsi_id_desc_exc(self):
        vpd_str = '0083'
        # Invalid VPD page data (buffer too small)
        self.assertRaises(exceptions.SCSIPageParsingError,
                          self._diskutils._parse_scsi_page_83,
                          _utils.hex_str_to_byte_array(vpd_str))

        vpd_str = ('00FF00240103001060002AC00000000000000EA0'
                   '0000869901140004000003F40115000400000001')
        # Unexpected page code
        self.assertRaises(exceptions.SCSIPageParsingError,
                          self._diskutils._parse_scsi_page_83,
                          _utils.hex_str_to_byte_array(vpd_str))

        vpd_str = ('008300F40103001060002AC00000000000000EA0'
                   '0000869901140004000003F40115000400000001')
        # VPD page overflow
        self.assertRaises(exceptions.SCSIPageParsingError,
                          self._diskutils._parse_scsi_page_83,
                          _utils.hex_str_to_byte_array(vpd_str))

        vpd_str = ('00830024010300FF60002AC00000000000000EA0'
                   '0000869901140004000003F40115000400000001')
        # Identifier overflow
        self.assertRaises(exceptions.SCSIIdDescriptorParsingError,
                          self._diskutils._parse_scsi_page_83,
                          _utils.hex_str_to_byte_array(vpd_str))

        vpd_str = ('0083001F0103001060002AC00000000000000EA0'
                   '0000869901140004000003F4011500')
        # Invalid identifier structure (too small)
        self.assertRaises(exceptions.SCSIIdDescriptorParsingError,
                          self._diskutils._parse_scsi_page_83,
                          _utils.hex_str_to_byte_array(vpd_str))

    def test_select_supported_scsi_identifiers(self):
        identifiers = [
            {'type': id_type}
            for id_type in constants.SUPPORTED_SCSI_UID_FORMATS[::-1]]
        identifiers.append({'type': mock.sentinel.scsi_id_format})

        expected_identifiers = [
            {'type': id_type}
            for id_type in constants.SUPPORTED_SCSI_UID_FORMATS]

        result = self._diskutils._select_supported_scsi_identifiers(
            identifiers)
        self.assertEqual(expected_identifiers, result)

    def test_get_new_disk_policy(self):
        mock_setting_obj = mock.Mock()
        setting_cls = self._diskutils._conn_storage.MSFT_StorageSetting
        setting_cls.Get.return_value = (0, mock_setting_obj)

        policy = self._diskutils.get_new_disk_policy()
        self.assertEqual(mock_setting_obj.NewDiskPolicy, policy)

    def test_set_new_disk_policy(self):
        self._diskutils.set_new_disk_policy(mock.sentinel.policy)

        setting_cls = self._diskutils._conn_storage.MSFT_StorageSetting
        setting_cls.Set.assert_called_once_with(
            NewDiskPolicy=mock.sentinel.policy)

    @mock.patch.object(diskutils.DiskUtils, '_get_disk_by_number')
    @ddt.data(0, 1)
    def test_set_disk_online(self, err_code, mock_get_disk):
        mock_disk = mock_get_disk.return_value
        mock_disk.Online.return_value = (mock.sentinel.ext_err_info,
                                         err_code)

        if err_code:
            self.assertRaises(exceptions.DiskUpdateError,
                              self._diskutils.set_disk_online,
                              mock.sentinel.disk_number)
        else:
            self._diskutils.set_disk_online(mock.sentinel.disk_number)

        mock_disk.Online.assert_called_once_with()
        mock_get_disk.assert_called_once_with(mock.sentinel.disk_number)

    @mock.patch.object(diskutils.DiskUtils, '_get_disk_by_number')
    @ddt.data(0, 1)
    def test_set_disk_offline(self, err_code, mock_get_disk):
        mock_disk = mock_get_disk.return_value
        mock_disk.Offline.return_value = (mock.sentinel.ext_err_info,
                                          err_code)

        if err_code:
            self.assertRaises(exceptions.DiskUpdateError,
                              self._diskutils.set_disk_offline,
                              mock.sentinel.disk_number)
        else:
            self._diskutils.set_disk_offline(mock.sentinel.disk_number)

        mock_disk.Offline.assert_called_once_with()
        mock_get_disk.assert_called_once_with(mock.sentinel.disk_number)

    @mock.patch.object(diskutils.DiskUtils, '_get_disk_by_number')
    @ddt.data(0, 1)
    def test_set_disk_readonly(self, err_code, mock_get_disk):
        mock_disk = mock_get_disk.return_value
        mock_disk.SetAttributes.return_value = (mock.sentinel.ext_err_info,
                                                err_code)

        if err_code:
            self.assertRaises(exceptions.DiskUpdateError,
                              self._diskutils.set_disk_readonly_status,
                              mock.sentinel.disk_number,
                              read_only=True)
        else:
            self._diskutils.set_disk_readonly_status(
                mock.sentinel.disk_number,
                read_only=True)

        mock_disk.SetAttributes.assert_called_once_with(IsReadOnly=True)
        mock_get_disk.assert_called_once_with(mock.sentinel.disk_number)
