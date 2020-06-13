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

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils.compute import migrationutils


@ddt.ddt
class MigrationUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V MigrationUtils class."""

    _autospec_classes = [
        migrationutils.vmutils.VMUtils,
        migrationutils.jobutils.JobUtils,
    ]

    _FAKE_VM_NAME = 'fake_vm'

    def setUp(self):
        super(MigrationUtilsTestCase, self).setUp()
        self._migrationutils = migrationutils.MigrationUtils()
        self._migrationutils._conn_attr = mock.MagicMock()

    def test_get_export_setting_data(self):
        mock_vm = self._migrationutils._vmutils._lookup_vm.return_value
        mock_conn = self._migrationutils._compat_conn
        mock_exp = mock_conn.Msvm_VirtualSystemExportSettingData
        mock_exp.return_value = [mock.sentinel.export_setting_data]
        expected_result = mock.sentinel.export_setting_data

        actual_result = self._migrationutils._get_export_setting_data(
            self._FAKE_VM_NAME)
        self.assertEqual(expected_result, actual_result)
        mock_exp.assert_called_once_with(InstanceID=mock_vm.InstanceID)

    @mock.patch.object(
        migrationutils.MigrationUtils, '_get_export_setting_data')
    def test_export_vm(self, mock_get_export_setting_data):
        mock_vm = self._migrationutils._vmutils._lookup_vm.return_value
        export_setting_data = mock_get_export_setting_data.return_value
        mock_svc = self._migrationutils._vs_man_svc
        mock_svc.ExportSystemDefinition.return_value = (
            mock.sentinel.job_path, mock.sentinel.ret_val)

        self._migrationutils.export_vm(
            vm_name=self._FAKE_VM_NAME,
            export_path=mock.sentinel.fake_export_path)

        self.assertEqual(constants.EXPORT_CONFIG_SNAPSHOTS_ALL,
                         export_setting_data.CopySnapshotConfiguration)
        self.assertFalse(export_setting_data.CopyVmStorage)
        self.assertFalse(export_setting_data.CreateVmExportSubdirectory)
        mock_get_export_setting_data.assert_called_once_with(
            self._FAKE_VM_NAME)
        mock_svc.ExportSystemDefinition.assert_called_once_with(
            ComputerSystem=mock_vm.path_(),
            ExportDirectory=mock.sentinel.fake_export_path,
            ExportSettingData=export_setting_data.GetText_(1))
        self._migrationutils._jobutils.check_ret_val.assert_called_once_with(
            mock.sentinel.ret_val, mock.sentinel.job_path)

    def test_import_vm_definition(self):
        mock_svc = self._migrationutils._vs_man_svc
        mock_svc.ImportSystemDefinition.return_value = (
            mock.sentinel.ref,
            mock.sentinel.job_path,
            mock.sentinel.ret_val)

        self._migrationutils.import_vm_definition(
            export_config_file_path=mock.sentinel.export_config_file_path,
            snapshot_folder_path=mock.sentinel.snapshot_folder_path)

        mock_svc.ImportSystemDefinition.assert_called_once_with(
            False, mock.sentinel.snapshot_folder_path,
            mock.sentinel.export_config_file_path)
        self._migrationutils._jobutils.check_ret_val.assert_called_once_with(
            mock.sentinel.ret_val, mock.sentinel.job_path)

    @mock.patch.object(migrationutils.MigrationUtils, '_get_planned_vm')
    def test_realize_vm(self, mock_get_planned_vm):
        mock_get_planned_vm.return_value = mock.MagicMock()
        self._migrationutils._vs_man_svc.ValidatePlannedSystem.return_value = (
            mock.sentinel.job_path_ValidatePlannedSystem,
            mock.sentinel.ret_val_ValidatePlannedSystem)
        self._migrationutils._vs_man_svc.RealizePlannedSystem.return_value = (
            mock.sentinel.job_path_RealizePlannedSystem,
            mock.sentinel.ref_RealizePlannedSystem,
            mock.sentinel.ret_val_RealizePlannedSystem)

        self._migrationutils.realize_vm(self._FAKE_VM_NAME)

        mock_get_planned_vm.assert_called_once_with(
            self._FAKE_VM_NAME, fail_if_not_found=True)
        expected_call = [
            mock.call(mock.sentinel.ret_val_ValidatePlannedSystem,
                      mock.sentinel.job_path_ValidatePlannedSystem),
            mock.call(mock.sentinel.ret_val_RealizePlannedSystem,
                      mock.sentinel.job_path_RealizePlannedSystem)]
        self._migrationutils._jobutils.check_ret_val.has_calls(expected_call)

    @ddt.data([mock.sentinel.planned_vm], [])
    def test_get_planned_vm(self, planned_vm):
        planned_computer_system = (
            self._migrationutils._conn.Msvm_PlannedComputerSystem)
        planned_computer_system.return_value = planned_vm

        actual_result = self._migrationutils._get_planned_vm(
            self._FAKE_VM_NAME, fail_if_not_found=False)

        if planned_vm:
            self.assertEqual(planned_vm[0], actual_result)
        else:
            self.assertIsNone(actual_result)
        planned_computer_system.assert_called_once_with(
            ElementName=self._FAKE_VM_NAME)

    def test_get_planned_vm_exception(self):
        planned_computer_system = (
            self._migrationutils._conn.Msvm_PlannedComputerSystem)
        planned_computer_system.return_value = None

        self.assertRaises(exceptions.HyperVException,
                          self._migrationutils._get_planned_vm,
                          self._FAKE_VM_NAME, fail_if_not_found=True)

        planned_computer_system.assert_called_once_with(
            ElementName=self._FAKE_VM_NAME)

    @mock.patch.object(migrationutils.MigrationUtils, '_get_planned_vm')
    def test_planned_vm_exists(self, mock_get_planned_vm):
        mock_get_planned_vm.return_value = None

        result = self._migrationutils.planned_vm_exists(mock.sentinel.vm_name)
        self.assertFalse(result)
        mock_get_planned_vm.assert_called_once_with(mock.sentinel.vm_name)

    def test_destroy_planned_vm(self):
        mock_planned_vm = mock.MagicMock()
        mock_planned_vm.path_.return_value = mock.sentinel.planned_vm_path
        mock_vs_man_svc = self._migrationutils._vs_man_svc
        mock_vs_man_svc.DestroySystem.return_value = (
            mock.sentinel.job_path, mock.sentinel.ret_val)

        self._migrationutils._destroy_planned_vm(mock_planned_vm)

        mock_vs_man_svc.DestroySystem.assert_called_once_with(
            mock.sentinel.planned_vm_path)
        self._migrationutils._jobutils.check_ret_val.assert_called_once_with(
            mock.sentinel.ret_val,
            mock.sentinel.job_path)

    @ddt.data({'planned_vm': None}, {'planned_vm': mock.sentinel.planned_vm})
    @ddt.unpack
    @mock.patch.object(migrationutils.MigrationUtils, '_destroy_planned_vm')
    @mock.patch.object(migrationutils.MigrationUtils, '_get_planned_vm')
    def test_destroy_existing_planned_vm(self, mock_get_planned_vm,
                                         mock_destroy_planned_vm, planned_vm):
        mock_get_planned_vm.return_value = planned_vm

        self._migrationutils.destroy_existing_planned_vm(mock.sentinel.vm_name)

        mock_get_planned_vm.assert_called_once_with(
            mock.sentinel.vm_name, self._migrationutils._compat_conn)
        if planned_vm:
            mock_destroy_planned_vm.assert_called_once_with(planned_vm)
        else:
            self.assertFalse(mock_destroy_planned_vm.called)
