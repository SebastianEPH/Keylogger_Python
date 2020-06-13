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

import ddt
import mock
from six.moves import range  # noqa

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import _wqlutils
from os_win.utils.compute import vmutils


@ddt.ddt
class VMUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V VMUtils class."""

    _autospec_classes = [
        vmutils.jobutils.JobUtils,
        vmutils.pathutils.PathUtils,
    ]

    _FAKE_VM_NAME = 'fake_vm'
    _FAKE_MEMORY_MB = 2
    _FAKE_VCPUS_NUM = 4
    _FAKE_JOB_PATH = 'fake_job_path'
    _FAKE_RET_VAL = 0
    _FAKE_PATH = "fake_path"
    _FAKE_CTRL_PATH = 'fake_ctrl_path'
    _FAKE_CTRL_ADDR = 0
    _FAKE_DRIVE_ADDR = 0
    _FAKE_MOUNTED_DISK_PATH = 'fake_mounted_disk_path'
    _FAKE_VM_PATH = "fake_vm_path"
    _FAKE_VHD_PATH = "fake_vhd_path"
    _FAKE_DVD_PATH = "fake_dvd_path"
    _FAKE_VOLUME_DRIVE_PATH = "fake_volume_drive_path"
    _FAKE_VM_UUID = "04e79212-39bc-4065-933c-50f6d48a57f6"
    _FAKE_INSTANCE = {"name": _FAKE_VM_NAME,
                      "uuid": _FAKE_VM_UUID}
    _FAKE_SNAPSHOT_PATH = "fake_snapshot_path"
    _FAKE_RES_DATA = "fake_res_data"
    _FAKE_HOST_RESOURCE = "fake_host_resource"
    _FAKE_CLASS = "FakeClass"
    _FAKE_RES_PATH = "fake_res_path"
    _FAKE_RES_NAME = 'fake_res_name'
    _FAKE_ADDRESS = "fake_address"
    _FAKE_DYNAMIC_MEMORY_RATIO = 1.0
    _FAKE_MONITOR_COUNT = 1

    _FAKE_MEMORY_INFO = {'DynamicMemoryEnabled': True,
                         'Reservation': 1024,
                         'Limit': 4096,
                         'Weight': 5000,
                         'MaxMemoryBlocksPerNumaNode': 2048}

    _FAKE_SUMMARY_INFO = {'NumberOfProcessors': 4,
                          'EnabledState': 2,
                          'MemoryUsage': 2,
                          'UpTime': 1}

    _DEFINE_SYSTEM = 'DefineSystem'
    _DESTROY_SYSTEM = 'DestroySystem'
    _DESTROY_SNAPSHOT = 'DestroySnapshot'
    _VM_GEN = constants.VM_GEN_2

    _VIRTUAL_SYSTEM_TYPE_REALIZED = 'Microsoft:Hyper-V:System:Realized'

    def setUp(self):
        super(VMUtilsTestCase, self).setUp()
        self._vmutils = vmutils.VMUtils()
        self._vmutils._conn_attr = mock.MagicMock()
        self._jobutils = self._vmutils._jobutils

    def test_get_vm_summary_info(self):
        self._lookup_vm()

        mock_summary = mock.MagicMock()
        mock_svc = self._vmutils._vs_man_svc
        mock_svc.GetSummaryInformation.return_value = (self._FAKE_RET_VAL,
                                                       [mock_summary])

        for (key, val) in self._FAKE_SUMMARY_INFO.items():
            setattr(mock_summary, key, val)

        summary = self._vmutils.get_vm_summary_info(self._FAKE_VM_NAME)
        self.assertEqual(self._FAKE_SUMMARY_INFO, summary)

    def _lookup_vm(self):
        mock_vm = mock.MagicMock()
        self._vmutils._lookup_vm_check = mock.MagicMock(
            return_value=mock_vm)
        mock_vm.path_.return_value = self._FAKE_VM_PATH
        return mock_vm

    def test_lookup_vm_ok(self):
        mock_vm = mock.MagicMock()
        self._vmutils._conn.Msvm_ComputerSystem.return_value = [mock_vm]
        vm = self._vmutils._lookup_vm_check(self._FAKE_VM_NAME, as_vssd=False)
        self.assertEqual(mock_vm, vm)

    def test_lookup_vm_multiple(self):
        mockvm = mock.MagicMock()
        self._vmutils._conn.Msvm_ComputerSystem.return_value = [mockvm, mockvm]
        self.assertRaises(exceptions.HyperVException,
                          self._vmutils._lookup_vm_check,
                          self._FAKE_VM_NAME,
                          as_vssd=False)

    def test_lookup_vm_none(self):
        self._vmutils._conn.Msvm_ComputerSystem.return_value = []
        self.assertRaises(exceptions.HyperVVMNotFoundException,
                          self._vmutils._lookup_vm_check,
                          self._FAKE_VM_NAME,
                          as_vssd=False)

    def test_lookup_vm_as_vssd(self):
        vssd = mock.MagicMock()
        expected_vssd = mock.MagicMock(
            VirtualSystemType=self._vmutils._VIRTUAL_SYSTEM_TYPE_REALIZED)

        self._vmutils._conn.Msvm_VirtualSystemSettingData.return_value = [
            vssd, expected_vssd]

        vssd = self._vmutils._lookup_vm_check(self._FAKE_VM_NAME)
        self.assertEqual(expected_vssd, vssd)

    @mock.patch.object(vmutils.VMUtils, '_lookup_vm')
    def test_vm_exists(self, mock_lookup_vm):
        result = self._vmutils.vm_exists(mock.sentinel.vm_name)

        self.assertTrue(result)
        mock_lookup_vm.assert_called_once_with(mock.sentinel.vm_name, False)

    def test_set_vm_memory_static(self):
        self._test_set_vm_memory_dynamic(dynamic_memory_ratio=1.0)

    def test_set_vm_memory_dynamic(self):
        self._test_set_vm_memory_dynamic(dynamic_memory_ratio=2.0)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_vm_memory_info(self, mock_get_element_associated_class):
        vmsetting = self._lookup_vm()

        mock_s = mock.MagicMock(**self._FAKE_MEMORY_INFO)
        mock_get_element_associated_class.return_value = [mock_s]

        memory = self._vmutils.get_vm_memory_info(self._FAKE_VM_NAME)
        self.assertEqual(self._FAKE_MEMORY_INFO, memory)

        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._compat_conn,
            self._vmutils._MEMORY_SETTING_DATA_CLASS,
            element_instance_id=vmsetting.InstanceID)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def _test_set_vm_memory_dynamic(self, mock_get_element_associated_class,
                                    dynamic_memory_ratio,
                                    mem_per_numa_node=None):
        mock_s = mock.MagicMock()

        mock_get_element_associated_class.return_value = [mock_s]

        self._vmutils._set_vm_memory(mock_s,
                                     self._FAKE_MEMORY_MB,
                                     mem_per_numa_node,
                                     dynamic_memory_ratio)

        self._vmutils._jobutils.modify_virt_resource.assert_called_once_with(
            mock_s)

        if mem_per_numa_node:
            self.assertEqual(mem_per_numa_node,
                             mock_s.MaxMemoryBlocksPerNumaNode)
        if dynamic_memory_ratio > 1:
            self.assertTrue(mock_s.DynamicMemoryEnabled)
        else:
            self.assertFalse(mock_s.DynamicMemoryEnabled)

    def test_set_vm_vcpus(self):
        self._check_set_vm_vcpus()

    def test_set_vm_vcpus_per_vnuma_node(self):
        self._check_set_vm_vcpus(vcpus_per_numa_node=1)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def _check_set_vm_vcpus(self, mock_get_element_associated_class,
                            vcpus_per_numa_node=None):
        procsetting = mock.MagicMock()
        mock_vmsettings = mock.MagicMock()
        mock_get_element_associated_class.return_value = [procsetting]

        self._vmutils._set_vm_vcpus(mock_vmsettings,
                                    self._FAKE_VCPUS_NUM,
                                    vcpus_per_numa_node,
                                    limit_cpu_features=False)

        self._vmutils._jobutils.modify_virt_resource.assert_called_once_with(
            procsetting)
        if vcpus_per_numa_node:
            self.assertEqual(vcpus_per_numa_node,
                             procsetting.MaxProcessorsPerNumaNode)
        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn, self._vmutils._PROCESSOR_SETTING_DATA_CLASS,
            element_instance_id=mock_vmsettings.InstanceID)

    def test_soft_shutdown_vm(self):
        mock_vm = self._lookup_vm()
        mock_shutdown = mock.MagicMock()
        mock_shutdown.InitiateShutdown.return_value = (self._FAKE_RET_VAL, )
        self._vmutils._conn.Msvm_ShutdownComponent.return_value = [
            mock_shutdown]

        self._vmutils.soft_shutdown_vm(self._FAKE_VM_NAME)

        mock_shutdown.InitiateShutdown.assert_called_once_with(
            Force=False, Reason=mock.ANY)
        self._vmutils._conn.Msvm_ShutdownComponent.assert_called_once_with(
            SystemName=mock_vm.Name)
        self._vmutils._jobutils.check_ret_val.assert_called_once_with(
            self._FAKE_RET_VAL, None)

    def test_soft_shutdown_vm_no_component(self):
        mock_vm = self._lookup_vm()
        self._vmutils._conn.Msvm_ShutdownComponent.return_value = []

        self._vmutils.soft_shutdown_vm(self._FAKE_VM_NAME)

        self._vmutils._conn.Msvm_ShutdownComponent.assert_called_once_with(
            SystemName=mock_vm.Name)
        self.assertFalse(self._vmutils._jobutils.check_ret_val.called)

    def test_get_vm_config_root_dir(self):
        mock_vm = self._lookup_vm()

        config_root_dir = self._vmutils.get_vm_config_root_dir(
            self._FAKE_VM_NAME)

        self.assertEqual(mock_vm.ConfigurationDataRoot, config_root_dir)

    @mock.patch.object(vmutils.VMUtils, '_get_vm_disks')
    @mock.patch.object(vmutils.VMUtils, '_lookup_vm_check')
    def test_get_vm_storage_paths(self, mock_lookup_vm_check,
                                  mock_get_vm_disks):
        mock_rasds = self._create_mock_disks()
        mock_get_vm_disks.return_value = ([mock_rasds[0]], [mock_rasds[1]])

        storage = self._vmutils.get_vm_storage_paths(self._FAKE_VM_NAME)
        (disk_files, volume_drives) = storage

        self.assertEqual([self._FAKE_VHD_PATH], disk_files)
        self.assertEqual([self._FAKE_VOLUME_DRIVE_PATH], volume_drives)
        mock_lookup_vm_check.assert_called_once_with(self._FAKE_VM_NAME)

    @mock.patch.object(vmutils.VMUtils, '_get_vm_disks')
    def test_get_vm_disks_by_instance_name(self, mock_get_vm_disks):
        self._lookup_vm()
        mock_get_vm_disks.return_value = mock.sentinel.vm_disks

        vm_disks = self._vmutils.get_vm_disks(self._FAKE_VM_NAME)

        self._vmutils._lookup_vm_check.assert_called_once_with(
            self._FAKE_VM_NAME)
        self.assertEqual(mock.sentinel.vm_disks, vm_disks)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_vm_disks(self, mock_get_element_associated_class):
        mock_vmsettings = self._lookup_vm()

        mock_rasds = self._create_mock_disks()
        mock_get_element_associated_class.return_value = mock_rasds

        (disks, volumes) = self._vmutils._get_vm_disks(mock_vmsettings)

        expected_calls = [
            mock.call(self._vmutils._conn,
                      self._vmutils._STORAGE_ALLOC_SETTING_DATA_CLASS,
                      element_instance_id=mock_vmsettings.InstanceID),
            mock.call(self._vmutils._conn,
                      self._vmutils._RESOURCE_ALLOC_SETTING_DATA_CLASS,
                      element_instance_id=mock_vmsettings.InstanceID)]

        mock_get_element_associated_class.assert_has_calls(expected_calls)

        self.assertEqual([mock_rasds[0]], disks)
        self.assertEqual([mock_rasds[1]], volumes)

    def _create_mock_disks(self):
        mock_rasd1 = mock.MagicMock()
        mock_rasd1.ResourceSubType = self._vmutils._HARD_DISK_RES_SUB_TYPE
        mock_rasd1.HostResource = [self._FAKE_VHD_PATH]
        mock_rasd1.Connection = [self._FAKE_VHD_PATH]
        mock_rasd1.Parent = self._FAKE_CTRL_PATH
        mock_rasd1.Address = self._FAKE_ADDRESS
        mock_rasd1.HostResource = [self._FAKE_VHD_PATH]

        mock_rasd2 = mock.MagicMock()
        mock_rasd2.ResourceSubType = self._vmutils._PHYS_DISK_RES_SUB_TYPE
        mock_rasd2.HostResource = [self._FAKE_VOLUME_DRIVE_PATH]

        return [mock_rasd1, mock_rasd2]

    def test_check_admin_permissions(self):
        mock_svc = self._vmutils._conn.Msvm_VirtualSystemManagementService
        mock_svc.return_value = False

        self.assertRaises(exceptions.HyperVAuthorizationException,
                          self._vmutils.check_admin_permissions)

    def test_set_nested_virtualization(self):
        self.assertRaises(NotImplementedError,
                          self._vmutils.set_nested_virtualization,
                          mock.sentinel.vm_name, mock.sentinel.state)

    @ddt.data(
        {'vnuma_enabled': mock.sentinel.vnuma_enabled},
        {'configuration_root_dir': mock.sentinel.configuration_root_dir},
        {'host_shutdown_action': mock.sentinel.shutdown_action},
        {})
    @ddt.unpack
    @mock.patch.object(vmutils.VMUtils, '_modify_virtual_system')
    @mock.patch.object(vmutils.VMUtils, '_set_vm_vcpus')
    @mock.patch.object(vmutils.VMUtils, '_set_vm_memory')
    @mock.patch.object(vmutils.VMUtils, '_set_vm_snapshot_type')
    @mock.patch.object(vmutils.VMUtils, '_lookup_vm_check')
    def test_update_vm(self, mock_lookup_vm_check,
                       mock_set_vm_snap_type,
                       mock_set_mem, mock_set_vcpus,
                       mock_modify_virtual_system,
                       host_shutdown_action=None,
                       configuration_root_dir=None, vnuma_enabled=None):
        mock_vmsettings = mock_lookup_vm_check.return_value
        self._vmutils.update_vm(
            mock.sentinel.vm_name, mock.sentinel.memory_mb,
            mock.sentinel.memory_per_numa, mock.sentinel.vcpus_num,
            mock.sentinel.vcpus_per_numa, mock.sentinel.limit_cpu_features,
            mock.sentinel.dynamic_mem_ratio, configuration_root_dir,
            host_shutdown_action=host_shutdown_action,
            vnuma_enabled=vnuma_enabled,
            snapshot_type=mock.sentinel.snap_type)

        mock_lookup_vm_check.assert_called_once_with(mock.sentinel.vm_name,
                                                     for_update=True)
        mock_set_mem.assert_called_once_with(
            mock_vmsettings, mock.sentinel.memory_mb,
            mock.sentinel.memory_per_numa, mock.sentinel.dynamic_mem_ratio)
        mock_set_vcpus.assert_called_once_with(
            mock_vmsettings, mock.sentinel.vcpus_num,
            mock.sentinel.vcpus_per_numa, mock.sentinel.limit_cpu_features)

        if configuration_root_dir:
            self.assertEqual(configuration_root_dir,
                             mock_vmsettings.ConfigurationDataRoot)
            self.assertEqual(configuration_root_dir,
                             mock_vmsettings.LogDataRoot)
            self.assertEqual(configuration_root_dir,
                             mock_vmsettings.SnapshotDataRoot)
            self.assertEqual(configuration_root_dir,
                             mock_vmsettings.SuspendDataRoot)
            self.assertEqual(configuration_root_dir,
                             mock_vmsettings.SwapFileDataRoot)
        if host_shutdown_action:
            self.assertEqual(host_shutdown_action,
                             mock_vmsettings.AutomaticShutdownAction)
        if vnuma_enabled:
            self.assertEqual(vnuma_enabled, mock_vmsettings.VirtualNumaEnabled)

        mock_set_vm_snap_type.assert_called_once_with(
            mock_vmsettings, mock.sentinel.snap_type)

        mock_modify_virtual_system.assert_called_once_with(
            mock_vmsettings)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_vm_scsi_controller(self, mock_get_element_associated_class):
        self._prepare_get_vm_controller(self._vmutils._SCSI_CTRL_RES_SUB_TYPE,
                                        mock_get_element_associated_class)
        path = self._vmutils.get_vm_scsi_controller(self._FAKE_VM_NAME)
        self.assertEqual(self._FAKE_RES_PATH, path)

    @mock.patch.object(vmutils.VMUtils, 'get_attached_disks')
    def test_get_free_controller_slot(self, mock_get_attached_disks):
        mock_disk = mock.MagicMock()
        mock_disk.AddressOnParent = 3
        mock_get_attached_disks.return_value = [mock_disk]

        response = self._vmutils.get_free_controller_slot(
            self._FAKE_CTRL_PATH)

        mock_get_attached_disks.assert_called_once_with(
            self._FAKE_CTRL_PATH)

        self.assertEqual(response, 0)

    def test_get_free_controller_slot_exception(self):
        fake_drive = mock.MagicMock()
        type(fake_drive).AddressOnParent = mock.PropertyMock(
            side_effect=list(range(constants.SCSI_CONTROLLER_SLOTS_NUMBER)))

        with mock.patch.object(
                self._vmutils,
                'get_attached_disks') as fake_get_attached_disks:
            fake_get_attached_disks.return_value = (
                [fake_drive] * constants.SCSI_CONTROLLER_SLOTS_NUMBER)
            self.assertRaises(exceptions.HyperVException,
                              self._vmutils.get_free_controller_slot,
                              mock.sentinel.scsi_controller_path)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_vm_ide_controller(self, mock_get_element_associated_class):
        self._prepare_get_vm_controller(
            self._vmutils._IDE_CTRL_RES_SUB_TYPE,
            mock_get_element_associated_class)
        path = self._vmutils.get_vm_ide_controller(
            mock.sentinel.FAKE_VM_SETTINGS, self._FAKE_ADDRESS)
        self.assertEqual(self._FAKE_RES_PATH, path)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_vm_ide_controller_none(self,
                                        mock_get_element_associated_class):
        self._prepare_get_vm_controller(
            self._vmutils._IDE_CTRL_RES_SUB_TYPE,
            mock_get_element_associated_class)
        path = self._vmutils.get_vm_ide_controller(
            mock.sentinel.FAKE_VM_SETTINGS, mock.sentinel.FAKE_NOT_FOUND_ADDR)
        self.assertNotEqual(self._FAKE_RES_PATH, path)

    def _prepare_get_vm_controller(self, resource_sub_type,
                                   mock_get_element_associated_class):
        self._lookup_vm()
        mock_rasds = mock.MagicMock()
        mock_rasds.path_.return_value = self._FAKE_RES_PATH
        mock_rasds.ResourceSubType = resource_sub_type
        mock_rasds.Address = self._FAKE_ADDRESS
        mock_get_element_associated_class.return_value = [mock_rasds]

    @mock.patch.object(vmutils.VMUtils, '_get_wmi_obj')
    def test_get_ide_ctrl_addr(self, mock_get_wmi_obj):
        mock_rasds = mock.Mock()
        mock_rasds.ResourceSubType = self._vmutils._IDE_CTRL_RES_SUB_TYPE
        mock_rasds.Address = mock.sentinel.ctrl_addr
        mock_get_wmi_obj.return_value = mock_rasds

        ret_val = self._vmutils._get_disk_ctrl_addr(mock.sentinel.ctrl_path)
        self.assertEqual(mock.sentinel.ctrl_addr, ret_val)

        mock_get_wmi_obj.assert_called_once_with(mock.sentinel.ctrl_path)

    @mock.patch.object(vmutils.VMUtils, '_get_vm_disk_controllers')
    @mock.patch.object(vmutils.VMUtils, '_get_wmi_obj')
    def test_get_scsi_ctrl_addr(self, mock_get_wmi_obj, mock_get_ctrls):
        mock_rasds = mock.Mock()
        mock_rasds.ResourceSubType = self._vmutils._SCSI_CTRL_RES_SUB_TYPE
        mock_rasds.associators.return_value = [mock.sentinel.vmsettings]
        mock_get_wmi_obj.return_value = mock_rasds

        mock_scsi_ctrls = ['someCtrl', self._FAKE_CTRL_PATH.upper(),
                           'someOtherCtrl']
        exp_ctrl_addr = 1

        mock_scsi_ctrl = mock.Mock()
        mock_scsi_ctrl.path_.side_effect = mock_scsi_ctrls
        mock_get_ctrls.return_value = [mock_scsi_ctrl] * len(mock_scsi_ctrls)

        ret_val = self._vmutils._get_disk_ctrl_addr(self._FAKE_CTRL_PATH)
        self.assertEqual(exp_ctrl_addr, ret_val)

        mock_get_wmi_obj.assert_called_once_with(self._FAKE_CTRL_PATH)
        mock_get_ctrls.assert_called_once_with(
            mock.sentinel.vmsettings, self._vmutils._SCSI_CTRL_RES_SUB_TYPE)

    @mock.patch.object(vmutils.VMUtils, 'get_free_controller_slot')
    @mock.patch.object(vmutils.VMUtils, '_get_vm_scsi_controller')
    def test_attach_scsi_drive(self, mock_get_vm_scsi_controller,
                               mock_get_free_controller_slot):
        mock_vm = self._lookup_vm()
        mock_get_vm_scsi_controller.return_value = self._FAKE_CTRL_PATH
        mock_get_free_controller_slot.return_value = self._FAKE_DRIVE_ADDR

        with mock.patch.object(self._vmutils,
                               'attach_drive') as mock_attach_drive:
            self._vmutils.attach_scsi_drive(mock_vm, self._FAKE_PATH,
                                            constants.DISK)

            mock_get_vm_scsi_controller.assert_called_once_with(mock_vm)
            mock_get_free_controller_slot.assert_called_once_with(
                self._FAKE_CTRL_PATH)
            mock_attach_drive.assert_called_once_with(
                mock_vm, self._FAKE_PATH, self._FAKE_CTRL_PATH,
                self._FAKE_DRIVE_ADDR, constants.DISK)

    @mock.patch.object(vmutils.VMUtils, 'attach_drive')
    @mock.patch.object(vmutils.VMUtils, '_get_vm_ide_controller')
    def test_attach_ide_drive(self, mock_get_ide_ctrl, mock_attach_drive):
        mock_vm = self._lookup_vm()

        self._vmutils.attach_ide_drive(self._FAKE_VM_NAME,
                                       self._FAKE_CTRL_PATH,
                                       self._FAKE_CTRL_ADDR,
                                       self._FAKE_DRIVE_ADDR)

        mock_get_ide_ctrl.assert_called_with(mock_vm, self._FAKE_CTRL_ADDR)
        mock_attach_drive.assert_called_once_with(
            self._FAKE_VM_NAME, self._FAKE_CTRL_PATH,
            mock_get_ide_ctrl.return_value, self._FAKE_DRIVE_ADDR,
            constants.DISK)

    @ddt.data(constants.DISK, constants.DVD)
    @mock.patch.object(vmutils.VMUtils, '_get_new_resource_setting_data')
    def test_attach_drive(self, drive_type, mock_get_new_rsd):
        mock_vm = self._lookup_vm()

        mock_drive_res = mock.Mock()
        mock_disk_res = mock.Mock()

        mock_get_new_rsd.side_effect = [mock_drive_res, mock_disk_res]
        self._jobutils.add_virt_resource.side_effect = [
            [mock.sentinel.drive_res_path],
            [mock.sentinel.disk_res_path]]

        self._vmutils.attach_drive(mock.sentinel.vm_name,
                                   mock.sentinel.disk_path,
                                   mock.sentinel.ctrl_path,
                                   mock.sentinel.drive_addr,
                                   drive_type)

        self._vmutils._lookup_vm_check.assert_called_once_with(
            mock.sentinel.vm_name, as_vssd=False)

        if drive_type == constants.DISK:
            exp_res_sub_types = [self._vmutils._DISK_DRIVE_RES_SUB_TYPE,
                                 self._vmutils._HARD_DISK_RES_SUB_TYPE]
        else:
            exp_res_sub_types = [self._vmutils._DVD_DRIVE_RES_SUB_TYPE,
                                 self._vmutils._DVD_DISK_RES_SUB_TYPE]

        mock_get_new_rsd.assert_has_calls(
            [mock.call(exp_res_sub_types[0]),
             mock.call(exp_res_sub_types[1],
                       self._vmutils._STORAGE_ALLOC_SETTING_DATA_CLASS)])

        self.assertEqual(mock.sentinel.ctrl_path, mock_drive_res.Parent)
        self.assertEqual(mock.sentinel.drive_addr, mock_drive_res.Address)
        self.assertEqual(mock.sentinel.drive_addr,
                         mock_drive_res.AddressOnParent)

        self.assertEqual(mock.sentinel.drive_res_path,
                         mock_disk_res.Parent)
        self.assertEqual([mock.sentinel.disk_path],
                         mock_disk_res.HostResource)

        self._jobutils.add_virt_resource.assert_has_calls(
            [mock.call(mock_drive_res, mock_vm),
             mock.call(mock_disk_res, mock_vm)])

    @mock.patch.object(vmutils.VMUtils, '_get_wmi_obj')
    @mock.patch.object(vmutils.VMUtils, '_get_new_resource_setting_data')
    def test_attach_drive_exc(self, mock_get_new_rsd, mock_get_wmi_obj):
        self._lookup_vm()

        mock_drive_res = mock.Mock()
        mock_disk_res = mock.Mock()

        mock_get_new_rsd.side_effect = [mock_drive_res, mock_disk_res]
        self._jobutils.add_virt_resource.side_effect = [
            [mock.sentinel.drive_res_path],
            exceptions.OSWinException]
        mock_get_wmi_obj.return_value = mock.sentinel.attached_drive_res

        self.assertRaises(exceptions.OSWinException,
                          self._vmutils.attach_drive,
                          mock.sentinel.vm_name,
                          mock.sentinel.disk_path,
                          mock.sentinel.ctrl_path,
                          mock.sentinel.drive_addr,
                          constants.DISK)

        mock_get_wmi_obj.assert_called_once_with(mock.sentinel.drive_res_path)
        self._jobutils.remove_virt_resource.assert_called_once_with(
            mock.sentinel.attached_drive_res)

    @mock.patch.object(vmutils.VMUtils,
                       '_get_mounted_disk_resource_from_path')
    def test_get_disk_attachment_info_detached(self, mock_get_disk_res):
        mock_get_disk_res.return_value = None
        self.assertRaises(exceptions.DiskNotFound,
                          self._vmutils.get_disk_attachment_info,
                          mock.sentinel.disk_path,
                          mock.sentinel.is_physical,
                          mock.sentinel.serial)

        mock_get_disk_res.assert_called_once_with(
            mock.sentinel.disk_path,
            mock.sentinel.is_physical,
            serial=mock.sentinel.serial)

    @ddt.data(True, False)
    @mock.patch.object(vmutils.VMUtils,
                       '_get_mounted_disk_resource_from_path')
    @mock.patch.object(vmutils.VMUtils,
                       '_get_disk_controller_type')
    @mock.patch.object(vmutils.VMUtils,
                       '_get_wmi_obj')
    @mock.patch.object(vmutils.VMUtils, '_get_disk_ctrl_addr')
    def test_get_disk_attachment_info(self, is_physical,
                                      mock_get_disk_ctrl_addr,
                                      mock_get_wmi_obj,
                                      mock_get_disk_ctrl_type,
                                      mock_get_disk_res):
        mock_res = mock_get_disk_res.return_value
        exp_res = mock_res if is_physical else mock_get_wmi_obj.return_value

        fake_slot = 5
        exp_res.AddressOnParent = str(fake_slot)

        exp_att_info = dict(
            controller_slot=fake_slot,
            controller_path=exp_res.Parent,
            controller_type=mock_get_disk_ctrl_type.return_value,
            controller_addr=mock_get_disk_ctrl_addr.return_value)

        att_info = self._vmutils.get_disk_attachment_info(
            mock.sentinel.disk_path,
            is_physical)
        self.assertEqual(exp_att_info, att_info)

        if not is_physical:
            mock_get_wmi_obj.assert_called_once_with(mock_res.Parent)
        mock_get_disk_ctrl_type.assert_called_once_with(exp_res.Parent)
        mock_get_disk_ctrl_addr.assert_called_once_with(exp_res.Parent)

    @ddt.data(vmutils.VMUtils._SCSI_CTRL_RES_SUB_TYPE,
              vmutils.VMUtils._IDE_CTRL_RES_SUB_TYPE)
    @mock.patch.object(vmutils.VMUtils, '_get_wmi_obj')
    def test_get_disk_controller_type(self, res_sub_type, mock_get_wmi_obj):
        mock_ctrl = mock_get_wmi_obj.return_value
        mock_ctrl.ResourceSubType = res_sub_type

        exp_ctrl_type = self._vmutils._disk_ctrl_type_mapping[res_sub_type]

        ctrl_type = self._vmutils._get_disk_controller_type(
            mock.sentinel.ctrl_path)
        self.assertEqual(exp_ctrl_type, ctrl_type)

        mock_get_wmi_obj.assert_called_once_with(mock.sentinel.ctrl_path)

    @mock.patch.object(vmutils.VMUtils, '_get_new_resource_setting_data')
    def test_create_scsi_controller(self, mock_get_new_rsd):
        mock_vm = self._lookup_vm()

        self._vmutils.create_scsi_controller(self._FAKE_VM_NAME)

        self._vmutils._jobutils.add_virt_resource.assert_called_once_with(
            mock_get_new_rsd.return_value, mock_vm)

    @mock.patch.object(vmutils.VMUtils, '_get_new_resource_setting_data')
    @mock.patch.object(vmutils.VMUtils, '_get_wmi_obj')
    def _test_attach_volume_to_controller(self, mock_get_wmi_obj,
                                          mock_get_new_rsd, disk_serial=None):
        mock_vm = self._lookup_vm()
        mock_diskdrive = mock.MagicMock()
        jobutils = self._vmutils._jobutils
        jobutils.add_virt_resource.return_value = [mock_diskdrive]
        mock_get_wmi_obj.return_value = mock_diskdrive

        self._vmutils.attach_volume_to_controller(
            self._FAKE_VM_NAME, self._FAKE_CTRL_PATH, self._FAKE_CTRL_ADDR,
            self._FAKE_MOUNTED_DISK_PATH, serial=disk_serial)

        self._vmutils._jobutils.add_virt_resource.assert_called_once_with(
            mock_get_new_rsd.return_value, mock_vm)

        if disk_serial:
            jobutils.modify_virt_resource.assert_called_once_with(
                mock_diskdrive)
            self.assertEqual(disk_serial, mock_diskdrive.ElementName)

    def test_attach_volume_to_controller_without_disk_serial(self):
        self._test_attach_volume_to_controller()

    def test_attach_volume_to_controller_with_disk_serial(self):
        self._test_attach_volume_to_controller(
            disk_serial=mock.sentinel.serial)

    @mock.patch.object(vmutils.VMUtils, '_get_new_setting_data')
    def test_create_nic(self, mock_get_new_virt_res):
        mock_vm = self._lookup_vm()
        mock_nic = mock_get_new_virt_res.return_value

        self._vmutils.create_nic(
            self._FAKE_VM_NAME, self._FAKE_RES_NAME, self._FAKE_ADDRESS)

        self._vmutils._jobutils.add_virt_resource.assert_called_once_with(
            mock_nic, mock_vm)

    def test_get_nic_data_by_name(self):
        nic_cls = self._vmutils._conn.Msvm_SyntheticEthernetPortSettingData
        nic_cls.return_value = [mock.sentinel.nic]

        nic = self._vmutils._get_nic_data_by_name(mock.sentinel.name)

        self.assertEqual(mock.sentinel.nic, nic)
        nic_cls.assert_called_once_with(ElementName=mock.sentinel.name)

    def test_get_missing_nic_data_by_name(self):
        nic_cls = self._vmutils._conn.Msvm_SyntheticEthernetPortSettingData
        nic_cls.return_value = []
        self.assertRaises(
            exceptions.HyperVvNicNotFound,
            self._vmutils._get_nic_data_by_name,
            mock.sentinel.name)

    @mock.patch.object(vmutils.VMUtils, '_get_nic_data_by_name')
    def test_destroy_nic(self, mock_get_nic_data_by_name):
        mock_nic_data = mock_get_nic_data_by_name.return_value

        # We expect this exception to be ignored.
        self._vmutils._jobutils.remove_virt_resource.side_effect = (
            exceptions.NotFound(message='fake_exc'))

        self._vmutils.destroy_nic(self._FAKE_VM_NAME,
                                  mock.sentinel.FAKE_NIC_NAME)

        self._vmutils._jobutils.remove_virt_resource.assert_called_once_with(
            mock_nic_data)

    @mock.patch.object(vmutils.VMUtils, '_lookup_vm_check')
    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_vm_nics(self, mock_get_assoc, mock_lookup_vm):
        vnics = self._vmutils._get_vm_nics(mock.sentinel.vm_name)

        self.assertEqual(mock_get_assoc.return_value, vnics)
        mock_lookup_vm.assert_called_once_with(mock.sentinel.vm_name)
        mock_get_assoc.assert_called_once_with(
            self._vmutils._compat_conn,
            self._vmutils._SYNTHETIC_ETHERNET_PORT_SETTING_DATA_CLASS,
            element_instance_id=mock_lookup_vm.return_value.InstanceId)

    @mock.patch.object(vmutils.VMUtils, '_get_vm_nics')
    def test_get_vm_nic_names(self, mock_get_vm_nics):
        exp_nic_names = ['port1', 'port2']

        mock_get_vm_nics.return_value = [
            mock.Mock(ElementName=nic_name)
            for nic_name in exp_nic_names]
        nic_names = self._vmutils.get_vm_nic_names(mock.sentinel.vm_name)

        self.assertEqual(exp_nic_names, nic_names)
        mock_get_vm_nics.assert_called_once_with(mock.sentinel.vm_name)

    def test_set_vm_state(self):
        mock_vm = self._lookup_vm()
        mock_vm.RequestStateChange.return_value = (
            self._FAKE_JOB_PATH, self._FAKE_RET_VAL)

        self._vmutils.set_vm_state(self._FAKE_VM_NAME,
                                   constants.HYPERV_VM_STATE_ENABLED)
        mock_vm.RequestStateChange.assert_called_with(
            constants.HYPERV_VM_STATE_ENABLED)

    def test_destroy_vm(self):
        self._lookup_vm()

        mock_svc = self._vmutils._vs_man_svc
        getattr(mock_svc, self._DESTROY_SYSTEM).return_value = (
            self._FAKE_JOB_PATH, self._FAKE_RET_VAL)

        self._vmutils.destroy_vm(self._FAKE_VM_NAME)

        getattr(mock_svc, self._DESTROY_SYSTEM).assert_called_with(
            self._FAKE_VM_PATH)

    @mock.patch.object(vmutils.VMUtils, 'get_vm_disks')
    def test_get_vm_physical_disk_mapping(self, mock_get_vm_disks):
        mock_phys_disk = self._create_mock_disks()[1]

        expected_serial = mock_phys_disk.ElementName
        expected_mapping = {
            expected_serial: {
                'resource_path': mock_phys_disk.path_.return_value,
                'mounted_disk_path': mock_phys_disk.HostResource[0]
            }
        }

        mock_get_vm_disks.return_value = ([], [mock_phys_disk])

        result = self._vmutils.get_vm_physical_disk_mapping(self._FAKE_VM_NAME)
        self.assertEqual(expected_mapping, result)
        mock_get_vm_disks.assert_called_once_with(self._FAKE_VM_NAME)

    @mock.patch.object(vmutils.VMUtils, '_get_wmi_obj')
    def test_set_disk_host_res(self, mock_get_wmi_obj):
        mock_diskdrive = mock_get_wmi_obj.return_value

        self._vmutils.set_disk_host_res(self._FAKE_RES_PATH,
                                        self._FAKE_MOUNTED_DISK_PATH)

        self._vmutils._jobutils.modify_virt_resource.assert_called_once_with(
            mock_diskdrive)

        mock_get_wmi_obj.assert_called_once_with(self._FAKE_RES_PATH, True)
        self.assertEqual(mock_diskdrive.HostResource,
                         [self._FAKE_MOUNTED_DISK_PATH])

    @mock.patch.object(vmutils.VMUtils, '_modify_virtual_system')
    @ddt.data(None, mock.sentinel.snap_name)
    def test_take_vm_snapshot(self, snap_name, mock_modify_virtual_system):
        self._lookup_vm()
        mock_snap = mock.Mock(ElementName=mock.sentinel.default_snap_name)

        mock_svc = self._get_snapshot_service()
        mock_svc.CreateSnapshot.return_value = (self._FAKE_JOB_PATH,
                                                mock.MagicMock(),
                                                self._FAKE_RET_VAL)

        mock_job = self._vmutils._jobutils.check_ret_val.return_value
        mock_job.associators.return_value = [mock_snap]

        snap_path = self._vmutils.take_vm_snapshot(self._FAKE_VM_NAME,
                                                   snap_name)

        self.assertEqual(mock_snap.path_.return_value, snap_path)
        mock_svc.CreateSnapshot.assert_called_with(
            AffectedSystem=self._FAKE_VM_PATH,
            SnapshotType=self._vmutils._SNAPSHOT_FULL)

        self._vmutils._jobutils.check_ret_val.assert_called_once_with(
            self._FAKE_RET_VAL, self._FAKE_JOB_PATH)

        mock_job.associators.assert_called_once_with(
            wmi_result_class=self._vmutils._VIRTUAL_SYSTEM_SETTING_DATA_CLASS,
            wmi_association_class=self._vmutils._AFFECTED_JOB_ELEMENT_CLASS)

        if snap_name:
            self.assertEqual(snap_name, mock_snap.ElementName)
            mock_modify_virtual_system.assert_called_once_with(mock_snap)
        else:
            self.assertEqual(mock.sentinel.default_snap_name,
                             mock_snap.ElementName)
            mock_modify_virtual_system.assert_not_called()

    @ddt.data(None, mock.sentinel.snap1)
    def test_get_vm_snapshots(self, snap_name):
        mock_snap1 = mock.Mock(ElementName=mock.sentinel.snap1)
        mock_snap2 = mock.Mock(ElementName=mock.sentinel.snap2)

        mock_vm = self._lookup_vm()
        mock_vm.associators.return_value = [mock_snap1, mock_snap2]

        snaps = self._vmutils.get_vm_snapshots(mock.sentinel.vm_name,
                                               snap_name)

        expected_snaps = [mock_snap1.path_.return_value]
        if not snap_name:
            expected_snaps += [mock_snap2.path_.return_value]

        self.assertEqual(expected_snaps, snaps)

        mock_vm.associators.assert_called_once_with(
            wmi_association_class=(
                self._vmutils._VIRTUAL_SYSTEM_SNAP_ASSOC_CLASS),
            wmi_result_class=(
                self._vmutils._VIRTUAL_SYSTEM_SETTING_DATA_CLASS))

    def test_remove_vm_snapshot(self):
        mock_svc = self._get_snapshot_service()
        getattr(mock_svc, self._DESTROY_SNAPSHOT).return_value = (
            self._FAKE_JOB_PATH, self._FAKE_RET_VAL)

        self._vmutils.remove_vm_snapshot(self._FAKE_SNAPSHOT_PATH)
        getattr(mock_svc, self._DESTROY_SNAPSHOT).assert_called_with(
            self._FAKE_SNAPSHOT_PATH)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_vm_dvd_disk_paths(self, mock_get_element_associated_class):
        self._lookup_vm()
        mock_sasd1 = mock.MagicMock(
            ResourceSubType=self._vmutils._DVD_DISK_RES_SUB_TYPE,
            HostResource=[mock.sentinel.FAKE_DVD_PATH1])
        mock_get_element_associated_class.return_value = [mock_sasd1]

        ret_val = self._vmutils.get_vm_dvd_disk_paths(self._FAKE_VM_NAME)
        self.assertEqual(mock.sentinel.FAKE_DVD_PATH1, ret_val[0])

    @mock.patch.object(vmutils.VMUtils,
                       '_get_mounted_disk_resource_from_path')
    def test_is_disk_attached(self, mock_get_mounted_disk_from_path):
        is_physical = True

        is_attached = self._vmutils.is_disk_attached(mock.sentinel.disk_path,
                                                     is_physical=is_physical)

        self.assertTrue(is_attached)
        mock_get_mounted_disk_from_path.assert_called_once_with(
            mock.sentinel.disk_path, is_physical)

    def test_detach_vm_disk(self):
        mock_disk = self._prepare_mock_disk()

        self._vmutils.detach_vm_disk(self._FAKE_VM_NAME,
                                     self._FAKE_HOST_RESOURCE,
                                     serial=mock.sentinel.serial)
        self._vmutils._jobutils.remove_virt_resource.assert_called_once_with(
            mock_disk)

    @ddt.data(None, mock.sentinel.serial)
    def test_get_mounted_disk_resource_from_path(self, serial):
        mock_disk = mock.MagicMock()

        if serial:
            self._vmutils._conn.query.return_value = [mock_disk]
        else:
            mock_disk.HostResource = [self._FAKE_MOUNTED_DISK_PATH]
            self._vmutils._conn.query.return_value = [
                mock.MagicMock(), mock_disk]

        physical_disk = self._vmutils._get_mounted_disk_resource_from_path(
            self._FAKE_MOUNTED_DISK_PATH, True, serial=serial)

        self.assertEqual(mock_disk, physical_disk)

    def test_get_controller_volume_paths(self):
        self._prepare_mock_disk()
        mock_disks = {self._FAKE_RES_PATH: self._FAKE_HOST_RESOURCE}
        disks = self._vmutils.get_controller_volume_paths(self._FAKE_RES_PATH)
        self.assertEqual(mock_disks, disks)

    def _prepare_mock_disk(self):
        mock_disk = mock.MagicMock()
        mock_disk.HostResource = [self._FAKE_HOST_RESOURCE]
        mock_disk.path.return_value.RelPath = self._FAKE_RES_PATH
        mock_disk.ResourceSubType = self._vmutils._HARD_DISK_RES_SUB_TYPE
        self._vmutils._conn.query.return_value = [mock_disk]

        return mock_disk

    def _get_snapshot_service(self):
        return self._vmutils._conn.Msvm_VirtualSystemSnapshotService()[0]

    def test_get_active_instances(self):
        fake_vm = mock.MagicMock()

        type(fake_vm).ElementName = mock.PropertyMock(
            side_effect=['active_vm', 'inactive_vm'])
        type(fake_vm).EnabledState = mock.PropertyMock(
            side_effect=[constants.HYPERV_VM_STATE_ENABLED,
                         constants.HYPERV_VM_STATE_DISABLED])
        self._vmutils.list_instances = mock.MagicMock(
            return_value=[mock.sentinel.fake_vm_name] * 2)
        self._vmutils._lookup_vm = mock.MagicMock(side_effect=[fake_vm] * 2)
        active_instances = self._vmutils.get_active_instances()

        self.assertEqual(['active_vm'], active_instances)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_vm_serial_ports(self, mock_get_element_associated_class):
        mock_vmsettings = self._lookup_vm()

        fake_serial_port = mock.MagicMock()
        fake_serial_port.ResourceSubType = (
            self._vmutils._SERIAL_PORT_RES_SUB_TYPE)

        mock_rasds = [fake_serial_port]
        mock_get_element_associated_class.return_value = mock_rasds

        ret_val = self._vmutils._get_vm_serial_ports(mock_vmsettings)

        self.assertEqual(mock_rasds, ret_val)
        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn, self._vmutils._SERIAL_PORT_SETTING_DATA_CLASS,
            element_instance_id=mock_vmsettings.InstanceID)

    def test_set_vm_serial_port_conn(self):
        self._lookup_vm()
        mock_com_1 = mock.Mock()
        mock_com_2 = mock.Mock()

        self._vmutils._get_vm_serial_ports = mock.Mock(
            return_value=[mock_com_1, mock_com_2])

        self._vmutils.set_vm_serial_port_connection(
            mock.sentinel.vm_name,
            port_number=1,
            pipe_path=mock.sentinel.pipe_path)

        self.assertEqual([mock.sentinel.pipe_path], mock_com_1.Connection)
        self._vmutils._jobutils.modify_virt_resource.assert_called_once_with(
            mock_com_1)

    def test_get_serial_port_conns(self):
        self._lookup_vm()

        mock_com_1 = mock.Mock()
        mock_com_1.Connection = []

        mock_com_2 = mock.Mock()
        mock_com_2.Connection = [mock.sentinel.pipe_path]

        self._vmutils._get_vm_serial_ports = mock.Mock(
            return_value=[mock_com_1, mock_com_2])

        ret_val = self._vmutils.get_vm_serial_port_connections(
            mock.sentinel.vm_name)
        expected_ret_val = [mock.sentinel.pipe_path]

        self.assertEqual(expected_ret_val, ret_val)

    def test_list_instance_notes(self):
        vs = mock.MagicMock()
        attrs = {'ElementName': 'fake_name',
                 'Notes': ['4f54fb69-d3a2-45b7-bb9b-b6e6b3d893b3']}
        vs.configure_mock(**attrs)
        vs2 = mock.MagicMock(ElementName='fake_name2', Notes=None)
        self._vmutils._conn.Msvm_VirtualSystemSettingData.return_value = [vs,
                                                                          vs2]
        response = self._vmutils.list_instance_notes()

        self.assertEqual([(attrs['ElementName'], attrs['Notes'])], response)
        self._vmutils._conn.Msvm_VirtualSystemSettingData.assert_called_with(
            ['ElementName', 'Notes'],
            VirtualSystemType=self._vmutils._VIRTUAL_SYSTEM_TYPE_REALIZED)

    def test_modify_virtual_system(self):
        mock_vs_man_svc = self._vmutils._vs_man_svc
        mock_vmsetting = mock.MagicMock()
        fake_job_path = 'fake job path'
        fake_ret_val = 'fake return value'

        mock_vs_man_svc.ModifySystemSettings.return_value = (fake_job_path,
                                                             fake_ret_val)

        self._vmutils._modify_virtual_system(vmsetting=mock_vmsetting)

        mock_vs_man_svc.ModifySystemSettings.assert_called_once_with(
            SystemSettings=mock_vmsetting.GetText_(1))
        self._vmutils._jobutils.check_ret_val.assert_called_once_with(
            fake_ret_val, fake_job_path)

    @ddt.data(True, False)
    @mock.patch.object(vmutils.VMUtils, '_get_wmi_obj')
    def test_create_vm(self, mock_get_wmi_obj, vnuma_enabled=True):
        mock_vs_man_svc = self._vmutils._vs_man_svc
        mock_vs_data = mock.MagicMock()
        fake_job_path = 'fake job path'
        fake_ret_val = 'fake return value'
        fake_vm_name = 'fake_vm_name'
        _conn = self._vmutils._conn.Msvm_VirtualSystemSettingData

        self._vmutils._jobutils.check_ret_val.return_value = mock.sentinel.job
        _conn.new.return_value = mock_vs_data
        mock_vs_man_svc.DefineSystem.return_value = (fake_job_path,
                                                     mock.sentinel.vm_path,
                                                     fake_ret_val)

        self._vmutils.create_vm(vm_name=fake_vm_name,
                                vm_gen=constants.VM_GEN_2,
                                notes='fake notes',
                                vnuma_enabled=vnuma_enabled,
                                instance_path=mock.sentinel.instance_path)

        _conn.new.assert_called_once_with()
        self.assertEqual(mock_vs_data.ElementName, fake_vm_name)
        mock_vs_man_svc.DefineSystem.assert_called_once_with(
            ResourceSettings=[], ReferenceConfiguration=None,
            SystemSettings=mock_vs_data.GetText_(1))
        self._vmutils._jobutils.check_ret_val.assert_called_once_with(
            fake_ret_val, fake_job_path)

        self.assertEqual(self._vmutils._VIRTUAL_SYSTEM_SUBTYPE_GEN2,
                         mock_vs_data.VirtualSystemSubType)
        self.assertFalse(mock_vs_data.SecureBootEnabled)

        self.assertEqual(vnuma_enabled, mock_vs_data.VirtualNumaEnabled)
        self.assertEqual(self._vmutils._VIRTUAL_SYSTEM_SUBTYPE_GEN2,
                         mock_vs_data.VirtualSystemSubType)
        self.assertEqual(mock_vs_data.Notes, 'fake notes')
        self.assertEqual(mock.sentinel.instance_path,
                         mock_vs_data.ConfigurationDataRoot)
        self.assertEqual(mock.sentinel.instance_path, mock_vs_data.LogDataRoot)
        self.assertEqual(mock.sentinel.instance_path,
                         mock_vs_data.SnapshotDataRoot)
        self.assertEqual(mock.sentinel.instance_path,
                         mock_vs_data.SuspendDataRoot)
        self.assertEqual(mock.sentinel.instance_path,
                         mock_vs_data.SwapFileDataRoot)

    def test_list_instances(self):
        vs = mock.MagicMock()
        attrs = {'ElementName': 'fake_name'}
        vs.configure_mock(**attrs)
        self._vmutils._conn.Msvm_VirtualSystemSettingData.return_value = [vs]
        response = self._vmutils.list_instances()

        self.assertEqual([(attrs['ElementName'])], response)
        self._vmutils._conn.Msvm_VirtualSystemSettingData.assert_called_with(
            ['ElementName'],
            VirtualSystemType=self._vmutils._VIRTUAL_SYSTEM_TYPE_REALIZED)

    def test_get_attached_disks(self):
        mock_scsi_ctrl_path = mock.MagicMock()
        expected_query = ("SELECT * FROM %(class_name)s "
                          "WHERE (ResourceSubType='%(res_sub_type)s' OR "
                          "ResourceSubType='%(res_sub_type_virt)s' OR "
                          "ResourceSubType='%(res_sub_type_dvd)s') AND "
                          "Parent = '%(parent)s'" %
                          {"class_name":
                           self._vmutils._RESOURCE_ALLOC_SETTING_DATA_CLASS,
                           "res_sub_type":
                           self._vmutils._PHYS_DISK_RES_SUB_TYPE,
                           "res_sub_type_virt":
                           self._vmutils._DISK_DRIVE_RES_SUB_TYPE,
                           "res_sub_type_dvd":
                           self._vmutils._DVD_DRIVE_RES_SUB_TYPE,
                           "parent": mock_scsi_ctrl_path.replace("'", "''")})
        expected_disks = self._vmutils._conn.query.return_value

        ret_disks = self._vmutils.get_attached_disks(mock_scsi_ctrl_path)

        self._vmutils._conn.query.assert_called_once_with(expected_query)
        self.assertEqual(expected_disks, ret_disks)

    def _get_fake_instance_notes(self):
        return [self._FAKE_VM_UUID]

    def test_instance_notes(self):
        mock_vm_settings = self._lookup_vm()
        mock_vm_settings.Notes = self._get_fake_instance_notes()

        notes = self._vmutils._get_instance_notes(mock.sentinel.vm_name)

        self.assertEqual(notes[0], self._FAKE_VM_UUID)

    def test_get_event_wql_query(self):
        cls = self._vmutils._COMPUTER_SYSTEM_CLASS
        field = self._vmutils._VM_ENABLED_STATE_PROP
        timeframe = 10
        filtered_states = [constants.HYPERV_VM_STATE_ENABLED,
                           constants.HYPERV_VM_STATE_DISABLED]

        expected_checks = ' OR '.join(
            ["TargetInstance.%s = '%s'" % (field, state)
             for state in filtered_states])
        expected_query = (
            "SELECT %(field)s, TargetInstance "
            "FROM __InstanceModificationEvent "
            "WITHIN %(timeframe)s "
            "WHERE TargetInstance ISA '%(class)s' "
            "AND TargetInstance.%(field)s != "
            "PreviousInstance.%(field)s "
            "AND (%(checks)s)"
            % {'class': cls,
               'field': field,
               'timeframe': timeframe,
               'checks': expected_checks})

        query = self._vmutils._get_event_wql_query(
            cls=cls, field=field, timeframe=timeframe,
            filtered_states=filtered_states)
        self.assertEqual(expected_query, query)

    def test_get_vm_power_state_change_listener(self):
        with mock.patch.object(self._vmutils,
                               '_get_event_wql_query') as mock_get_query:
            listener = self._vmutils.get_vm_power_state_change_listener(
                timeframe=mock.sentinel.timeframe,
                filtered_states=mock.sentinel.filtered_states)

            mock_get_query.assert_called_once_with(
                cls=self._vmutils._COMPUTER_SYSTEM_CLASS,
                field=self._vmutils._VM_ENABLED_STATE_PROP,
                timeframe=mock.sentinel.timeframe,
                filtered_states=mock.sentinel.filtered_states)
            watcher = self._vmutils._conn.Msvm_ComputerSystem.watch_for
            watcher.assert_called_once_with(
                raw_wql=mock_get_query.return_value,
                fields=[self._vmutils._VM_ENABLED_STATE_PROP])

            self.assertEqual(watcher.return_value, listener)

    @mock.patch('time.sleep')
    @mock.patch.object(vmutils, 'tpool')
    @mock.patch.object(vmutils, 'patcher')
    def test_vm_power_state_change_event_handler(self, mock_patcher,
                                                 mock_tpool, mock_sleep):
        enabled_state = constants.HYPERV_VM_STATE_ENABLED
        hv_enabled_state = self._vmutils._vm_power_states_map[enabled_state]
        fake_event = mock.Mock(ElementName=mock.sentinel.vm_name,
                               EnabledState=hv_enabled_state)
        fake_callback = mock.Mock(side_effect=Exception)

        fake_listener = (
            self._vmutils._conn.Msvm_ComputerSystem.watch_for.return_value)
        mock_tpool.execute.side_effect = (exceptions.x_wmi_timed_out,
                                          fake_event, Exception,
                                          KeyboardInterrupt)

        handler = self._vmutils.get_vm_power_state_change_listener(
            get_handler=True)
        # This is supposed to run as a daemon, so we'll just cause an
        # exception in order to be able to test the method.
        self.assertRaises(KeyboardInterrupt, handler, fake_callback)

        fake_callback.assert_called_once_with(mock.sentinel.vm_name,
                                              enabled_state)
        mock_tpool.execute.assert_has_calls(
            fake_listener,
            [mock.call(constants.DEFAULT_WMI_EVENT_TIMEOUT_MS)] * 4)
        mock_sleep.assert_called_once_with(
            constants.DEFAULT_WMI_EVENT_TIMEOUT_MS / 1000)

    def _test_get_vm_generation(self, vm_gen):
        mock_settings = self._lookup_vm()
        vm_gen_string = "Microsoft:Hyper-V:SubType:" + str(vm_gen)
        mock_settings.VirtualSystemSubType = vm_gen_string

        ret = self._vmutils.get_vm_generation(mock.sentinel.FAKE_VM_NAME)

        self.assertEqual(vm_gen, ret)

    def test_get_vm_generation_gen1(self):
        self._test_get_vm_generation(constants.VM_GEN_1)

    def test_get_vm_generation_gen2(self):
        self._test_get_vm_generation(constants.VM_GEN_2)

    def test_get_vm_generation_no_attr(self):
        mock_settings = self._lookup_vm()
        mock_settings.VirtualSystemSubType.side_effect = AttributeError

        ret = self._vmutils.get_vm_generation(mock.sentinel.FAKE_VM_NAME)

        self.assertEqual(constants.VM_GEN_1, ret)

    def test_stop_vm_jobs(self):
        mock_vm = self._lookup_vm()

        self._vmutils.stop_vm_jobs(mock.sentinel.vm_name)

        self._vmutils._jobutils.stop_jobs.assert_called_once_with(
            mock_vm, None)

    def test_set_secure_boot(self):
        vs_data = mock.MagicMock()
        self._vmutils._set_secure_boot(vs_data, msft_ca_required=False)
        self.assertTrue(vs_data.SecureBootEnabled)

    def test_set_secure_boot_CA_required(self):
        self.assertRaises(exceptions.HyperVException,
                          self._vmutils._set_secure_boot,
                          mock.MagicMock(), True)

    @mock.patch.object(vmutils.VMUtils, '_modify_virtual_system')
    @mock.patch.object(vmutils.VMUtils, '_lookup_vm_check')
    def test_enable_secure_boot(self, mock_lookup_vm_check,
                                mock_modify_virtual_system):
        vs_data = mock_lookup_vm_check.return_value

        with mock.patch.object(self._vmutils,
                               '_set_secure_boot') as mock_set_secure_boot:
            self._vmutils.enable_secure_boot(
                mock.sentinel.VM_NAME, mock.sentinel.certificate_required)

            mock_lookup_vm_check.assert_called_with(mock.sentinel.VM_NAME)
            mock_set_secure_boot.assert_called_once_with(
                vs_data, mock.sentinel.certificate_required)
            mock_modify_virtual_system.assert_called_once_with(vs_data)

    def test_set_disk_qos_specs_exc(self):
        self.assertRaises(exceptions.UnsupportedOperation,
                          self._vmutils.set_disk_qos_specs,
                          mock.sentinel.disk_path, mock.sentinel.max_iops)

    def test_set_disk_qos_specs_noop(self):
        self._vmutils.set_disk_qos_specs(mock.sentinel.disk_path, 0, 0)

    @ddt.data(
        {'drive_path':
            r'\\ADCONTROLLER\root\virtualization\v2:Msvm_DiskDrive.'
            r'CreationClassName="Msvm_DiskDrive",DeviceID="Microsoft:'
            r'6344C73D-6FD6-4A74-8BE8-8EEAC2737369\\0\\0\\D",'
            r'SystemCreationClassName="Msvm_ComputerSystem"',
         'exp_phys_disk': True},
        {'drive_path': 'some_image.vhdx',
         'exp_phys_disk': False})
    @ddt.unpack
    @mock.patch.object(vmutils.VMUtils,
                       '_get_mounted_disk_resource_from_path')
    def test_drive_to_boot_source(self, mock_get_disk_res_from_path,
                                  drive_path, exp_phys_disk):
        mock_drive = mock.MagicMock()
        mock_drive.Parent = mock.sentinel.bssd
        mock_get_disk_res_from_path.return_value = mock_drive

        exp_rasd_path = (mock_drive.path_.return_value
                         if exp_phys_disk else mock_drive.Parent)
        mock_same_element = mock.MagicMock()
        self._vmutils._conn.Msvm_LogicalIdentity.return_value = [
            mock.Mock(SameElement=mock_same_element)]

        ret = self._vmutils._drive_to_boot_source(drive_path)

        self._vmutils._conn.Msvm_LogicalIdentity.assert_called_once_with(
            SystemElement=exp_rasd_path)
        mock_get_disk_res_from_path.assert_called_once_with(
            drive_path, is_physical=exp_phys_disk)
        expected_path = mock_same_element.path_.return_value
        self.assertEqual(expected_path, ret)

    @mock.patch.object(vmutils.VMUtils, '_set_boot_order_gen1')
    @mock.patch.object(vmutils.VMUtils, '_set_boot_order_gen2')
    @mock.patch.object(vmutils.VMUtils, 'get_vm_generation')
    def _test_set_boot_order(self, mock_get_vm_gen, mock_set_boot_order_gen2,
                             mock_set_boot_order_gen1, vm_gen):
        mock_get_vm_gen.return_value = vm_gen
        self._vmutils.set_boot_order(mock.sentinel.fake_vm_name,
                                     mock.sentinel.boot_order)
        if vm_gen == constants.VM_GEN_1:
            mock_set_boot_order_gen1.assert_called_once_with(
                mock.sentinel.fake_vm_name, mock.sentinel.boot_order)
        else:
            mock_set_boot_order_gen2.assert_called_once_with(
                mock.sentinel.fake_vm_name, mock.sentinel.boot_order)

    def test_set_boot_order_gen1_vm(self):
        self._test_set_boot_order(vm_gen=constants.VM_GEN_1)

    def test_set_boot_order_gen2_vm(self):
        self._test_set_boot_order(vm_gen=constants.VM_GEN_2)

    @mock.patch.object(vmutils.VMUtils, '_modify_virtual_system')
    def test_set_boot_order_gen1(self, mock_modify_virt_syst):
        mock_vssd = self._lookup_vm()

        fake_dev_boot_order = [mock.sentinel.BOOT_DEV1,
                               mock.sentinel.BOOT_DEV2]
        self._vmutils._set_boot_order_gen1(
            mock_vssd.name, fake_dev_boot_order)

        mock_modify_virt_syst.assert_called_once_with(mock_vssd)
        self.assertEqual(mock_vssd.BootOrder, tuple(fake_dev_boot_order))

    @mock.patch.object(vmutils.VMUtils, '_drive_to_boot_source')
    @mock.patch.object(vmutils.VMUtils, '_modify_virtual_system')
    def test_set_boot_order_gen2(self, mock_modify_virtual_system,
                                 mock_drive_to_boot_source):
        fake_dev_order = ['fake_boot_source1', 'fake_boot_source2']
        mock_drive_to_boot_source.side_effect = fake_dev_order
        mock_vssd = self._lookup_vm()
        old_boot_order = tuple(['fake_boot_source2',
                                'fake_boot_source1',
                                'fake_boot_source_net'])
        expected_boot_order = tuple(['FAKE_BOOT_SOURCE1',
                                     'FAKE_BOOT_SOURCE2',
                                     'FAKE_BOOT_SOURCE_NET'])
        mock_vssd.BootSourceOrder = old_boot_order

        self._vmutils._set_boot_order_gen2(mock_vssd.name, fake_dev_order)

        mock_modify_virtual_system.assert_called_once_with(mock_vssd)
        self.assertEqual(expected_boot_order, mock_vssd.BootSourceOrder)

    def test_vm_gen_1_supports_remotefx(self):
        ret = self._vmutils.vm_gen_supports_remotefx(constants.VM_GEN_1)
        self.assertTrue(ret)

    def test_vm_gen_2_supports_remotefx(self):
        ret = self._vmutils.vm_gen_supports_remotefx(constants.VM_GEN_2)
        self.assertFalse(ret)

    def test_validate_remotefx_monitor_count(self):
        self.assertRaises(exceptions.HyperVRemoteFXException,
                          self._vmutils._validate_remotefx_params,
                          10, constants.REMOTEFX_MAX_RES_1024x768)

    def test_validate_remotefx_max_resolution(self):
        self.assertRaises(exceptions.HyperVRemoteFXException,
                          self._vmutils._validate_remotefx_params,
                          1, '1024x700')

    @ddt.data(True, False)
    @mock.patch.object(vmutils.VMUtils, '_set_remotefx_vram')
    @mock.patch.object(vmutils.VMUtils, '_get_new_resource_setting_data')
    def test_set_remotefx_display_controller(self, new_obj, mock_get_new_rsd,
                                             mock_set_remotefx_vram):
        if new_obj:
            remotefx_ctrl_res = None
            expected_res = mock_get_new_rsd.return_value
        else:
            remotefx_ctrl_res = mock.MagicMock()
            expected_res = remotefx_ctrl_res

        self._vmutils._set_remotefx_display_controller(
            mock.sentinel.fake_vm, remotefx_ctrl_res,
            mock.sentinel.monitor_count, mock.sentinel.max_resolution,
            mock.sentinel.vram_bytes)

        self.assertEqual(mock.sentinel.monitor_count,
                         expected_res.MaximumMonitors)
        self.assertEqual(mock.sentinel.max_resolution,
                         expected_res.MaximumScreenResolution)
        mock_set_remotefx_vram.assert_called_once_with(
            expected_res, mock.sentinel.vram_bytes)

        if new_obj:
            mock_get_new_rsd.assert_called_once_with(
                self._vmutils._REMOTEFX_DISP_CTRL_RES_SUB_TYPE,
                self._vmutils._REMOTEFX_DISP_ALLOCATION_SETTING_DATA_CLASS)
            self._vmutils._jobutils.add_virt_resource.assert_called_once_with(
                expected_res, mock.sentinel.fake_vm)
        else:
            self.assertFalse(mock_get_new_rsd.called)
            modify_virt_res = self._vmutils._jobutils.modify_virt_resource
            modify_virt_res.assert_called_once_with(expected_res)

    def test_set_remotefx_vram(self):
        self._vmutils._set_remotefx_vram(mock.sentinel.remotefx_ctrl_res,
                                         mock.sentinel.vram_bytes)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(vmutils.VMUtils, '_set_remotefx_display_controller')
    @mock.patch.object(vmutils.VMUtils, '_vm_has_s3_controller')
    def test_enable_remotefx_video_adapter(self,
                                           mock_vm_has_s3_controller,
                                           mock_set_remotefx_ctrl,
                                           mock_get_element_associated_class):
        mock_vm = self._lookup_vm()

        mock_r1 = mock.MagicMock()
        mock_r1.ResourceSubType = self._vmutils._SYNTH_DISP_CTRL_RES_SUB_TYPE

        mock_r2 = mock.MagicMock()
        mock_r2.ResourceSubType = self._vmutils._S3_DISP_CTRL_RES_SUB_TYPE

        mock_get_element_associated_class.return_value = [mock_r1, mock_r2]

        self._vmutils.enable_remotefx_video_adapter(
            mock.sentinel.fake_vm_name,
            self._FAKE_MONITOR_COUNT,
            constants.REMOTEFX_MAX_RES_1024x768)

        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn,
            self._vmutils._CIM_RES_ALLOC_SETTING_DATA_CLASS,
            element_instance_id=mock_vm.InstanceID)
        self._vmutils._jobutils.remove_virt_resource.assert_called_once_with(
            mock_r1)

        mock_set_remotefx_ctrl.assert_called_once_with(
            mock_vm, None, self._FAKE_MONITOR_COUNT,
            self._vmutils._remote_fx_res_map[
                constants.REMOTEFX_MAX_RES_1024x768],
            None)

        self._vmutils._jobutils.modify_virt_resource.assert_called_once_with(
            mock_r2)
        self.assertEqual(self._vmutils._DISP_CTRL_ADDRESS_DX_11,
                         mock_r2.Address)

    @mock.patch.object(vmutils.VMUtils, '_vm_has_s3_controller')
    @mock.patch.object(vmutils.VMUtils, '_get_new_resource_setting_data')
    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_disable_remotefx_video_adapter(self,
                                            mock_get_element_associated_class,
                                            mock_get_new_rsd,
                                            mock_vm_has_s3_controller):
        mock_vm = self._lookup_vm()
        mock_r1 = mock.MagicMock(
            ResourceSubType=self._vmutils._REMOTEFX_DISP_CTRL_RES_SUB_TYPE)
        mock_r2 = mock.MagicMock(
            ResourceSubType=self._vmutils._S3_DISP_CTRL_RES_SUB_TYPE)

        mock_get_element_associated_class.return_value = [mock_r1, mock_r2]

        self._vmutils.disable_remotefx_video_adapter(
            mock.sentinel.fake_vm_name)

        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn,
            self._vmutils._CIM_RES_ALLOC_SETTING_DATA_CLASS,
            element_instance_id=mock_vm.InstanceID)
        self._vmutils._jobutils.remove_virt_resource.assert_called_once_with(
            mock_r1)
        mock_get_new_rsd.assert_called_once_with(
            self._vmutils._SYNTH_DISP_CTRL_RES_SUB_TYPE,
            self._vmutils._SYNTH_DISP_ALLOCATION_SETTING_DATA_CLASS)
        self._vmutils._jobutils.add_virt_resource.assert_called_once_with(
            mock_get_new_rsd.return_value, mock_vm)
        self._vmutils._jobutils.modify_virt_resource.assert_called_once_with(
            mock_r2)
        self.assertEqual(self._vmutils._DISP_CTRL_ADDRESS, mock_r2.Address)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_disable_remotefx_video_adapter_not_found(
            self, mock_get_element_associated_class):
        mock_vm = self._lookup_vm()
        mock_get_element_associated_class.return_value = []

        self._vmutils.disable_remotefx_video_adapter(
            mock.sentinel.fake_vm_name)

        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn,
            self._vmutils._CIM_RES_ALLOC_SETTING_DATA_CLASS,
            element_instance_id=mock_vm.InstanceID)
        self.assertFalse(self._vmutils._jobutils.remove_virt_resource.called)

    @mock.patch.object(vmutils.VMUtils, 'get_vm_generation')
    def test_vm_has_s3_controller(self, mock_get_vm_generation):
        self.assertTrue(self._vmutils._vm_has_s3_controller(
            mock.sentinel.fake_vm_name))

    @mock.patch.object(vmutils.VMUtils, '_get_mounted_disk_resource_from_path')
    def test_update_vm_disk_path(self, mock_get_disk_resource_from_path):
        disk_resource = mock_get_disk_resource_from_path.return_value
        self._vmutils.update_vm_disk_path(mock.sentinel.disk_path,
                                          mock.sentinel.new_path,
                                          is_physical=True)

        mock_get_disk_resource_from_path.assert_called_once_with(
            disk_path=mock.sentinel.disk_path, is_physical=True)
        self._vmutils._jobutils.modify_virt_resource.assert_called_once_with(
            disk_resource)
        self.assertEqual(disk_resource.HostResource, [mock.sentinel.new_path])

    def test_add_pci_device(self):
        self.assertRaises(NotImplementedError,
                          self._vmutils.add_pci_device,
                          mock.sentinel.vm_name, mock.sentinel.vendor_id,
                          mock.sentinel.product_id)

    def test_remove_pci_device(self):
        self.assertRaises(NotImplementedError,
                          self._vmutils.remove_pci_device,
                          mock.sentinel.vm_name, mock.sentinel.vendor_id,
                          mock.sentinel.product_id)

    def test_remove_all_pci_devices(self):
        self._vmutils.remove_all_pci_devices(mock.sentinel.vm_name)

    def test_populate_fsk(self):
        self.assertRaises(NotImplementedError,
                          self._vmutils.populate_fsk,
                          mock.sentinel.fsk_filepath,
                          mock.sentinel.fsk_pairs)

    def test_add_vtpm(self):
        self.assertRaises(NotImplementedError,
                          self._vmutils.add_vtpm,
                          mock.sentinel.vm_name, mock.sentinel.pdk_filepath,
                          mock.sentinel.shielded)

    def test_provision_vm(self):
        self.assertRaises(NotImplementedError,
                          self._vmutils.provision_vm,
                          mock.sentinel.vm_name, mock.sentinel.fsk_filepath,
                          mock.sentinel.pdk_filepath)


class VMUtils6_3TestCase(test_base.OsWinBaseTestCase):

    def setUp(self):
        super(VMUtils6_3TestCase, self).setUp()
        self._vmutils = vmutils.VMUtils6_3()
        self._vmutils._conn_attr = mock.MagicMock()
        self._vmutils._jobutils = mock.MagicMock()

    @mock.patch.object(vmutils.VMUtils,
                       '_get_mounted_disk_resource_from_path')
    def test_set_disk_qos_specs(self, mock_get_disk_resource):
        mock_disk = mock_get_disk_resource.return_value

        self._vmutils.set_disk_qos_specs(mock.sentinel.disk_path,
                                         max_iops=mock.sentinel.max_iops,
                                         min_iops=mock.sentinel.min_iops)

        mock_get_disk_resource.assert_called_once_with(
            mock.sentinel.disk_path, is_physical=False)
        self.assertEqual(mock.sentinel.max_iops, mock_disk.IOPSLimit)
        self.assertEqual(mock.sentinel.min_iops, mock_disk.IOPSReservation)
        self._vmutils._jobutils.modify_virt_resource.assert_called_once_with(
            mock_disk)

    @mock.patch.object(vmutils.VMUtils,
                       '_get_mounted_disk_resource_from_path')
    def test_set_disk_qos_specs_missing_values(self, mock_get_disk_resource):
        self._vmutils.set_disk_qos_specs(mock.sentinel.disk_path)

        self.assertFalse(mock_get_disk_resource.called)
