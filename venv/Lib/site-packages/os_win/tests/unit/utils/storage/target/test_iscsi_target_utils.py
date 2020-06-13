# Copyright 2015 Cloudbase Solutions Srl
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

import mock

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils.storage.target import iscsi_target_utils as tg_utils


class ISCSITargetUtilsTestCase(test_base.OsWinBaseTestCase):

    _autospec_classes = [
        tg_utils.pathutils.PathUtils,
        tg_utils.hostutils.HostUtils,
        tg_utils.win32utils.Win32Utils,
    ]

    @mock.patch.object(tg_utils.ISCSITargetUtils,
                       '_ensure_wt_provider_available')
    def setUp(self, mock_ensure_wt_provider_available):
        super(ISCSITargetUtilsTestCase, self).setUp()

        self._tgutils = tg_utils.ISCSITargetUtils()
        self._tgutils._conn_wmi = mock.Mock()

    def test_ensure_wt_provider_unavailable(self):
        self._tgutils._conn_wmi = None
        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils._ensure_wt_provider_available)

    def test_get_supported_disk_format_6_2(self):
        self._tgutils._win_gteq_6_3 = False
        fmt = self._tgutils.get_supported_disk_format()
        self.assertEqual(constants.DISK_FORMAT_VHD, fmt)

    def test_get_supported_disk_format_6_3(self):
        self._tgutils._win_gteq_6_3 = True
        fmt = self._tgutils.get_supported_disk_format()
        self.assertEqual(constants.DISK_FORMAT_VHDX, fmt)

    def test_get_supported_vhd_type_6_2(self):
        self._tgutils._win_gteq_6_3 = False
        vhd_type = self._tgutils.get_supported_vhd_type()
        self.assertEqual(constants.VHD_TYPE_FIXED, vhd_type)

    def test_get_supported_vhd_type_6_3(self):
        self._tgutils._win_gteq_6_3 = True
        vhd_type = self._tgutils.get_supported_vhd_type()
        self.assertEqual(constants.VHD_TYPE_DYNAMIC, vhd_type)

    def _test_get_portal_locations(self, available_only=False,
                                   fail_if_none_found=False):
        mock_portal = mock.Mock(Listen=False,
                                Address=mock.sentinel.address,
                                Port=mock.sentinel.port)
        mock_portal_location = "%s:%s" % (mock.sentinel.address,
                                          mock.sentinel.port)

        mock_wt_portal_cls = self._tgutils._conn_wmi.WT_Portal
        mock_wt_portal_cls.return_value = [mock_portal]

        if available_only and fail_if_none_found:
            self.assertRaises(exceptions.ISCSITargetException,
                              self._tgutils.get_portal_locations,
                              available_only=available_only,
                              fail_if_none_found=fail_if_none_found)
        else:
            portals = self._tgutils.get_portal_locations(
                available_only=available_only,
                fail_if_none_found=fail_if_none_found)

            expected_retrieved_portals = []
            if not available_only:
                expected_retrieved_portals.append(mock_portal_location)

            self.assertEqual(expected_retrieved_portals,
                             portals)

    def test_get_portal_locations(self):
        self._test_get_portal_locations()

    def test_get_available_portal_locations(self):
        self._test_get_portal_locations(available_only=True)

    def test_get_portal_locations_failing_if_none(self):
        self._test_get_portal_locations(available_only=True,
                                        fail_if_none_found=True)

    def _test_get_wt_host(self, host_found=True, fail_if_not_found=False):
        mock_wt_host = mock.Mock()
        mock_wt_host_cls = self._tgutils._conn_wmi.WT_Host
        mock_wt_host_cls.return_value = [mock_wt_host] if host_found else []

        if not host_found and fail_if_not_found:
            self.assertRaises(exceptions.ISCSITargetException,
                              self._tgutils._get_wt_host,
                              mock.sentinel.target_name,
                              fail_if_not_found=fail_if_not_found)
        else:
            wt_host = self._tgutils._get_wt_host(
                mock.sentinel.target_name,
                fail_if_not_found=fail_if_not_found)

            expected_wt_host = mock_wt_host if host_found else None
            self.assertEqual(expected_wt_host, wt_host)

        mock_wt_host_cls.assert_called_once_with(
            HostName=mock.sentinel.target_name)

    def test_get_wt_host(self):
        self._test_get_wt_host()

    def test_get_wt_host_not_found(self):
        self._test_get_wt_host(host_found=False)

    def test_get_wt_host_not_found_exception(self):
        self._test_get_wt_host(host_found=False,
                               fail_if_not_found=True)

    def _test_get_wt_disk(self, disk_found=True, fail_if_not_found=False):
        mock_wt_disk = mock.Mock()
        mock_wt_disk_cls = self._tgutils._conn_wmi.WT_Disk
        mock_wt_disk_cls.return_value = [mock_wt_disk] if disk_found else []

        if not disk_found and fail_if_not_found:
            self.assertRaises(exceptions.ISCSITargetException,
                              self._tgutils._get_wt_disk,
                              mock.sentinel.disk_description,
                              fail_if_not_found=fail_if_not_found)
        else:
            wt_disk = self._tgutils._get_wt_disk(
                mock.sentinel.disk_description,
                fail_if_not_found=fail_if_not_found)

            expected_wt_disk = mock_wt_disk if disk_found else None
            self.assertEqual(expected_wt_disk, wt_disk)

        mock_wt_disk_cls.assert_called_once_with(
            Description=mock.sentinel.disk_description)

    def test_get_wt_disk(self):
        self._test_get_wt_disk()

    def test_get_wt_disk_not_found(self):
        self._test_get_wt_disk(disk_found=False)

    def test_get_wt_disk_not_found_exception(self):
        self._test_get_wt_disk(disk_found=False,
                               fail_if_not_found=True)

    def _test_get_wt_snap(self, snap_found=True, fail_if_not_found=False):
        mock_wt_snap = mock.Mock()
        mock_wt_snap_cls = self._tgutils._conn_wmi.WT_Snapshot
        mock_wt_snap_cls.return_value = [mock_wt_snap] if snap_found else []

        if not snap_found and fail_if_not_found:
            self.assertRaises(exceptions.ISCSITargetException,
                              self._tgutils._get_wt_snapshot,
                              mock.sentinel.snap_description,
                              fail_if_not_found=fail_if_not_found)
        else:
            wt_snap = self._tgutils._get_wt_snapshot(
                mock.sentinel.snap_description,
                fail_if_not_found=fail_if_not_found)

            expected_wt_snap = mock_wt_snap if snap_found else None
            self.assertEqual(expected_wt_snap, wt_snap)

        mock_wt_snap_cls.assert_called_once_with(
            Description=mock.sentinel.snap_description)

    def test_get_wt_snap(self):
        self._test_get_wt_snap()

    def test_get_wt_snap_not_found(self):
        self._test_get_wt_snap(snap_found=False)

    def test_get_wt_snap_not_found_exception(self):
        self._test_get_wt_snap(snap_found=False,
                               fail_if_not_found=True)

    def _test_get_wt_idmethod(self, idmeth_found=True):
        mock_wt_idmeth = mock.Mock()
        mock_wt_idmeth_cls = self._tgutils._conn_wmi.WT_IDMethod
        mock_wt_idmeth_cls.return_value = ([mock_wt_idmeth]
                                           if idmeth_found else [])

        wt_idmeth = self._tgutils._get_wt_idmethod(mock.sentinel.initiator,
                                                   mock.sentinel.target_name)

        expected_wt_idmeth = mock_wt_idmeth if idmeth_found else None
        self.assertEqual(expected_wt_idmeth, wt_idmeth)

        mock_wt_idmeth_cls.assert_called_once_with(
            HostName=mock.sentinel.target_name,
            Value=mock.sentinel.initiator)

    def test_get_wt_idmethod(self):
        self._test_get_wt_idmethod()

    def test_get_wt_idmethod_not_found(self):
        self._test_get_wt_idmethod(idmeth_found=False)

    @mock.patch('os_win._utils.get_com_error_code')
    def _test_create_iscsi_target_exception(self, mock_get_com_err_code,
                                            target_exists=False,
                                            fail_if_exists=False):
        mock_wt_host_cls = self._tgutils._conn_wmi.WT_Host
        mock_wt_host_cls.NewHost.side_effect = test_base.FakeWMIExc
        mock_get_com_err_code.return_value = (
            self._tgutils._ERR_FILE_EXISTS if target_exists else 1)

        if target_exists and not fail_if_exists:
            self._tgutils.create_iscsi_target(mock.sentinel.target_name,
                                              fail_if_exists=fail_if_exists)
        else:
            self.assertRaises(exceptions.ISCSITargetException,
                              self._tgutils.create_iscsi_target,
                              mock.sentinel.target_name,
                              fail_if_exists=fail_if_exists)

        mock_wt_host_cls.NewHost.assert_called_once_with(
            HostName=mock.sentinel.target_name)

    def test_create_iscsi_target_exception(self):
        self._test_create_iscsi_target_exception()

    def test_create_iscsi_target_already_exists_skipping(self):
        self._test_create_iscsi_target_exception(target_exists=True)

    def test_create_iscsi_target_already_exists_failing(self):
        self._test_create_iscsi_target_exception(target_exists=True,
                                                 fail_if_exists=True)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_host')
    def test_delete_iscsi_target_exception(self, mock_get_wt_host):
        mock_wt_host = mock_get_wt_host.return_value
        mock_wt_host.Delete_.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.delete_iscsi_target,
                          mock.sentinel.target_name)

        mock_wt_host.RemoveAllWTDisks.assert_called_once_with()
        mock_get_wt_host.assert_called_once_with(mock.sentinel.target_name,
                                                 fail_if_not_found=False)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_host')
    def _test_iscsi_target_exists(self, mock_get_wt_host, target_exists=True):
        mock_get_wt_host.return_value = (mock.sentinel.wt_host
                                         if target_exists else None)

        result = self._tgutils.iscsi_target_exists(mock.sentinel.target_name)

        self.assertEqual(target_exists, result)
        mock_get_wt_host.assert_called_once_with(mock.sentinel.target_name,
                                                 fail_if_not_found=False)

    def test_iscsi_target_exists(self):
        self._test_iscsi_target_exists()

    def test_iscsi_target_unexisting(self):
        self._test_iscsi_target_exists(target_exists=False)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_host')
    def test_get_target_information(self, mock_get_wt_host):
        mock_wt_host = mock_get_wt_host.return_value
        mock_wt_host.EnableCHAP = True
        mock_wt_host.Status = 1  # connected

        target_info = self._tgutils.get_target_information(
            mock.sentinel.target_name)

        expected_info = dict(target_iqn=mock_wt_host.TargetIQN,
                             enabled=mock_wt_host.Enabled,
                             connected=True,
                             auth_method='CHAP',
                             auth_username=mock_wt_host.CHAPUserName,
                             auth_password=mock_wt_host.CHAPSecret)
        self.assertEqual(expected_info, target_info)
        mock_get_wt_host.assert_called_once_with(mock.sentinel.target_name)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_host')
    def test_set_chap_credentials_exception(self, mock_get_wt_host):
        mock_wt_host = mock_get_wt_host.return_value
        mock_wt_host.put.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.set_chap_credentials,
                          mock.sentinel.target_name,
                          mock.sentinel.chap_username,
                          mock.sentinel.chap_password)

        mock_get_wt_host.assert_called_once_with(mock.sentinel.target_name)
        self.assertTrue(mock_wt_host.EnableCHAP),
        self.assertEqual(mock.sentinel.chap_username,
                         mock_wt_host.CHAPUserName)
        self.assertEqual(mock.sentinel.chap_password,
                         mock_wt_host.CHAPSecret)
        mock_wt_host.put.assert_called_once_with()

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_idmethod')
    def test_associate_initiator_exception(self, mock_get_wtidmethod):
        mock_get_wtidmethod.return_value = None
        mock_wt_idmeth_cls = self._tgutils._conn_wmi.WT_IDMethod
        mock_wt_idmetod = mock_wt_idmeth_cls.new.return_value
        mock_wt_idmetod.put.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.associate_initiator_with_iscsi_target,
                          mock.sentinel.initiator, mock.sentinel.target_name,
                          id_method=mock.sentinel.id_method)

        self.assertEqual(mock.sentinel.target_name, mock_wt_idmetod.HostName)
        self.assertEqual(mock.sentinel.initiator, mock_wt_idmetod.Value)
        self.assertEqual(mock.sentinel.id_method, mock_wt_idmetod.Method)
        mock_get_wtidmethod.assert_called_once_with(mock.sentinel.initiator,
                                                    mock.sentinel.target_name)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_idmethod')
    def test_already_associated_initiator(self, mock_get_wtidmethod):
        mock_wt_idmeth_cls = self._tgutils._conn_wmi.WT_IDMethod

        self._tgutils.associate_initiator_with_iscsi_target(
            mock.sentinel.initiator, mock.sentinel.target_name,
            id_method=mock.sentinel.id_method)

        self.assertFalse(mock_wt_idmeth_cls.new.called)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_idmethod')
    def test_deassociate_initiator_exception(self, mock_get_wtidmethod):
        mock_wt_idmetod = mock_get_wtidmethod.return_value
        mock_wt_idmetod.Delete_.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.deassociate_initiator,
                          mock.sentinel.initiator, mock.sentinel.target_name)

        mock_get_wtidmethod.assert_called_once_with(mock.sentinel.initiator,
                                                    mock.sentinel.target_name)

    def test_create_wt_disk_exception(self):
        mock_wt_disk_cls = self._tgutils._conn_wmi.WT_Disk
        mock_wt_disk_cls.NewWTDisk.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.create_wt_disk,
                          mock.sentinel.vhd_path, mock.sentinel.wtd_name,
                          mock.sentinel.size_mb)

        mock_wt_disk_cls.NewWTDisk.assert_called_once_with(
            DevicePath=mock.sentinel.vhd_path,
            Description=mock.sentinel.wtd_name,
            SizeInMB=mock.sentinel.size_mb)

    def test_import_wt_disk_exception(self):
        mock_wt_disk_cls = self._tgutils._conn_wmi.WT_Disk
        mock_wt_disk_cls.ImportWTDisk.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.import_wt_disk,
                          mock.sentinel.vhd_path, mock.sentinel.wtd_name)

        mock_wt_disk_cls.ImportWTDisk.assert_called_once_with(
            DevicePath=mock.sentinel.vhd_path,
            Description=mock.sentinel.wtd_name)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_disk')
    def test_change_wt_disk_status_exception(self, mock_get_wt_disk):
        mock_wt_disk = mock_get_wt_disk.return_value
        mock_wt_disk.put.side_effect = test_base.FakeWMIExc
        wt_disk_enabled = True

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.change_wt_disk_status,
                          mock.sentinel.wtd_name,
                          enabled=wt_disk_enabled)

        mock_get_wt_disk.assert_called_once_with(mock.sentinel.wtd_name)
        self.assertEqual(wt_disk_enabled, mock_wt_disk.Enabled)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_disk')
    def test_remove_wt_disk_exception(self, mock_get_wt_disk):
        mock_wt_disk = mock_get_wt_disk.return_value
        mock_wt_disk.Delete_.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.remove_wt_disk,
                          mock.sentinel.wtd_name)

        mock_get_wt_disk.assert_called_once_with(mock.sentinel.wtd_name,
                                                 fail_if_not_found=False)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_disk')
    def test_extend_wt_disk_exception(self, mock_get_wt_disk):
        mock_wt_disk = mock_get_wt_disk.return_value
        mock_wt_disk.Extend.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.extend_wt_disk,
                          mock.sentinel.wtd_name,
                          mock.sentinel.additional_mb)

        mock_get_wt_disk.assert_called_once_with(mock.sentinel.wtd_name)
        mock_wt_disk.Extend.assert_called_once_with(
            mock.sentinel.additional_mb)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_host')
    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_disk')
    def test_add_disk_to_target_exception(self, mock_get_wt_disk,
                                          mock_get_wt_host):
        mock_wt_disk = mock_get_wt_disk.return_value
        mock_wt_host = mock_get_wt_host.return_value
        mock_wt_host.AddWTDisk.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.add_disk_to_target,
                          mock.sentinel.wtd_name,
                          mock.sentinel.target_name)

        mock_get_wt_disk.assert_called_once_with(mock.sentinel.wtd_name)
        mock_get_wt_host.assert_called_once_with(mock.sentinel.target_name)
        mock_wt_host.AddWTDisk.assert_called_once_with(mock_wt_disk.WTD)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_disk')
    def test_create_snapshot_exception(self, mock_get_wt_disk):
        mock_wt_disk = mock_get_wt_disk.return_value
        mock_wt_snap = mock.Mock()
        mock_wt_snap.put.side_effect = test_base.FakeWMIExc
        mock_wt_snap_cls = self._tgutils._conn_wmi.WT_Snapshot
        mock_wt_snap_cls.return_value = [mock_wt_snap]
        mock_wt_snap_cls.Create.return_value = [mock.sentinel.snap_id]

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.create_snapshot,
                          mock.sentinel.wtd_name,
                          mock.sentinel.snap_name)

        mock_get_wt_disk.assert_called_once_with(mock.sentinel.wtd_name)
        mock_wt_snap_cls.Create.assert_called_once_with(WTD=mock_wt_disk.WTD)
        mock_wt_snap_cls.assert_called_once_with(Id=mock.sentinel.snap_id)
        self.assertEqual(mock.sentinel.snap_name, mock_wt_snap.Description)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_snapshot')
    def test_delete_snapshot_exception(self, mock_get_wt_snap):
        mock_wt_snap = mock_get_wt_snap.return_value
        mock_wt_snap.Delete_.side_effect = test_base.FakeWMIExc

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.delete_snapshot,
                          mock.sentinel.snap_name)

        mock_get_wt_snap.assert_called_once_with(mock.sentinel.snap_name,
                                                 fail_if_not_found=False)

    @mock.patch.object(tg_utils.ISCSITargetUtils, '_get_wt_snapshot')
    def test_export_snapshot_exception(self, mock_get_wt_snap):
        mock_wt_disk_cls = self._tgutils._conn_wmi.WT_Disk
        mock_wt_disk = mock.Mock()
        mock_wt_disk_cls.return_value = [mock_wt_disk]
        mock_wt_disk.Delete_.side_effect = test_base.FakeWMIExc
        mock_wt_snap = mock_get_wt_snap.return_value
        mock_wt_snap.Export.return_value = [mock.sentinel.wt_disk_id]

        self.assertRaises(exceptions.ISCSITargetException,
                          self._tgutils.export_snapshot,
                          mock.sentinel.snap_name,
                          mock.sentinel.dest_path)

        mock_get_wt_snap.assert_called_once_with(mock.sentinel.snap_name)
        mock_wt_snap.Export.assert_called_once_with()
        mock_wt_disk_cls.assert_called_once_with(WTD=mock.sentinel.wt_disk_id)

        expected_wt_disk_description = "%s-%s-temp" % (
            mock.sentinel.snap_name,
            mock.sentinel.wt_disk_id)
        self.assertEqual(expected_wt_disk_description,
                         mock_wt_disk.Description)

        mock_wt_disk.put.assert_called_once_with()
        mock_wt_disk.Delete_.assert_called_once_with()
        self._tgutils._pathutils.copy.assert_called_once_with(
            mock_wt_disk.DevicePath, mock.sentinel.dest_path)
