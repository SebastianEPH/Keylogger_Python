#  Copyright 2014 Hewlett-Packard Development Company, L.P.
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
from os_win.utils import hostutils


class FakeCPUSpec(object):
    """Fake CPU Spec for unit tests."""

    Architecture = mock.sentinel.cpu_arch
    Name = mock.sentinel.cpu_name
    Manufacturer = mock.sentinel.cpu_man
    MaxClockSpeed = mock.sentinel.max_clock_speed
    NumberOfCores = mock.sentinel.cpu_cores
    NumberOfLogicalProcessors = mock.sentinel.cpu_procs


class HostUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V hostutils class."""

    _DEVICE_ID = "Microsoft:UUID\\0\\0"
    _NODE_ID = "Microsoft:PhysicalNode\\0"

    _FAKE_MEMORY_TOTAL = 1024
    _FAKE_MEMORY_FREE = 512
    _FAKE_DISK_SIZE = 1024
    _FAKE_DISK_FREE = 512
    _FAKE_VERSION_GOOD = '6.2.0'
    _FAKE_VERSION_BAD = '6.1.9'

    def setUp(self):
        self._hostutils = hostutils.HostUtils()
        self._hostutils._conn_cimv2 = mock.MagicMock()
        self._hostutils._conn_scimv2 = mock.MagicMock()
        self._hostutils._conn_attr = mock.MagicMock()
        self._hostutils._netutils_prop = mock.MagicMock()
        self._conn = self._hostutils._conn
        self._conn_scimv2 = self._hostutils._conn_scimv2
        self._netutils = self._hostutils._netutils

        super(HostUtilsTestCase, self).setUp()

    @mock.patch('os_win.utilsfactory.get_networkutils')
    def test_netutils(self, mock_get_networkutils):
        self._hostutils._netutils_prop = None
        self.assertEqual(self._hostutils._netutils,
                         mock_get_networkutils.return_value)

    @mock.patch('os_win.utils.hostutils.kernel32')
    def test_get_host_tick_count64(self, mock_kernel32):
        tick_count64 = "100"
        mock_kernel32.GetTickCount64.return_value = tick_count64
        response = self._hostutils.get_host_tick_count64()
        self.assertEqual(tick_count64, response)

    def test_get_cpus_info(self):
        cpu = mock.MagicMock(spec=FakeCPUSpec)
        self._hostutils._conn_cimv2.query.return_value = [cpu]
        cpu_list = self._hostutils.get_cpus_info()
        self.assertEqual([cpu._mock_children], cpu_list)

    def test_get_memory_info(self):
        memory = mock.MagicMock()
        type(memory).TotalVisibleMemorySize = mock.PropertyMock(
            return_value=self._FAKE_MEMORY_TOTAL)
        type(memory).FreePhysicalMemory = mock.PropertyMock(
            return_value=self._FAKE_MEMORY_FREE)

        self._hostutils._conn_cimv2.query.return_value = [memory]
        total_memory, free_memory = self._hostutils.get_memory_info()

        self.assertEqual(self._FAKE_MEMORY_TOTAL, total_memory)
        self.assertEqual(self._FAKE_MEMORY_FREE, free_memory)

    def test_get_volume_info(self):
        disk = mock.MagicMock()
        type(disk).Size = mock.PropertyMock(return_value=self._FAKE_DISK_SIZE)
        type(disk).FreeSpace = mock.PropertyMock(
            return_value=self._FAKE_DISK_FREE)

        self._hostutils._conn_cimv2.query.return_value = [disk]
        (total_memory, free_memory) = self._hostutils.get_volume_info(
            mock.sentinel.FAKE_DRIVE)

        self.assertEqual(self._FAKE_DISK_SIZE, total_memory)
        self.assertEqual(self._FAKE_DISK_FREE, free_memory)

    def test_check_min_windows_version_true(self):
        self._test_check_min_windows_version(self._FAKE_VERSION_GOOD, True)

    def test_check_min_windows_version_false(self):
        self._test_check_min_windows_version(self._FAKE_VERSION_BAD, False)

    def _test_check_min_windows_version(self, version, expected):
        os = mock.MagicMock()
        os.Version = version
        self._hostutils._conn_cimv2.Win32_OperatingSystem.return_value = [os]
        hostutils.HostUtils._windows_version = None
        self.assertEqual(expected,
                         self._hostutils.check_min_windows_version(6, 2))

    def test_get_windows_version(self):
        os = mock.MagicMock()
        os.Version = self._FAKE_VERSION_GOOD
        self._hostutils._conn_cimv2.Win32_OperatingSystem.return_value = [os]
        hostutils.HostUtils._windows_version = None
        self.assertEqual(self._FAKE_VERSION_GOOD,
                         self._hostutils.get_windows_version())

    @mock.patch('socket.gethostname')
    @mock.patch('os_win._utils.get_ips')
    def test_get_local_ips(self, mock_get_ips, mock_gethostname):
        local_ips = self._hostutils.get_local_ips()

        self.assertEqual(mock_get_ips.return_value, local_ips)
        mock_gethostname.assert_called_once_with()
        mock_get_ips.assert_called_once_with(mock_gethostname.return_value)

    def _test_host_power_action(self, action):
        fake_win32 = mock.MagicMock()
        fake_win32.Win32Shutdown = mock.MagicMock()

        self._hostutils._conn_cimv2.Win32_OperatingSystem.return_value = [
            fake_win32]

        if action == constants.HOST_POWER_ACTION_SHUTDOWN:
            self._hostutils.host_power_action(action)
            fake_win32.Win32Shutdown.assert_called_with(
                self._hostutils._HOST_FORCED_SHUTDOWN)
        elif action == constants.HOST_POWER_ACTION_REBOOT:
            self._hostutils.host_power_action(action)
            fake_win32.Win32Shutdown.assert_called_with(
                self._hostutils._HOST_FORCED_REBOOT)
        else:
            self.assertRaises(NotImplementedError,
                              self._hostutils.host_power_action, action)

    def test_host_shutdown(self):
        self._test_host_power_action(constants.HOST_POWER_ACTION_SHUTDOWN)

    def test_host_reboot(self):
        self._test_host_power_action(constants.HOST_POWER_ACTION_REBOOT)

    def test_host_startup(self):
        self._test_host_power_action(constants.HOST_POWER_ACTION_STARTUP)

    def test_get_supported_vm_types_2012_r2(self):
        with mock.patch.object(self._hostutils,
                               'check_min_windows_version') as mock_check_win:
            mock_check_win.return_value = True
            result = self._hostutils.get_supported_vm_types()
            self.assertEqual([constants.IMAGE_PROP_VM_GEN_1,
                              constants.IMAGE_PROP_VM_GEN_2], result)

    def test_get_supported_vm_types(self):
        with mock.patch.object(self._hostutils,
                               'check_min_windows_version') as mock_check_win:
            mock_check_win.return_value = False
            result = self._hostutils.get_supported_vm_types()
            self.assertEqual([constants.IMAGE_PROP_VM_GEN_1], result)

    def test_check_server_feature(self):
        mock_sv_feature_cls = self._hostutils._conn_cimv2.Win32_ServerFeature
        mock_sv_feature_cls.return_value = [mock.sentinel.sv_feature]

        feature_enabled = self._hostutils.check_server_feature(
            mock.sentinel.feature_id)
        self.assertTrue(feature_enabled)

        mock_sv_feature_cls.assert_called_once_with(
            ID=mock.sentinel.feature_id)

    def test_get_nic_sriov_vfs(self):
        mock_vswitch_sd = mock.Mock()
        mock_hw_offload_sd_bad = mock.Mock(IovVfCapacity=0)
        mock_hw_offload_sd_ok = mock.Mock()
        vswitch_sds_class = self._conn.Msvm_VirtualEthernetSwitchSettingData
        vswitch_sds_class.return_value = [mock_vswitch_sd] * 3
        self._conn.Msvm_EthernetSwitchHardwareOffloadData.side_effect = [
            [mock_hw_offload_sd_bad], [mock_hw_offload_sd_ok],
            [mock_hw_offload_sd_ok]]
        self._netutils.get_vswitch_external_network_name.side_effect = [
            None, mock.sentinel.nic_name]
        mock_nic = mock.Mock()
        self._conn_scimv2.MSFT_NetAdapter.return_value = [mock_nic]

        vfs = self._hostutils.get_nic_sriov_vfs()

        expected = {
            'vswitch_name': mock_vswitch_sd.ElementName,
            'device_id': mock_nic.PnPDeviceID,
            'total_vfs': mock_hw_offload_sd_ok.IovVfCapacity,
            'used_vfs': mock_hw_offload_sd_ok.IovVfUsage,
        }
        self.assertEqual([expected], vfs)
        vswitch_sds_class.assert_called_once_with(IOVPreferred=True)
        self._conn.Msvm_EthernetSwitchHardwareOffloadData.assert_has_calls([
            mock.call(SystemName=mock_vswitch_sd.VirtualSystemIdentifier)] * 3)
        self._netutils.get_vswitch_external_network_name.assert_has_calls([
            mock.call(mock_vswitch_sd.ElementName)] * 2)
        self._conn_scimv2.MSFT_NetAdapter.assert_called_once_with(
            InterfaceDescription=mock.sentinel.nic_name)

    @mock.patch.object(hostutils.HostUtils, '_get_nic_hw_offload_info')
    def test_get_nic_hardware_offload_info(self, mock_get_nic_offload):
        mock_vswitch_sd = mock.Mock(VirtualSystemIdentifier=mock.sentinel.vsid)
        mock_hw_offload_sd = mock.Mock(SystemName=mock.sentinel.vsid)

        vswitch_sds_class = self._conn.Msvm_VirtualEthernetSwitchSettingData
        vswitch_sds_class.return_value = [mock_vswitch_sd]
        hw_offload_class = self._conn.Msvm_EthernetSwitchHardwareOffloadData
        hw_offload_class.return_value = [mock_hw_offload_sd]

        hw_offload_info = self._hostutils.get_nic_hardware_offload_info()

        self.assertEqual([mock_get_nic_offload.return_value], hw_offload_info)
        vswitch_sds_class.assert_called_once_with()
        hw_offload_class.assert_called_once_with()
        mock_get_nic_offload.assert_called_once_with(mock_vswitch_sd,
                                                     mock_hw_offload_sd)

    def test_get_nic_hardware_offload_info_no_nic(self):
        self._netutils.get_vswitch_external_network_name.return_value = None
        mock_vswitch_sd = mock.Mock()

        hw_offload_info = self._hostutils._get_nic_hw_offload_info(
            mock_vswitch_sd, mock.sentinel.hw_offload_sd)

        self.assertIsNone(hw_offload_info)

    @mock.patch.object(hostutils.LOG, 'warning')
    def test_get_nic_hw_offload_info(self, mock_warning):
        mock_vswitch_sd = mock.Mock()
        mock_hw_offload_sd = mock.Mock(IovVfCapacity=0)
        mock_nic = mock.Mock()
        self._conn_scimv2.MSFT_NetAdapter.return_value = [mock_nic]

        hw_offload_info = self._hostutils._get_nic_hw_offload_info(
            mock_vswitch_sd, mock_hw_offload_sd)

        expected = {
            'vswitch_name': mock_vswitch_sd.ElementName,
            'device_id': mock_nic.PnPDeviceID,
            'total_vfs': mock_hw_offload_sd.IovVfCapacity,
            'used_vfs': mock_hw_offload_sd.IovVfUsage,
            'total_iov_queue_pairs': mock_hw_offload_sd.IovQueuePairCapacity,
            'used_iov_queue_pairs': mock_hw_offload_sd.IovQueuePairUsage,
            'total_vmqs': mock_hw_offload_sd.VmqCapacity,
            'used_vmqs': mock_hw_offload_sd.VmqUsage,
            'total_ipsecsa': mock_hw_offload_sd.IPsecSACapacity,
            'used_ipsecsa': mock_hw_offload_sd.IPsecSAUsage,
        }
        self.assertEqual(expected, hw_offload_info)
        get_ext_net_name = self._netutils.get_vswitch_external_network_name
        get_ext_net_name.assert_called_once_with(mock_vswitch_sd.ElementName)
        self.assertTrue(mock_warning.called)
        self._conn_scimv2.MSFT_NetAdapter.assert_called_once_with(
            InterfaceDescription=get_ext_net_name.return_value)

    def _check_get_numa_nodes_missing_info(self):
        numa_node = mock.MagicMock()
        self._hostutils._conn.Msvm_NumaNode.return_value = [
            numa_node, numa_node]

        nodes_info = self._hostutils.get_numa_nodes()
        self.assertEqual([], nodes_info)

    @mock.patch.object(hostutils.HostUtils, '_get_numa_memory_info')
    def test_get_numa_nodes_missing_memory_info(self, mock_get_memory_info):
        mock_get_memory_info.return_value = None
        self._check_get_numa_nodes_missing_info()

    @mock.patch.object(hostutils.HostUtils, '_get_numa_cpu_info')
    @mock.patch.object(hostutils.HostUtils, '_get_numa_memory_info')
    def test_get_numa_nodes_missing_cpu_info(self, mock_get_memory_info,
                                             mock_get_cpu_info):
        mock_get_cpu_info.return_value = None
        self._check_get_numa_nodes_missing_info()

    @mock.patch.object(hostutils.HostUtils, '_get_numa_cpu_info')
    @mock.patch.object(hostutils.HostUtils, '_get_numa_memory_info')
    def test_get_numa_nodes(self, mock_get_memory_info, mock_get_cpu_info):
        numa_memory = mock_get_memory_info.return_value
        host_cpu = mock.MagicMock(DeviceID=self._DEVICE_ID)
        mock_get_cpu_info.return_value = [host_cpu]
        numa_node = mock.MagicMock(NodeID=self._NODE_ID)
        self._hostutils._conn.Msvm_NumaNode.return_value = [
            numa_node, numa_node]

        nodes_info = self._hostutils.get_numa_nodes()

        expected_info = {
            'id': self._DEVICE_ID.split('\\')[-1],
            'memory': numa_memory.NumberOfBlocks,
            'memory_usage': numa_node.CurrentlyConsumableMemoryBlocks,
            'cpuset': set([self._DEVICE_ID.split('\\')[-1]]),
            'cpu_usage': 0,
        }

        self.assertEqual([expected_info, expected_info], nodes_info)

    def test_get_numa_memory_info(self):
        system_memory = mock.MagicMock()
        system_memory.path_.return_value = 'fake_wmi_obj_path'
        numa_node_memory = mock.MagicMock()
        numa_node_memory.path_.return_value = 'fake_wmi_obj_path1'
        numa_node_assoc = [system_memory]
        memory_info = self._hostutils._get_numa_memory_info(
            numa_node_assoc, [system_memory, numa_node_memory])

        self.assertEqual(system_memory, memory_info)

    def test_get_numa_memory_info_not_found(self):
        other = mock.MagicMock()
        memory_info = self._hostutils._get_numa_memory_info([], [other])

        self.assertIsNone(memory_info)

    def test_get_numa_cpu_info(self):
        host_cpu = mock.MagicMock()
        host_cpu.path_.return_value = 'fake_wmi_obj_path'
        vm_cpu = mock.MagicMock()
        vm_cpu.path_.return_value = 'fake_wmi_obj_path1'
        numa_node_assoc = [host_cpu]
        cpu_info = self._hostutils._get_numa_cpu_info(numa_node_assoc,
                                                      [host_cpu, vm_cpu])

        self.assertEqual([host_cpu], cpu_info)

    def test_get_numa_cpu_info_not_found(self):
        other = mock.MagicMock()
        cpu_info = self._hostutils._get_numa_cpu_info([], [other])

        self.assertEqual([], cpu_info)

    def test_get_remotefx_gpu_info(self):
        fake_gpu = mock.MagicMock()
        fake_gpu.Name = mock.sentinel.Fake_gpu_name
        fake_gpu.TotalVideoMemory = mock.sentinel.Fake_gpu_total_memory
        fake_gpu.AvailableVideoMemory = mock.sentinel.Fake_gpu_available_memory
        fake_gpu.DirectXVersion = mock.sentinel.Fake_gpu_directx
        fake_gpu.DriverVersion = mock.sentinel.Fake_gpu_driver_version

        mock_phys_3d_proc = (
            self._hostutils._conn.Msvm_Physical3dGraphicsProcessor)
        mock_phys_3d_proc.return_value = [fake_gpu]

        return_gpus = self._hostutils.get_remotefx_gpu_info()
        self.assertEqual(mock.sentinel.Fake_gpu_name, return_gpus[0]['name'])
        self.assertEqual(mock.sentinel.Fake_gpu_driver_version,
                         return_gpus[0]['driver_version'])
        self.assertEqual(mock.sentinel.Fake_gpu_total_memory,
                         return_gpus[0]['total_video_ram'])
        self.assertEqual(mock.sentinel.Fake_gpu_available_memory,
                         return_gpus[0]['available_video_ram'])
        self.assertEqual(mock.sentinel.Fake_gpu_directx,
                         return_gpus[0]['directx_version'])

    def _set_verify_host_remotefx_capability_mocks(self, isGpuCapable=True,
                                                   isSlatCapable=True):
        s3d_video_pool = self._hostutils._conn.Msvm_Synth3dVideoPool()[0]
        s3d_video_pool.IsGpuCapable = isGpuCapable
        s3d_video_pool.IsSlatCapable = isSlatCapable

    def test_verify_host_remotefx_capability_unsupported_gpu(self):
        self._set_verify_host_remotefx_capability_mocks(isGpuCapable=False)
        self.assertRaises(exceptions.HyperVRemoteFXException,
                          self._hostutils.verify_host_remotefx_capability)

    def test_verify_host_remotefx_capability_no_slat(self):
        self._set_verify_host_remotefx_capability_mocks(isSlatCapable=False)
        self.assertRaises(exceptions.HyperVRemoteFXException,
                          self._hostutils.verify_host_remotefx_capability)

    def test_verify_host_remotefx_capability(self):
        self._set_verify_host_remotefx_capability_mocks()
        self._hostutils.verify_host_remotefx_capability()

    def test_supports_nested_virtualization(self):
        self.assertFalse(self._hostutils.supports_nested_virtualization())

    def test_get_pci_passthrough_devices(self):
        self.assertEqual([], self._hostutils.get_pci_passthrough_devices())
