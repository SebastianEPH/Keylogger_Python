# Copyright 2014 Cloudbase Solutions Srl
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

import platform

import ddt
import mock

from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import _wqlutils
from os_win.utils.compute import livemigrationutils
from os_win.utils.compute import vmutils
from os_win.utils import jobutils


@ddt.ddt
class LiveMigrationUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V LiveMigrationUtils class."""

    _autospec_classes = [
        vmutils.VMUtils,
        jobutils.JobUtils,
    ]

    _FAKE_VM_NAME = 'fake_vm_name'
    _FAKE_RET_VAL = 0

    _RESOURCE_TYPE_VHD = 31
    _RESOURCE_TYPE_DISK = 17
    _RESOURCE_SUB_TYPE_VHD = 'Microsoft:Hyper-V:Virtual Hard Disk'
    _RESOURCE_SUB_TYPE_DISK = 'Microsoft:Hyper-V:Physical Disk Drive'

    def setUp(self):
        super(LiveMigrationUtilsTestCase, self).setUp()
        self.liveutils = livemigrationutils.LiveMigrationUtils()
        self._conn = mock.MagicMock()
        self.liveutils._conn_attr = self._conn

        self.liveutils._get_wmi_obj = mock.MagicMock(return_value=self._conn)
        self.liveutils._conn_v2 = self._conn

    def test_get_conn_v2(self):
        self.liveutils._get_wmi_obj.side_effect = exceptions.x_wmi(
            com_error=mock.Mock())

        self.assertRaises(exceptions.HyperVException,
                          self.liveutils._get_conn_v2, '.')

        self.liveutils._get_wmi_obj.assert_called_once_with(
            self.liveutils._wmi_namespace % '.', compatibility_mode=True)

    def test_check_live_migration_config(self):
        mock_migr_svc = (
            self._conn.Msvm_VirtualSystemMigrationService.return_value[0])
        conn_vsmssd = self._conn.Msvm_VirtualSystemMigrationServiceSettingData

        vsmssd = mock.MagicMock()
        vsmssd.EnableVirtualSystemMigration = True
        conn_vsmssd.return_value = [vsmssd]
        mock_migr_svc.MigrationServiceListenerIPAdressList.return_value = [
            mock.sentinel.FAKE_HOST]

        self.liveutils.check_live_migration_config()
        conn_vsmssd.assert_called_once_with()
        self._conn.Msvm_VirtualSystemMigrationService.assert_called_once_with()

    def test_get_vm(self):
        expected_vm = mock.MagicMock()
        mock_conn_v2 = mock.MagicMock()
        mock_conn_v2.Msvm_ComputerSystem.return_value = [expected_vm]

        found_vm = self.liveutils._get_vm(mock_conn_v2, self._FAKE_VM_NAME)

        self.assertEqual(expected_vm, found_vm)

    def test_get_vm_duplicate(self):
        mock_vm = mock.MagicMock()
        mock_conn_v2 = mock.MagicMock()
        mock_conn_v2.Msvm_ComputerSystem.return_value = [mock_vm, mock_vm]

        self.assertRaises(exceptions.HyperVException, self.liveutils._get_vm,
                          mock_conn_v2, self._FAKE_VM_NAME)

    def test_get_vm_not_found(self):
        mock_conn_v2 = mock.MagicMock()
        mock_conn_v2.Msvm_ComputerSystem.return_value = []

        self.assertRaises(exceptions.HyperVVMNotFoundException,
                          self.liveutils._get_vm,
                          mock_conn_v2, self._FAKE_VM_NAME)

    def test_create_planned_vm_helper(self):
        mock_vm = mock.MagicMock()
        mock_v2 = mock.MagicMock()
        mock_vsmsd_cls = mock_v2.Msvm_VirtualSystemMigrationSettingData
        mock_vsmsd = mock_vsmsd_cls.return_value[0]
        self._conn.Msvm_PlannedComputerSystem.return_value = [mock_vm]

        migr_svc = mock_v2.Msvm_VirtualSystemMigrationService()[0]
        migr_svc.MigrateVirtualSystemToHost.return_value = (
            self._FAKE_RET_VAL, mock.sentinel.FAKE_JOB_PATH)

        resulted_vm = self.liveutils._create_planned_vm(
            self._conn, mock_v2, mock_vm, [mock.sentinel.FAKE_REMOTE_IP_ADDR],
            mock.sentinel.FAKE_HOST)

        self.assertEqual(mock_vm, resulted_vm)

        mock_vsmsd_cls.assert_called_once_with(
            MigrationType=self.liveutils._MIGRATION_TYPE_STAGED)
        migr_svc.MigrateVirtualSystemToHost.assert_called_once_with(
            ComputerSystem=mock_vm.path_.return_value,
            DestinationHost=mock.sentinel.FAKE_HOST,
            MigrationSettingData=mock_vsmsd.GetText_.return_value)
        self.liveutils._jobutils.check_ret_val.assert_called_once_with(
            mock.sentinel.FAKE_JOB_PATH,
            self._FAKE_RET_VAL)

    def test_get_disk_data(self):
        mock_vmutils_remote = mock.MagicMock()
        mock_disk = mock.MagicMock()
        mock_disk_path_mapping = {
            mock.sentinel.serial: mock.sentinel.disk_path}

        mock_disk.path.return_value.RelPath = mock.sentinel.rel_path
        mock_vmutils_remote.get_vm_disks.return_value = [
            None, [mock_disk]]
        mock_disk.ElementName = mock.sentinel.serial

        resulted_disk_paths = self.liveutils._get_disk_data(
            self._FAKE_VM_NAME, mock_vmutils_remote, mock_disk_path_mapping)

        mock_vmutils_remote.get_vm_disks.assert_called_once_with(
            self._FAKE_VM_NAME)
        mock_disk.path.assert_called_once_with()
        expected_disk_paths = {mock.sentinel.rel_path: mock.sentinel.disk_path}
        self.assertEqual(expected_disk_paths, resulted_disk_paths)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_update_planned_vm_disk_resources(self,
                                              mock_get_elem_associated_class):
        self._prepare_vm_mocks(self._RESOURCE_TYPE_DISK,
                               self._RESOURCE_SUB_TYPE_DISK,
                               mock_get_elem_associated_class)
        mock_vm = mock.Mock(Name='fake_name')
        sasd = mock_get_elem_associated_class.return_value[0]

        mock_vsmsvc = self._conn.Msvm_VirtualSystemManagementService()[0]

        self.liveutils._update_planned_vm_disk_resources(
            self._conn, mock_vm, mock.sentinel.FAKE_VM_NAME,
            {sasd.path.return_value.RelPath: mock.sentinel.FAKE_RASD_PATH})

        mock_vsmsvc.ModifyResourceSettings.assert_called_once_with(
            ResourceSettings=[sasd.GetText_.return_value])
        mock_get_elem_associated_class.assert_called_once_with(
            self._conn, self.liveutils._CIM_RES_ALLOC_SETTING_DATA_CLASS,
            element_uuid=mock_vm.Name)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_vhd_setting_data(self, mock_get_elem_associated_class):
        self._prepare_vm_mocks(self._RESOURCE_TYPE_VHD,
                               self._RESOURCE_SUB_TYPE_VHD,
                               mock_get_elem_associated_class)
        mock_vm = mock.Mock(Name='fake_vm_name')
        mock_sasd = mock_get_elem_associated_class.return_value[0]

        vhd_sds = self.liveutils._get_vhd_setting_data(mock_vm)
        self.assertEqual([mock_sasd.GetText_.return_value], vhd_sds)
        mock_get_elem_associated_class.assert_called_once_with(
            self._conn, self.liveutils._STORAGE_ALLOC_SETTING_DATA_CLASS,
            element_uuid=mock_vm.Name)

    def test_live_migrate_vm_helper(self):
        mock_conn_local = mock.MagicMock()
        mock_vm = mock.MagicMock()
        mock_vsmsd_cls = (
            mock_conn_local.Msvm_VirtualSystemMigrationSettingData)
        mock_vsmsd = mock_vsmsd_cls.return_value[0]

        mock_vsmsvc = mock_conn_local.Msvm_VirtualSystemMigrationService()[0]
        mock_vsmsvc.MigrateVirtualSystemToHost.return_value = (
            self._FAKE_RET_VAL, mock.sentinel.FAKE_JOB_PATH)

        self.liveutils._live_migrate_vm(
            mock_conn_local, mock_vm, None,
            [mock.sentinel.FAKE_REMOTE_IP_ADDR],
            mock.sentinel.FAKE_RASD_PATH, mock.sentinel.FAKE_HOST,
            mock.sentinel.migration_type)

        mock_vsmsd_cls.assert_called_once_with(
            MigrationType=mock.sentinel.migration_type)
        mock_vsmsvc.MigrateVirtualSystemToHost.assert_called_once_with(
            ComputerSystem=mock_vm.path_.return_value,
            DestinationHost=mock.sentinel.FAKE_HOST,
            MigrationSettingData=mock_vsmsd.GetText_.return_value,
            NewResourceSettingData=mock.sentinel.FAKE_RASD_PATH)

    @mock.patch.object(
        livemigrationutils.LiveMigrationUtils, '_live_migrate_vm')
    @mock.patch.object(
        livemigrationutils.LiveMigrationUtils, '_get_vhd_setting_data')
    @mock.patch.object(
        livemigrationutils.LiveMigrationUtils, '_get_planned_vm')
    def test_live_migrate_single_planned_vm(self, mock_get_planned_vm,
                                            mock_get_vhd_sd,
                                            mock_live_migrate_vm):
        mock_vm = self._get_vm()

        mock_migr_svc = self._conn.Msvm_VirtualSystemMigrationService()[0]
        mock_migr_svc.MigrationServiceListenerIPAddressList = [
            mock.sentinel.FAKE_REMOTE_IP_ADDR]

        mock_get_planned_vm.return_value = mock_vm
        self.liveutils.live_migrate_vm(mock.sentinel.vm_name,
                                       mock.sentinel.FAKE_HOST)
        self.liveutils._live_migrate_vm.assert_called_once_with(
            self._conn, mock_vm, mock_vm,
            [mock.sentinel.FAKE_REMOTE_IP_ADDR],
            self.liveutils._get_vhd_setting_data.return_value,
            mock.sentinel.FAKE_HOST,
            self.liveutils._MIGRATION_TYPE_VIRTUAL_SYSTEM_AND_STORAGE)
        mock_get_planned_vm.assert_called_once_with(
            mock.sentinel.vm_name, self._conn)

    @mock.patch.object(livemigrationutils.LiveMigrationUtils, '_get_vm')
    @mock.patch.object(livemigrationutils.LiveMigrationUtils,
                       '_get_ip_address_list')
    @mock.patch.object(livemigrationutils.LiveMigrationUtils,
                       '_update_planned_vm_disk_resources')
    @mock.patch.object(livemigrationutils.LiveMigrationUtils,
                       '_create_planned_vm')
    @mock.patch.object(livemigrationutils.LiveMigrationUtils,
                       'destroy_existing_planned_vm')
    @mock.patch.object(livemigrationutils.LiveMigrationUtils,
                       '_get_disk_data')
    def test_create_planned_vm(self, mock_get_disk_data,
                               mock_destroy_existing_planned_vm,
                               mock_create_planned_vm,
                               mock_update_planned_vm_disk_resources,
                               mock_get_ip_address_list, mock_get_vm):
        dest_host = platform.node()
        mock_vm = mock.MagicMock()
        mock_get_vm.return_value = mock_vm
        mock_conn_v2 = mock.MagicMock()
        self.liveutils._get_wmi_obj.return_value = mock_conn_v2

        mock_get_disk_data.return_value = mock.sentinel.disk_data
        mock_get_ip_address_list.return_value = mock.sentinel.ip_address_list

        mock_vsmsvc = self._conn.Msvm_VirtualSystemManagementService()[0]
        mock_vsmsvc.ModifyResourceSettings.return_value = (
            mock.sentinel.res_setting,
            mock.sentinel.job_path,
            self._FAKE_RET_VAL)

        self.liveutils.create_planned_vm(mock.sentinel.vm_name,
                                         mock.sentinel.host,
                                         mock.sentinel.disk_path_mapping)

        mock_destroy_existing_planned_vm.assert_called_once_with(
            mock.sentinel.vm_name)
        mock_get_ip_address_list.assert_called_once_with(self._conn, dest_host)
        mock_get_disk_data.assert_called_once_with(
            mock.sentinel.vm_name,
            vmutils.VMUtils.return_value,
            mock.sentinel.disk_path_mapping)
        mock_create_planned_vm.assert_called_once_with(
            self._conn, mock_conn_v2, mock_vm,
            mock.sentinel.ip_address_list, dest_host)
        mock_update_planned_vm_disk_resources.assert_called_once_with(
            self._conn, mock_create_planned_vm.return_value,
            mock.sentinel.vm_name, mock.sentinel.disk_data)

    def _prepare_vm_mocks(self, resource_type, resource_sub_type,
                          mock_get_elem_associated_class):
        mock_vm_svc = self._conn.Msvm_VirtualSystemManagementService()[0]
        vm = self._get_vm()
        self._conn.Msvm_PlannedComputerSystem.return_value = [vm]
        mock_vm_svc.DestroySystem.return_value = (mock.sentinel.FAKE_JOB_PATH,
                                                  self._FAKE_RET_VAL)
        mock_vm_svc.ModifyResourceSettings.return_value = (
            None, mock.sentinel.FAKE_JOB_PATH, self._FAKE_RET_VAL)

        sasd = mock.MagicMock()
        other_sasd = mock.MagicMock()
        sasd.ResourceType = resource_type
        sasd.ResourceSubType = resource_sub_type
        sasd.HostResource = [mock.sentinel.FAKE_SASD_RESOURCE]
        sasd.path.return_value.RelPath = mock.sentinel.FAKE_DISK_PATH

        mock_get_elem_associated_class.return_value = [sasd, other_sasd]

    def _get_vm(self):
        mock_vm = mock.MagicMock()
        self._conn.Msvm_ComputerSystem.return_value = [mock_vm]
        mock_vm.path_.return_value = mock.sentinel.FAKE_VM_PATH
        mock_vm.Name = self._FAKE_VM_NAME
        return mock_vm
