# Copyright 2013 Cloudbase Solutions Srl
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

import socket

from oslo_log import log as logging

from os_win._i18n import _
from os_win import _utils
from os_win import constants
from os_win import exceptions
from os_win.utils import baseutils
from os_win.utils.winapi import libs as w_lib

kernel32 = w_lib.get_shared_lib_handle(w_lib.KERNEL32)

LOG = logging.getLogger(__name__)


class HostUtils(baseutils.BaseUtilsVirt):

    _windows_version = None

    _MSVM_PROCESSOR = 'Msvm_Processor'
    _MSVM_MEMORY = 'Msvm_Memory'
    _MSVM_NUMA_NODE = 'Msvm_NumaNode'

    _CENTRAL_PROCESSOR = 'Central Processor'

    _HOST_FORCED_REBOOT = 6
    _HOST_FORCED_SHUTDOWN = 12
    _DEFAULT_VM_GENERATION = constants.IMAGE_PROP_VM_GEN_1

    FEATURE_RDS_VIRTUALIZATION = 322
    FEATURE_MPIO = 57

    _wmi_cimv2_namespace = '//./root/cimv2'
    _wmi_standard_cimv2_namespace = '//./root/StandardCimv2'

    def __init__(self, host='.'):
        super(HostUtils, self).__init__(host)
        self._conn_cimv2 = self._get_wmi_conn(self._wmi_cimv2_namespace,
                                              privileges=["Shutdown"])
        self._conn_scimv2 = self._get_wmi_conn(
            self._wmi_standard_cimv2_namespace)
        self._netutils_prop = None

    @property
    def _netutils(self):
        if not self._netutils_prop:
            # NOTE(claudiub): we're importing utilsfactory here in order to
            # avoid circular dependencies.
            from os_win import utilsfactory
            self._netutils_prop = utilsfactory.get_networkutils()

        return self._netutils_prop

    def get_cpus_info(self):
        """Returns dictionary containing information about the host's CPUs."""
        # NOTE(abalutoiu): Specifying exactly the fields that we need
        # improves the speed of the query. The LoadPercentage field
        # is the load capacity of each processor averaged to the last
        # second, which is time wasted.
        cpus = self._conn_cimv2.query(
            "SELECT Architecture, Name, Manufacturer, MaxClockSpeed, "
            "NumberOfCores, NumberOfLogicalProcessors FROM Win32_Processor "
            "WHERE ProcessorType = 3")
        cpus_list = []
        for cpu in cpus:
            cpu_info = {'Architecture': cpu.Architecture,
                        'Name': cpu.Name,
                        'Manufacturer': cpu.Manufacturer,
                        'MaxClockSpeed': cpu.MaxClockSpeed,
                        'NumberOfCores': cpu.NumberOfCores,
                        'NumberOfLogicalProcessors':
                        cpu.NumberOfLogicalProcessors}
            cpus_list.append(cpu_info)
        return cpus_list

    def is_cpu_feature_present(self, feature_key):
        """Checks if the host's CPUs have the given feature."""
        return kernel32.IsProcessorFeaturePresent(feature_key)

    def get_memory_info(self):
        """Returns a tuple with total visible memory and free physical memory.

        The returned values are expressed in KB.
        """

        mem_info = self._conn_cimv2.query("SELECT TotalVisibleMemorySize, "
                                          "FreePhysicalMemory "
                                          "FROM win32_operatingsystem")[0]
        return (int(mem_info.TotalVisibleMemorySize),
                int(mem_info.FreePhysicalMemory))

    # TODO(atuvenie) This method should be removed once all the callers have
    # changed to use the get_disk_capacity method from diskutils.
    def get_volume_info(self, drive):
        """Returns a tuple with total size and free space of the given drive.

        Returned values are expressed in bytes.

        :param drive: the drive letter of the logical disk whose information
            is required.
        """

        logical_disk = self._conn_cimv2.query("SELECT Size, FreeSpace "
                                              "FROM win32_logicaldisk "
                                              "WHERE DeviceID='%s'"
                                              % drive)[0]
        return (int(logical_disk.Size), int(logical_disk.FreeSpace))

    def check_min_windows_version(self, major, minor, build=0):
        """Compares the host's kernel version with the given version.

        :returns: True if the host's kernel version is higher or equal to
            the given version.
        """
        version_str = self.get_windows_version()
        return list(map(int, version_str.split('.'))) >= [major, minor, build]

    def get_windows_version(self):
        """Returns a string representing the host's kernel version."""
        if not HostUtils._windows_version:
            Win32_OperatingSystem = self._conn_cimv2.Win32_OperatingSystem()[0]
            HostUtils._windows_version = Win32_OperatingSystem.Version
        return HostUtils._windows_version

    def get_local_ips(self):
        """Returns the list of locally assigned IPs."""
        hostname = socket.gethostname()
        return _utils.get_ips(hostname)

    def get_host_tick_count64(self):
        """Returns host uptime in milliseconds."""
        return kernel32.GetTickCount64()

    def host_power_action(self, action):
        win32_os = self._conn_cimv2.Win32_OperatingSystem()[0]

        if action == constants.HOST_POWER_ACTION_SHUTDOWN:
            win32_os.Win32Shutdown(self._HOST_FORCED_SHUTDOWN)
        elif action == constants.HOST_POWER_ACTION_REBOOT:
            win32_os.Win32Shutdown(self._HOST_FORCED_REBOOT)
        else:
            raise NotImplementedError(
                _("Host %(action)s is not supported by the Hyper-V driver") %
                {"action": action})

    def get_supported_vm_types(self):
        """Get the supported Hyper-V VM generations.

        Hyper-V Generation 2 VMs are supported in Windows 8.1,
        Windows Server / Hyper-V Server 2012 R2 or newer.

        :returns: array of supported VM generations (ex. ['hyperv-gen1'])
        """

        if self.check_min_windows_version(6, 3):
            return [constants.IMAGE_PROP_VM_GEN_1,
                    constants.IMAGE_PROP_VM_GEN_2]
        else:
            return [constants.IMAGE_PROP_VM_GEN_1]

    def get_default_vm_generation(self):
        return self._DEFAULT_VM_GENERATION

    def check_server_feature(self, feature_id):
        """Checks if the given feature exists on the host."""
        return len(self._conn_cimv2.Win32_ServerFeature(ID=feature_id)) > 0

    def get_nic_sriov_vfs(self):
        """Get host's NIC SR-IOV VFs.

        This method will ignore the vSwitches which do not have SR-IOV enabled,
        or which are poorly configured (the NIC does not support SR-IOV).

        :returns: a list of dictionaries, containing the following fields:
            - 'vswitch_name': the vSwtch name.
            - 'total_vfs': the vSwitch's maximum number of VFs. (> 0)
            - 'used_vfs': the vSwitch's number of used VFs. (<= 'total_vfs')
        """

        # TODO(claudiub): We have added a different method that returns all
        # of the offloading capabilities available, including SR-IOV.
        # Remove this method in S.

        vfs = []

        # NOTE(claudiub): A vSwitch will have to be configured to enable
        # SR-IOV, otherwise its IOVPreferred flag will be False.
        vswitch_sds = self._conn.Msvm_VirtualEthernetSwitchSettingData(
            IOVPreferred=True)
        for vswitch_sd in vswitch_sds:
            hw_offload = self._conn.Msvm_EthernetSwitchHardwareOffloadData(
                SystemName=vswitch_sd.VirtualSystemIdentifier)[0]
            if not hw_offload.IovVfCapacity:
                LOG.warning("VSwitch %s has SR-IOV enabled, but it is not "
                            "supported by the NIC or by the OS.",
                            vswitch_sd.ElementName)
                continue

            nic_name = self._netutils.get_vswitch_external_network_name(
                vswitch_sd.ElementName)
            if not nic_name:
                # NOTE(claudiub): This can happen if the vSwitch is not
                # external.
                LOG.warning("VSwitch %s is not external.",
                            vswitch_sd.ElementName)
                continue

            nic = self._conn_scimv2.MSFT_NetAdapter(
                InterfaceDescription=nic_name)[0]

            vfs.append({
                'vswitch_name': vswitch_sd.ElementName,
                'device_id': nic.PnPDeviceID,
                'total_vfs': hw_offload.IovVfCapacity,
                'used_vfs': hw_offload.IovVfUsage,
            })

        return vfs

    def get_nic_hardware_offload_info(self):
        """Get host's NIC hardware offload information.

        Hyper-V offers a few different hardware offloading options for VMs and
        their vNICs, depending on the vSwitches' NICs hardware resources and
        capabilities. These resources are managed and assigned automatically by
        Hyper-V. These resources are: VFs, IOV queue pairs, VMQs, IPsec
        security association offloads.

        :returns: a list of dictionaries, containing the following fields:
            - 'vswitch_name': the switch name.
            - 'device_id': the switch's physical NIC's PnP device ID.
            - 'total_vfs': the switch's maximum number of VFs. (>= 0)
            - 'used_vfs': the switch's number of used VFs. (<= 'total_vfs')
            - 'total_iov_queue_pairs': the switch's maximum number of IOV
                queue pairs. (>= 'total_vfs')
            - 'used_iov_queue_pairs': the switch's number of used IOV queue
                pairs (<= 'total_iov_queue_pairs')
            - 'total_vmqs': the switch's maximum number of VMQs. (>= 0)
            - 'used_vmqs': the switch's number of used VMQs. (<= 'total_vmqs')
            - 'total_ipsecsa': the maximum number of IPsec SA offloads
                supported by the switch. (>= 0)
            - 'used_ipsecsa': the switch's number of IPsec SA offloads
                currently in use. (<= 'total_ipsecsa')
        """

        hw_offload_data = []

        vswitch_sds = self._conn.Msvm_VirtualEthernetSwitchSettingData()
        hw_offload_sds = self._conn.Msvm_EthernetSwitchHardwareOffloadData()
        for vswitch_sd in vswitch_sds:
            hw_offload = [
                s for s in hw_offload_sds if
                s.SystemName == vswitch_sd.VirtualSystemIdentifier][0]

            vswitch_offload_data = self._get_nic_hw_offload_info(
                vswitch_sd, hw_offload)
            if vswitch_offload_data:
                hw_offload_data.append(vswitch_offload_data)

        return hw_offload_data

    def _get_nic_hw_offload_info(self, vswitch_sd, hw_offload_sd):
        nic_name = self._netutils.get_vswitch_external_network_name(
            vswitch_sd.ElementName)
        if not nic_name:
            # NOTE(claudiub): This can happen if the vSwitch is not
            # external.
            LOG.warning("VSwitch %s is not external.", vswitch_sd.ElementName)
            return

        # check if the vSwitch is misconfigured.
        if vswitch_sd.IOVPreferred and not hw_offload_sd.IovVfCapacity:
            LOG.warning("VSwitch %s has SR-IOV enabled, but it is not "
                        "supported by the NIC or by the OS.",
                        vswitch_sd.ElementName)

        nic = self._conn_scimv2.MSFT_NetAdapter(
            InterfaceDescription=nic_name)[0]

        return {
            'vswitch_name': vswitch_sd.ElementName,
            'device_id': nic.PnPDeviceID,
            'total_vfs': hw_offload_sd.IovVfCapacity,
            'used_vfs': hw_offload_sd.IovVfUsage,
            'total_iov_queue_pairs': hw_offload_sd.IovQueuePairCapacity,
            'used_iov_queue_pairs': hw_offload_sd.IovQueuePairUsage,
            'total_vmqs': hw_offload_sd.VmqCapacity,
            'used_vmqs': hw_offload_sd.VmqUsage,
            'total_ipsecsa': hw_offload_sd.IPsecSACapacity,
            'used_ipsecsa': hw_offload_sd.IPsecSAUsage,
        }

    def get_numa_nodes(self):
        """Returns the host's list of NUMA nodes.

        :returns: list of dictionaries containing information about each
            host NUMA node. Each host has at least one NUMA node.
        """
        numa_nodes = self._conn.Msvm_NumaNode()
        nodes_info = []
        system_memory = self._conn.Msvm_Memory(['NumberOfBlocks'])
        processors = self._conn.Msvm_Processor(['DeviceID'])

        for node in numa_nodes:
            # Due to a bug in vmms, getting Msvm_Processor for the numa
            # node associators resulted in a vmms crash.
            # As an alternative to using associators we have to manually get
            # the related Msvm_Processor classes.
            # Msvm_HostedDependency is the association class between
            # Msvm_NumaNode and Msvm_Processor. We need to use this class to
            # relate the two because using associators on Msvm_Processor
            # will also result in a crash.
            numa_assoc = self._conn.Msvm_HostedDependency(
                Antecedent=node.path_())
            numa_node_assoc = [item.Dependent for item in numa_assoc]

            memory_info = self._get_numa_memory_info(numa_node_assoc,
                                                     system_memory)
            if not memory_info:
                LOG.warning("Could not find memory information for NUMA "
                            "node. Skipping node measurements.")
                continue

            cpu_info = self._get_numa_cpu_info(numa_node_assoc, processors)
            if not cpu_info:
                LOG.warning("Could not find CPU information for NUMA "
                            "node. Skipping node measurements.")
                continue

            node_info = {
                # NodeID has the format: Microsoft:PhysicalNode\<NODE_ID>
                'id': node.NodeID.split('\\')[-1],

                # memory block size is 1MB.
                'memory': memory_info.NumberOfBlocks,
                'memory_usage': node.CurrentlyConsumableMemoryBlocks,

                # DeviceID has the format: Microsoft:UUID\0\<DEV_ID>
                'cpuset': set([c.DeviceID.split('\\')[-1] for c in cpu_info]),
                # cpu_usage can be set, each CPU has a "LoadPercentage"
                'cpu_usage': 0,
            }

            nodes_info.append(node_info)

        return nodes_info

    def _get_numa_memory_info(self, numa_node_assoc, system_memory):
        memory_info = []
        paths = [x.path_().upper() for x in numa_node_assoc]
        for memory in system_memory:
            if memory.path_().upper() in paths:
                memory_info.append(memory)

        if memory_info:
            return memory_info[0]

    def _get_numa_cpu_info(self, numa_node_assoc, processors):
        cpu_info = []
        paths = [x.path_().upper() for x in numa_node_assoc]
        for proc in processors:
            if proc.path_().upper() in paths:
                cpu_info.append(proc)

        return cpu_info

    def get_remotefx_gpu_info(self):
        """Returns information about the GPUs used for RemoteFX.

        :returns: list with dictionaries containing information about each
            GPU used for RemoteFX.
        """
        gpus = []
        all_gpus = self._conn.Msvm_Physical3dGraphicsProcessor(
            EnabledForVirtualization=True)
        for gpu in all_gpus:
            gpus.append({'name': gpu.Name,
                         'driver_version': gpu.DriverVersion,
                         'total_video_ram': gpu.TotalVideoMemory,
                         'available_video_ram': gpu.AvailableVideoMemory,
                         'directx_version': gpu.DirectXVersion})
        return gpus

    def verify_host_remotefx_capability(self):
        """Validates that the host supports RemoteFX.

        :raises exceptions.HyperVRemoteFXException: if the host has no GPU
            that supports DirectX 11, or SLAT.
        """
        synth_3d_video_pool = self._conn.Msvm_Synth3dVideoPool()[0]
        if not synth_3d_video_pool.IsGpuCapable:
            raise exceptions.HyperVRemoteFXException(
                _("To enable RemoteFX on Hyper-V at least one GPU supporting "
                  "DirectX 11 is required."))
        if not synth_3d_video_pool.IsSlatCapable:
            raise exceptions.HyperVRemoteFXException(
                _("To enable RemoteFX on Hyper-V it is required that the host "
                  "GPUs support SLAT."))

    def is_host_guarded(self):
        """Checks if the host is guarded.

        :returns: False, only Windows / Hyper-V Server 2016 or newer can be
            guarded.
        """
        return False

    def supports_nested_virtualization(self):
        """Checks if the host supports nested virtualization.

        :returns: False, only Windows / Hyper-V Server 2016 or newer supports
            nested virtualization.
        """
        return False

    def get_pci_passthrough_devices(self):
        """Get host PCI devices path.

        Discrete device assignment is supported only on Windows / Hyper-V
        Server 2016 or newer.

        :returns: a list of the assignable PCI devices.
        """

        return []
