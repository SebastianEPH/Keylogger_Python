# Copyright (c) 2010 Cloud.com, Inc
# Copyright 2012 Cloudbase Solutions Srl / Pedro Navarro Perez
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

"""
Utility class for VM related operations.
Based on the "root/virtualization/v2" namespace available starting with
Hyper-V Server / Windows Server 2012.
"""

import functools
import time
import uuid

from eventlet import patcher
from eventlet import tpool
from oslo_log import log as logging
from oslo_utils import uuidutils
from six.moves import range  # noqa

from os_win._i18n import _
from os_win import _utils
from os_win import constants
from os_win import exceptions
from os_win.utils import _wqlutils
from os_win.utils import baseutils
from os_win.utils import jobutils
from os_win.utils import pathutils

LOG = logging.getLogger(__name__)

# TODO(claudiub): remove the is_planned_vm argument from methods once it is not
# used anymore.


class VMUtils(baseutils.BaseUtilsVirt):

    # These constants can be overridden by inherited classes
    _PHYS_DISK_RES_SUB_TYPE = 'Microsoft:Hyper-V:Physical Disk Drive'
    _DISK_DRIVE_RES_SUB_TYPE = 'Microsoft:Hyper-V:Synthetic Disk Drive'
    _DVD_DRIVE_RES_SUB_TYPE = 'Microsoft:Hyper-V:Synthetic DVD Drive'
    _HARD_DISK_RES_SUB_TYPE = 'Microsoft:Hyper-V:Virtual Hard Disk'
    _DVD_DISK_RES_SUB_TYPE = 'Microsoft:Hyper-V:Virtual CD/DVD Disk'
    _IDE_CTRL_RES_SUB_TYPE = 'Microsoft:Hyper-V:Emulated IDE Controller'
    _SCSI_CTRL_RES_SUB_TYPE = 'Microsoft:Hyper-V:Synthetic SCSI Controller'
    _SERIAL_PORT_RES_SUB_TYPE = 'Microsoft:Hyper-V:Serial Port'

    _SETTINGS_DEFINE_STATE_CLASS = 'Msvm_SettingsDefineState'
    _VIRTUAL_SYSTEM_SETTING_DATA_CLASS = 'Msvm_VirtualSystemSettingData'
    _RESOURCE_ALLOC_SETTING_DATA_CLASS = 'Msvm_ResourceAllocationSettingData'
    _PROCESSOR_SETTING_DATA_CLASS = 'Msvm_ProcessorSettingData'
    _MEMORY_SETTING_DATA_CLASS = 'Msvm_MemorySettingData'
    _SERIAL_PORT_SETTING_DATA_CLASS = _RESOURCE_ALLOC_SETTING_DATA_CLASS
    _STORAGE_ALLOC_SETTING_DATA_CLASS = 'Msvm_StorageAllocationSettingData'
    _SYNTHETIC_ETHERNET_PORT_SETTING_DATA_CLASS = (
        'Msvm_SyntheticEthernetPortSettingData')
    _AFFECTED_JOB_ELEMENT_CLASS = "Msvm_AffectedJobElement"
    _CIM_RES_ALLOC_SETTING_DATA_CLASS = 'Cim_ResourceAllocationSettingData'
    _COMPUTER_SYSTEM_CLASS = "Msvm_ComputerSystem"
    _LOGICAL_IDENTITY_CLASS = 'Msvm_LogicalIdentity'
    _VIRTUAL_SYSTEM_SNAP_ASSOC_CLASS = 'Msvm_SnapshotOfVirtualSystem'

    _S3_DISP_CTRL_RES_SUB_TYPE = 'Microsoft:Hyper-V:S3 Display Controller'
    _SYNTH_DISP_CTRL_RES_SUB_TYPE = ('Microsoft:Hyper-V:Synthetic Display '
                                     'Controller')
    _REMOTEFX_DISP_CTRL_RES_SUB_TYPE = ('Microsoft:Hyper-V:Synthetic 3D '
                                        'Display Controller')
    _SYNTH_DISP_ALLOCATION_SETTING_DATA_CLASS = (
        'Msvm_SyntheticDisplayControllerSettingData')
    _REMOTEFX_DISP_ALLOCATION_SETTING_DATA_CLASS = (
        'Msvm_Synthetic3DDisplayControllerSettingData')

    _VIRTUAL_SYSTEM_SUBTYPE = 'VirtualSystemSubType'
    _VIRTUAL_SYSTEM_TYPE_REALIZED = 'Microsoft:Hyper-V:System:Realized'
    _VIRTUAL_SYSTEM_TYPE_PLANNED = 'Microsoft:Hyper-V:System:Planned'
    _VIRTUAL_SYSTEM_SUBTYPE_GEN2 = 'Microsoft:Hyper-V:SubType:2'

    _SNAPSHOT_FULL = 2

    _VM_ENABLED_STATE_PROP = "EnabledState"

    _SHUTDOWN_COMPONENT = "Msvm_ShutdownComponent"
    _VIRTUAL_SYSTEM_CURRENT_SETTINGS = 3
    _AUTOMATIC_STARTUP_ACTION_NONE = 2

    _remote_fx_res_map = {
        constants.REMOTEFX_MAX_RES_1024x768: 0,
        constants.REMOTEFX_MAX_RES_1280x1024: 1,
        constants.REMOTEFX_MAX_RES_1600x1200: 2,
        constants.REMOTEFX_MAX_RES_1920x1200: 3,
        constants.REMOTEFX_MAX_RES_2560x1600: 4
    }

    _remotefx_max_monitors_map = {
        # defines the maximum number of monitors for a given
        # resolution
        constants.REMOTEFX_MAX_RES_1024x768: 4,
        constants.REMOTEFX_MAX_RES_1280x1024: 4,
        constants.REMOTEFX_MAX_RES_1600x1200: 3,
        constants.REMOTEFX_MAX_RES_1920x1200: 2,
        constants.REMOTEFX_MAX_RES_2560x1600: 1
    }

    _DISP_CTRL_ADDRESS_DX_11 = "02C1,00000000,01"
    _DISP_CTRL_ADDRESS = "5353,00000000,00"

    _vm_power_states_map = {constants.HYPERV_VM_STATE_ENABLED: 2,
                            constants.HYPERV_VM_STATE_DISABLED: 3,
                            constants.HYPERV_VM_STATE_REBOOT: 11,
                            constants.HYPERV_VM_STATE_PAUSED: 9,
                            constants.HYPERV_VM_STATE_SUSPENDED: 6}

    _disk_ctrl_type_mapping = {
        _SCSI_CTRL_RES_SUB_TYPE: constants.CTRL_TYPE_SCSI,
        _IDE_CTRL_RES_SUB_TYPE: constants.CTRL_TYPE_IDE
    }

    _DEFAULT_EVENT_CHECK_TIMEFRAME = 60  # seconds

    def __init__(self, host='.'):
        super(VMUtils, self).__init__(host)
        self._jobutils = jobutils.JobUtils(host)
        self._pathutils = pathutils.PathUtils()
        self._enabled_states_map = {v: k for k, v in
                                    self._vm_power_states_map.items()}

    def list_instance_notes(self):
        instance_notes = []

        for vs in self._conn.Msvm_VirtualSystemSettingData(
                ['ElementName', 'Notes'],
                VirtualSystemType=self._VIRTUAL_SYSTEM_TYPE_REALIZED):
            vs_notes = vs.Notes
            vs_name = vs.ElementName
            if vs_notes is not None and vs_name:
                instance_notes.append(
                    (vs_name, [v for v in vs_notes if v]))

        return instance_notes

    def list_instances(self):
        """Return the names of all the instances known to Hyper-V."""

        return [v.ElementName for v in
                self._conn.Msvm_VirtualSystemSettingData(
                    ['ElementName'],
                    VirtualSystemType=self._VIRTUAL_SYSTEM_TYPE_REALIZED)]

    @_utils.not_found_decorator(
        translated_exc=exceptions.HyperVVMNotFoundException)
    def get_vm_summary_info(self, vm_name):
        vmsettings = self._lookup_vm_check(vm_name)

        settings_paths = [vmsettings.path_()]
        # See http://msdn.microsoft.com/en-us/library/cc160706%28VS.85%29.aspx
        (ret_val, summary_info) = self._vs_man_svc.GetSummaryInformation(
            [constants.VM_SUMMARY_NUM_PROCS,
             constants.VM_SUMMARY_ENABLED_STATE,
             constants.VM_SUMMARY_MEMORY_USAGE,
             constants.VM_SUMMARY_UPTIME],
            settings_paths)
        if ret_val:
            raise exceptions.HyperVException(
                _('Cannot get VM summary data for: %s') % vm_name)

        si = summary_info[0]
        memory_usage = None
        if si.MemoryUsage is not None:
            memory_usage = int(si.MemoryUsage)
        up_time = None
        if si.UpTime is not None:
            up_time = int(si.UpTime)

        # Nova requires a valid state to be returned. Hyper-V has more
        # states than Nova, typically intermediate ones and since there is
        # no direct mapping for those, ENABLED is the only reasonable option
        # considering that in all the non mappable states the instance
        # is running.
        enabled_state = self._enabled_states_map.get(si.EnabledState,
                                                     constants.
                                                     HYPERV_VM_STATE_ENABLED)

        summary_info_dict = {'NumberOfProcessors': si.NumberOfProcessors,
                             'EnabledState': enabled_state,
                             'MemoryUsage': memory_usage,
                             'UpTime': up_time}
        return summary_info_dict

    def get_vm_state(self, vm_name):
        settings = self.get_vm_summary_info(vm_name)
        return settings['EnabledState']

    def _lookup_vm_check(self, vm_name, as_vssd=True, for_update=False):
        vm = self._lookup_vm(vm_name, as_vssd, for_update)
        if not vm:
            raise exceptions.HyperVVMNotFoundException(vm_name=vm_name)
        return vm

    def _lookup_vm(self, vm_name, as_vssd=True, for_update=False):
        if as_vssd:
            conn = self._compat_conn if for_update else self._conn
            vms = conn.Msvm_VirtualSystemSettingData(ElementName=vm_name)
            vms = [v for v in vms if
                   v.VirtualSystemType in [self._VIRTUAL_SYSTEM_TYPE_PLANNED,
                                           self._VIRTUAL_SYSTEM_TYPE_REALIZED]]
        else:
            vms = self._conn.Msvm_ComputerSystem(ElementName=vm_name)
        n = len(vms)
        if n == 0:
            return None
        elif n > 1:
            raise exceptions.HyperVException(
                _('Duplicate VM name found: %s') % vm_name)
        else:
            return vms[0]

    def vm_exists(self, vm_name):
        """Checks if the Realized VM with the given name exists on the host."""
        # NOTE(claudiub): A planned VM and a realized VM cannot exist at the
        # same time on the same host. The 2 types must be treated separately,
        # thus, this will only check if the Realized VM exits.
        return self._lookup_vm(vm_name, False) is not None

    def get_vm_id(self, vm_name):
        vm = self._lookup_vm_check(vm_name, as_vssd=False)
        return vm.Name

    def get_vm_memory_info(self, vm_name):
        vmsetting = self._lookup_vm_check(vm_name)
        memory = self._get_vm_memory(vmsetting)

        memory_info_dict = {
            'DynamicMemoryEnabled': memory.DynamicMemoryEnabled,
            'Reservation': memory.Reservation,
            'Limit': memory.Limit,
            'Weight': memory.Weight,
            'MaxMemoryBlocksPerNumaNode': memory.MaxMemoryBlocksPerNumaNode,
        }
        return memory_info_dict

    def _get_vm_memory(self, vmsetting):
        mem_settings = _wqlutils.get_element_associated_class(
            self._compat_conn, self._MEMORY_SETTING_DATA_CLASS,
            element_instance_id=vmsetting.InstanceID)[0]

        return mem_settings

    def _set_vm_memory(self, vmsetting, memory_mb, memory_per_numa_node,
                       dynamic_memory_ratio):
        mem_settings = self._get_vm_memory(vmsetting)
        max_mem = int(memory_mb)
        mem_settings.Limit = max_mem

        if dynamic_memory_ratio > 1:
            mem_settings.DynamicMemoryEnabled = True
            # Must be a multiple of 2
            reserved_mem = min(
                int(max_mem / dynamic_memory_ratio) >> 1 << 1,
                max_mem)
        else:
            mem_settings.DynamicMemoryEnabled = False
            reserved_mem = max_mem

        mem_settings.Reservation = reserved_mem
        # Start with the minimum memory
        mem_settings.VirtualQuantity = reserved_mem

        if memory_per_numa_node:
            # One memory block is 1 MB.
            mem_settings.MaxMemoryBlocksPerNumaNode = memory_per_numa_node

        self._jobutils.modify_virt_resource(mem_settings)

    def _set_vm_vcpus(self, vmsetting, vcpus_num, vcpus_per_numa_node,
                      limit_cpu_features):
        procsetting = _wqlutils.get_element_associated_class(
            self._compat_conn, self._PROCESSOR_SETTING_DATA_CLASS,
            element_instance_id=vmsetting.InstanceID)[0]

        vcpus = int(vcpus_num)
        procsetting.VirtualQuantity = vcpus
        procsetting.Reservation = vcpus
        procsetting.Limit = 100000  # static assignment to 100%
        procsetting.LimitProcessorFeatures = limit_cpu_features

        if vcpus_per_numa_node:
            procsetting.MaxProcessorsPerNumaNode = vcpus_per_numa_node

        self._jobutils.modify_virt_resource(procsetting)

    def set_nested_virtualization(self, vm_name, state):
        """Enables nested virtualization for the given VM.

        :raises NotImplemented: Nested virtualization is supported on
            Windows / Hyper-V Server 2016 or newer.
        """
        raise NotImplementedError(_('Nested virtualization is supported on '
                                    'Windows / Hyper-V Server 2016 or newer.'))

    def update_vm(self, vm_name, memory_mb, memory_per_numa_node, vcpus_num,
                  vcpus_per_numa_node, limit_cpu_features, dynamic_mem_ratio,
                  configuration_root_dir=None, snapshot_dir=None,
                  host_shutdown_action=None, vnuma_enabled=None,
                  snapshot_type=None,
                  is_planned_vm=False):
        vmsetting = self._lookup_vm_check(vm_name, for_update=True)

        if host_shutdown_action:
            vmsetting.AutomaticShutdownAction = host_shutdown_action
        if configuration_root_dir:
            # Created VMs must have their *DataRoot paths in the same location
            # as the VM's path.
            vmsetting.ConfigurationDataRoot = configuration_root_dir
            vmsetting.LogDataRoot = configuration_root_dir
            vmsetting.SnapshotDataRoot = configuration_root_dir
            vmsetting.SuspendDataRoot = configuration_root_dir
            vmsetting.SwapFileDataRoot = configuration_root_dir
        if vnuma_enabled is not None:
            vmsetting.VirtualNumaEnabled = vnuma_enabled

        self._set_vm_memory(vmsetting, memory_mb, memory_per_numa_node,
                            dynamic_mem_ratio)
        self._set_vm_vcpus(vmsetting, vcpus_num, vcpus_per_numa_node,
                           limit_cpu_features)

        if snapshot_type:
            self._set_vm_snapshot_type(vmsetting, snapshot_type)

        self._modify_virtual_system(vmsetting)

    def check_admin_permissions(self):
        if not self._compat_conn.Msvm_VirtualSystemManagementService():
            raise exceptions.HyperVAuthorizationException()

    def create_vm(self, vm_name, vnuma_enabled, vm_gen, instance_path,
                  notes=None):
        LOG.debug('Creating VM %s', vm_name)
        vs_data = self._compat_conn.Msvm_VirtualSystemSettingData.new()
        vs_data.ElementName = vm_name
        vs_data.Notes = notes
        # Don't start automatically on host boot
        vs_data.AutomaticStartupAction = self._AUTOMATIC_STARTUP_ACTION_NONE

        vs_data.VirtualNumaEnabled = vnuma_enabled

        if vm_gen == constants.VM_GEN_2:
            vs_data.VirtualSystemSubType = self._VIRTUAL_SYSTEM_SUBTYPE_GEN2
            vs_data.SecureBootEnabled = False

        # Created VMs must have their *DataRoot paths in the same location as
        # the instances' path.
        vs_data.ConfigurationDataRoot = instance_path
        vs_data.LogDataRoot = instance_path
        vs_data.SnapshotDataRoot = instance_path
        vs_data.SuspendDataRoot = instance_path
        vs_data.SwapFileDataRoot = instance_path

        (job_path,
         vm_path,
         ret_val) = self._vs_man_svc.DefineSystem(
            ResourceSettings=[], ReferenceConfiguration=None,
            SystemSettings=vs_data.GetText_(1))
        self._jobutils.check_ret_val(ret_val, job_path)

    @_utils.retry_decorator(exceptions=exceptions.HyperVException)
    def _modify_virtual_system(self, vmsetting):
        (job_path, ret_val) = self._vs_man_svc.ModifySystemSettings(
            SystemSettings=vmsetting.GetText_(1))
        self._jobutils.check_ret_val(ret_val, job_path)

    def get_vm_scsi_controller(self, vm_name):
        vmsettings = self._lookup_vm_check(vm_name)
        return self._get_vm_scsi_controller(vmsettings)

    def _get_vm_scsi_controller(self, vmsettings):
        res = self._get_vm_disk_controllers(vmsettings,
                                            self._SCSI_CTRL_RES_SUB_TYPE)
        return res[0].path_() if res else None

    def _get_vm_disk_controllers(self, vmsettings, ctrl_res_sub_type):
        rasds = _wqlutils.get_element_associated_class(
            self._conn, self._RESOURCE_ALLOC_SETTING_DATA_CLASS,
            element_instance_id=vmsettings.InstanceID)
        res = [r for r in rasds
               if r.ResourceSubType == ctrl_res_sub_type]
        return res

    def _get_vm_ide_controller(self, vmsettings, ctrller_addr):
        ide_ctrls = self._get_vm_disk_controllers(vmsettings,
                                                  self._IDE_CTRL_RES_SUB_TYPE)
        ctrl = [r for r in ide_ctrls
                if r.Address == str(ctrller_addr)]

        return ctrl[0].path_() if ctrl else None

    def get_vm_ide_controller(self, vm_name, ctrller_addr):
        vmsettings = self._lookup_vm_check(vm_name)
        return self._get_vm_ide_controller(vmsettings, ctrller_addr)

    def _get_disk_ctrl_addr(self, controller_path):
        ctrl = self._get_wmi_obj(controller_path)
        if ctrl.ResourceSubType == self._IDE_CTRL_RES_SUB_TYPE:
            return ctrl.Address

        vmsettings = ctrl.associators(
            wmi_result_class=self._VIRTUAL_SYSTEM_SETTING_DATA_CLASS)[0]
        # The powershell commandlets rely on the controller index as SCSI
        # controllers are missing the 'Address' attribute. We'll do the
        # same.
        scsi_ctrls = self._get_vm_disk_controllers(
            vmsettings, self._SCSI_CTRL_RES_SUB_TYPE)
        ctrl_paths = [rasd.path_().upper() for rasd in scsi_ctrls]

        if controller_path.upper() in ctrl_paths:
            return ctrl_paths.index(controller_path.upper())

    def get_attached_disks(self, scsi_controller_path):
        volumes = self._conn.query(
            self._get_attached_disks_query_string(scsi_controller_path))
        return volumes

    def _get_attached_disks_query_string(self, scsi_controller_path):
        # DVD Drives can be attached to SCSI as well, if the VM Generation is 2
        return ("SELECT * FROM Msvm_ResourceAllocationSettingData WHERE ("
                "ResourceSubType='%(res_sub_type)s' OR "
                "ResourceSubType='%(res_sub_type_virt)s' OR "
                "ResourceSubType='%(res_sub_type_dvd)s') AND "
                "Parent = '%(parent)s'" % {
                    'res_sub_type': self._PHYS_DISK_RES_SUB_TYPE,
                    'res_sub_type_virt': self._DISK_DRIVE_RES_SUB_TYPE,
                    'res_sub_type_dvd': self._DVD_DRIVE_RES_SUB_TYPE,
                    'parent': scsi_controller_path.replace("'", "''")})

    def _get_new_setting_data(self, class_name):
        obj = self._compat_conn.query("SELECT * FROM %s WHERE InstanceID "
                                      "LIKE '%%\\Default'" % class_name)[0]
        return obj

    def _get_new_resource_setting_data(self, resource_sub_type,
                                       class_name=None):
        if class_name is None:
            class_name = self._RESOURCE_ALLOC_SETTING_DATA_CLASS
        obj = self._compat_conn.query("SELECT * FROM %(class_name)s "
                                      "WHERE ResourceSubType = "
                                      "'%(res_sub_type)s' AND "
                                      "InstanceID LIKE '%%\\Default'" %
                                      {"class_name": class_name,
                                       "res_sub_type": resource_sub_type})[0]
        return obj

    def attach_scsi_drive(self, vm_name, path, drive_type=constants.DISK):
        vmsettings = self._lookup_vm_check(vm_name)
        ctrller_path = self._get_vm_scsi_controller(vmsettings)
        drive_addr = self.get_free_controller_slot(ctrller_path)
        self.attach_drive(vm_name, path, ctrller_path, drive_addr, drive_type)

    def attach_ide_drive(self, vm_name, path, ctrller_addr, drive_addr,
                         drive_type=constants.DISK):
        vmsettings = self._lookup_vm_check(vm_name)
        ctrller_path = self._get_vm_ide_controller(vmsettings, ctrller_addr)
        self.attach_drive(vm_name, path, ctrller_path, drive_addr, drive_type)

    def attach_drive(self, vm_name, path, ctrller_path, drive_addr,
                     drive_type=constants.DISK):
        """Create a drive and attach it to the vm."""

        vm = self._lookup_vm_check(vm_name, as_vssd=False)

        if drive_type == constants.DISK:
            res_sub_type = self._DISK_DRIVE_RES_SUB_TYPE
        elif drive_type == constants.DVD:
            res_sub_type = self._DVD_DRIVE_RES_SUB_TYPE

        drive = self._get_new_resource_setting_data(res_sub_type)

        # Set the ctrller as parent.
        drive.Parent = ctrller_path
        drive.Address = drive_addr
        drive.AddressOnParent = drive_addr
        # Add the cloned disk drive object to the vm.
        new_resources = self._jobutils.add_virt_resource(drive, vm)
        drive_path = new_resources[0]

        if drive_type == constants.DISK:
            res_sub_type = self._HARD_DISK_RES_SUB_TYPE
        elif drive_type == constants.DVD:
            res_sub_type = self._DVD_DISK_RES_SUB_TYPE

        res = self._get_new_resource_setting_data(
            res_sub_type, self._STORAGE_ALLOC_SETTING_DATA_CLASS)

        res.Parent = drive_path
        res.HostResource = [path]

        try:
            # Add the new vhd object as a virtual hard disk to the vm.
            self._jobutils.add_virt_resource(res, vm)
        except Exception:
            LOG.exception("Failed to attach disk image %(disk_path)s "
                          "to vm %(vm_name)s. Reverting attachment.",
                          dict(disk_path=path, vm_name=vm_name))

            drive = self._get_wmi_obj(drive_path)
            self._jobutils.remove_virt_resource(drive)
            raise

    def get_disk_attachment_info(self, attached_disk_path=None,
                                 is_physical=True, serial=None):
        res = self._get_mounted_disk_resource_from_path(attached_disk_path,
                                                        is_physical,
                                                        serial=serial)
        if not res:
            err_msg = _("Disk '%s' is not attached to a vm.")
            raise exceptions.DiskNotFound(err_msg % attached_disk_path)

        if is_physical:
            drive = res
        else:
            drive = self._get_wmi_obj(res.Parent)

        ctrl_slot = int(drive.AddressOnParent)
        ctrl_path = drive.Parent
        ctrl_type = self._get_disk_controller_type(ctrl_path)
        ctrl_addr = self._get_disk_ctrl_addr(ctrl_path)

        attachment_info = dict(controller_slot=ctrl_slot,
                               controller_path=ctrl_path,
                               controller_type=ctrl_type,
                               controller_addr=ctrl_addr)
        return attachment_info

    def _get_disk_controller_type(self, controller_path):
        ctrl = self._get_wmi_obj(controller_path)
        res_sub_type = ctrl.ResourceSubType

        ctrl_type = self._disk_ctrl_type_mapping[res_sub_type]
        return ctrl_type

    def create_scsi_controller(self, vm_name):
        """Create an iscsi controller ready to mount volumes."""

        vmsettings = self._lookup_vm_check(vm_name)
        scsicontrl = self._get_new_resource_setting_data(
            self._SCSI_CTRL_RES_SUB_TYPE)

        scsicontrl.VirtualSystemIdentifiers = ['{' + str(uuid.uuid4()) + '}']
        self._jobutils.add_virt_resource(scsicontrl, vmsettings)

    def attach_volume_to_controller(self, vm_name, controller_path, address,
                                    mounted_disk_path, serial=None):
        """Attach a volume to a controller."""

        vmsettings = self._lookup_vm_check(vm_name)

        diskdrive = self._get_new_resource_setting_data(
            self._PHYS_DISK_RES_SUB_TYPE)

        diskdrive.AddressOnParent = address
        diskdrive.Parent = controller_path
        diskdrive.HostResource = [mounted_disk_path]

        diskdrive_path = self._jobutils.add_virt_resource(diskdrive,
                                                          vmsettings)[0]

        if serial:
            # Apparently this can't be set when the resource is added.
            diskdrive = self._get_wmi_obj(diskdrive_path, True)
            diskdrive.ElementName = serial
            self._jobutils.modify_virt_resource(diskdrive)

    def get_vm_physical_disk_mapping(self, vm_name, is_planned_vm=False):
        mapping = {}
        physical_disks = (
            self.get_vm_disks(vm_name)[1])
        for diskdrive in physical_disks:
            mapping[diskdrive.ElementName] = dict(
                resource_path=diskdrive.path_(),
                mounted_disk_path=diskdrive.HostResource[0])
        return mapping

    def _get_disk_resource_address(self, disk_resource):
        return disk_resource.AddressOnParent

    def set_disk_host_res(self, disk_res_path, mounted_disk_path):
        diskdrive = self._get_wmi_obj(disk_res_path, True)
        diskdrive.HostResource = [mounted_disk_path]
        self._jobutils.modify_virt_resource(diskdrive)

    def _get_nic_data_by_name(self, name):
        nics = self._conn.Msvm_SyntheticEthernetPortSettingData(
            ElementName=name)
        if nics:
            return nics[0]

        raise exceptions.HyperVvNicNotFound(vnic_name=name)

    def create_nic(self, vm_name, nic_name, mac_address=None):
        """Create a (synthetic) nic and attach it to the vm.

        :param vm_name: The VM name to which the NIC will be attached to.
        :param nic_name: The name of the NIC to be attached.
        :param mac_address: The VM NIC's MAC address. If None, a Dynamic MAC
            address will be used instead.
        """
        # Create a new nic
        new_nic_data = self._get_new_setting_data(
            self._SYNTHETIC_ETHERNET_PORT_SETTING_DATA_CLASS)

        # Configure the nic
        new_nic_data.ElementName = nic_name
        new_nic_data.VirtualSystemIdentifiers = ['{' + str(uuid.uuid4()) + '}']
        if mac_address:
            new_nic_data.Address = mac_address.replace(':', '')
            new_nic_data.StaticMacAddress = 'True'

        # Add the new nic to the vm
        vmsettings = self._lookup_vm_check(vm_name)

        self._jobutils.add_virt_resource(new_nic_data, vmsettings)

    def destroy_nic(self, vm_name, nic_name):
        """Destroys the NIC with the given nic_name from the given VM.

        :param vm_name: The name of the VM which has the NIC to be destroyed.
        :param nic_name: The NIC's ElementName.
        """
        # TODO(claudiub): remove vm_name argument, no longer used.
        try:
            nic_data = self._get_nic_data_by_name(nic_name)
            self._jobutils.remove_virt_resource(nic_data)
        except exceptions.NotFound:
            LOG.debug("Ignoring NotFound exception while attempting "
                      "to remove vm nic: '%s'. It may have been already "
                      "deleted.", nic_name)

    def _get_vm_nics(self, vm_name):
        vmsettings = self._lookup_vm_check(vm_name)
        nics = _wqlutils.get_element_associated_class(
            self._compat_conn,
            self._SYNTHETIC_ETHERNET_PORT_SETTING_DATA_CLASS,
            element_instance_id=vmsettings.InstanceId)
        return nics

    def get_vm_nic_names(self, vm_name):
        nics = self._get_vm_nics(vm_name)
        return [nic.ElementName for nic in nics]

    def soft_shutdown_vm(self, vm_name):
        vm = self._lookup_vm_check(vm_name, as_vssd=False)
        shutdown_component = self._conn.Msvm_ShutdownComponent(
            SystemName=vm.Name)

        if not shutdown_component:
            # If no shutdown_component is found, it means the VM is already
            # in a shutdown state.
            return

        reason = 'Soft shutdown requested by OpenStack Nova.'
        (ret_val, ) = shutdown_component[0].InitiateShutdown(Force=False,
                                                             Reason=reason)
        self._jobutils.check_ret_val(ret_val, None)

    @_utils.retry_decorator(exceptions=exceptions.WMIJobFailed)
    def set_vm_state(self, vm_name, req_state):
        """Set the desired state of the VM."""

        vm = self._lookup_vm_check(vm_name, as_vssd=False)
        (job_path,
         ret_val) = vm.RequestStateChange(self._vm_power_states_map[req_state])
        # Invalid state for current operation (32775) typically means that
        # the VM is already in the state requested
        self._jobutils.check_ret_val(ret_val, job_path, [0, 32775])
        LOG.debug("Successfully changed vm state of %(vm_name)s "
                  "to %(req_state)s",
                  {'vm_name': vm_name, 'req_state': req_state})

    def _get_disk_resource_disk_path(self, disk_resource):
        return disk_resource.HostResource

    def get_vm_config_root_dir(self, vm_name):
        vmsettings = self._lookup_vm_check(vm_name)
        return vmsettings.ConfigurationDataRoot

    def get_vm_storage_paths(self, vm_name, is_planned_vm=False):
        vmsettings = self._lookup_vm_check(vm_name)
        (disk_resources, volume_resources) = self._get_vm_disks(vmsettings)

        volume_drives = []
        for volume_resource in volume_resources:
            drive_path = volume_resource.HostResource[0]
            volume_drives.append(drive_path)

        disk_files = []
        for disk_resource in disk_resources:
            disk_files.extend(
                [c for c in self._get_disk_resource_disk_path(disk_resource)])

        return (disk_files, volume_drives)

    def get_vm_disks(self, vm_name, is_planned_vm=False):
        vmsettings = self._lookup_vm_check(vm_name)
        return self._get_vm_disks(vmsettings)

    def _get_vm_disks(self, vmsettings):
        rasds = _wqlutils.get_element_associated_class(
            self._compat_conn, self._STORAGE_ALLOC_SETTING_DATA_CLASS,
            element_instance_id=vmsettings.InstanceID)
        disk_resources = [r for r in rasds if
                          r.ResourceSubType in
                          [self._HARD_DISK_RES_SUB_TYPE,
                           self._DVD_DISK_RES_SUB_TYPE]]

        if (self._RESOURCE_ALLOC_SETTING_DATA_CLASS !=
                self._STORAGE_ALLOC_SETTING_DATA_CLASS):
            rasds = _wqlutils.get_element_associated_class(
                self._compat_conn, self._RESOURCE_ALLOC_SETTING_DATA_CLASS,
                element_instance_id=vmsettings.InstanceID)

        volume_resources = [r for r in rasds if
                            r.ResourceSubType == self._PHYS_DISK_RES_SUB_TYPE]

        return (disk_resources, volume_resources)

    def destroy_vm(self, vm_name):
        vm = self._lookup_vm_check(vm_name, as_vssd=False)

        # Remove the VM. It does not destroy any associated virtual disk.
        (job_path, ret_val) = self._vs_man_svc.DestroySystem(vm.path_())
        self._jobutils.check_ret_val(ret_val, job_path)

    def take_vm_snapshot(self, vm_name, snapshot_name=None):
        vm = self._lookup_vm_check(vm_name, as_vssd=False)
        vs_snap_svc = self._compat_conn.Msvm_VirtualSystemSnapshotService()[0]

        (job_path, snp_setting_data, ret_val) = vs_snap_svc.CreateSnapshot(
            AffectedSystem=vm.path_(),
            SnapshotType=self._SNAPSHOT_FULL)

        job = self._jobutils.check_ret_val(ret_val, job_path)
        snp_setting_data = job.associators(
            wmi_result_class=self._VIRTUAL_SYSTEM_SETTING_DATA_CLASS,
            wmi_association_class=self._AFFECTED_JOB_ELEMENT_CLASS)[0]

        if snapshot_name is not None:
            snp_setting_data.ElementName = snapshot_name
            self._modify_virtual_system(snp_setting_data)

        return snp_setting_data.path_()

    def get_vm_snapshots(self, vm_name, snapshot_name=None):
        vm = self._lookup_vm_check(vm_name, as_vssd=False)
        snapshots = vm.associators(
            wmi_association_class=self._VIRTUAL_SYSTEM_SNAP_ASSOC_CLASS,
            wmi_result_class=self._VIRTUAL_SYSTEM_SETTING_DATA_CLASS)

        return [
            s.path_() for s in snapshots
            if snapshot_name is None or s.ElementName == snapshot_name]

    def remove_vm_snapshot(self, snapshot_path):
        vs_snap_svc = self._compat_conn.Msvm_VirtualSystemSnapshotService()[0]
        (job_path, ret_val) = vs_snap_svc.DestroySnapshot(snapshot_path)
        self._jobutils.check_ret_val(ret_val, job_path)

    def get_vm_dvd_disk_paths(self, vm_name):
        vmsettings = self._lookup_vm_check(vm_name)

        sasds = _wqlutils.get_element_associated_class(
            self._conn, self._STORAGE_ALLOC_SETTING_DATA_CLASS,
            element_instance_id=vmsettings.InstanceID)

        dvd_paths = [sasd.HostResource[0] for sasd in sasds
                     if sasd.ResourceSubType == self._DVD_DISK_RES_SUB_TYPE]

        return dvd_paths

    def is_disk_attached(self, disk_path, is_physical=True):
        disk_resource = self._get_mounted_disk_resource_from_path(disk_path,
                                                                  is_physical)
        return disk_resource is not None

    def detach_vm_disk(self, vm_name, disk_path=None, is_physical=True,
                       serial=None):
        # TODO(claudiub): remove vm_name argument, no longer used.
        disk_resource = self._get_mounted_disk_resource_from_path(
            disk_path, is_physical, serial=serial)

        if disk_resource:
            parent = self._conn.query("SELECT * FROM "
                                      "Msvm_ResourceAllocationSettingData "
                                      "WHERE __PATH = '%s'" %
                                      disk_resource.Parent)[0]

            self._jobutils.remove_virt_resource(disk_resource)
            if not is_physical:
                self._jobutils.remove_virt_resource(parent)

    def _get_mounted_disk_resource_from_path(self, disk_path, is_physical,
                                             serial=None):
        if is_physical:
            class_name = self._RESOURCE_ALLOC_SETTING_DATA_CLASS
        else:
            class_name = self._STORAGE_ALLOC_SETTING_DATA_CLASS

        query = ("SELECT * FROM %(class_name)s WHERE ("
                 "ResourceSubType='%(res_sub_type)s' OR "
                 "ResourceSubType='%(res_sub_type_virt)s' OR "
                 "ResourceSubType='%(res_sub_type_dvd)s')" % {
                     'class_name': class_name,
                     'res_sub_type': self._PHYS_DISK_RES_SUB_TYPE,
                     'res_sub_type_virt': self._HARD_DISK_RES_SUB_TYPE,
                     'res_sub_type_dvd': self._DVD_DISK_RES_SUB_TYPE})

        if serial:
            query += " AND ElementName='%s'" % serial

        disk_resources = self._compat_conn.query(query)

        for disk_resource in disk_resources:
            if serial:
                return disk_resource

            if disk_resource.HostResource:
                if disk_resource.HostResource[0].lower() == disk_path.lower():
                    return disk_resource

    def get_mounted_disk_by_drive_number(self, device_number):
        mounted_disks = self._conn.query("SELECT * FROM Msvm_DiskDrive "
                                         "WHERE DriveNumber=" +
                                         str(device_number))
        if len(mounted_disks):
            return mounted_disks[0].path_()

    def get_controller_volume_paths(self, controller_path):
        disks = self._conn.query("SELECT * FROM %(class_name)s "
                                 "WHERE ResourceSubType = '%(res_sub_type)s' "
                                 "AND Parent='%(parent)s'" %
                                 {"class_name":
                                  self._RESOURCE_ALLOC_SETTING_DATA_CLASS,
                                  "res_sub_type":
                                  self._PHYS_DISK_RES_SUB_TYPE,
                                  "parent":
                                  controller_path})
        disk_data = {}
        for disk in disks:
            if disk.HostResource:
                disk_data[disk.path().RelPath] = disk.HostResource[0]
        return disk_data

    def get_free_controller_slot(self, scsi_controller_path):
        attached_disks = self.get_attached_disks(scsi_controller_path)
        used_slots = [int(disk.AddressOnParent) for disk in attached_disks]

        for slot in range(constants.SCSI_CONTROLLER_SLOTS_NUMBER):
            if slot not in used_slots:
                return slot
        raise exceptions.HyperVException(
            _("Exceeded the maximum number of slots"))

    def _get_vm_serial_ports(self, vmsettings):
        rasds = _wqlutils.get_element_associated_class(
            self._compat_conn, self._SERIAL_PORT_SETTING_DATA_CLASS,
            element_instance_id=vmsettings.InstanceID)
        serial_ports = (
            [r for r in rasds if
             r.ResourceSubType == self._SERIAL_PORT_RES_SUB_TYPE]
        )
        return serial_ports

    def set_vm_serial_port_connection(self, vm_name, port_number, pipe_path):
        vmsettings = self._lookup_vm_check(vm_name)

        serial_port = self._get_vm_serial_ports(vmsettings)[port_number - 1]
        serial_port.Connection = [pipe_path]

        self._jobutils.modify_virt_resource(serial_port)

    def get_vm_serial_port_connections(self, vm_name):
        vmsettings = self._lookup_vm_check(vm_name)
        serial_ports = self._get_vm_serial_ports(vmsettings)
        conns = [serial_port.Connection[0]
                 for serial_port in serial_ports
                 if serial_port.Connection and serial_port.Connection[0]]
        return conns

    def get_active_instances(self):
        """Return the names of all the active instances known to Hyper-V."""

        vm_names = self.list_instances()
        vms = [self._lookup_vm(vm_name, as_vssd=False) for vm_name in vm_names]
        active_vm_names = [v.ElementName for v in vms
                           if v.EnabledState ==
                           constants.HYPERV_VM_STATE_ENABLED]

        return active_vm_names

    def get_vm_power_state_change_listener(
            self, timeframe=_DEFAULT_EVENT_CHECK_TIMEFRAME,
            event_timeout=constants.DEFAULT_WMI_EVENT_TIMEOUT_MS,
            filtered_states=None, get_handler=False):
        field = self._VM_ENABLED_STATE_PROP
        query = self._get_event_wql_query(cls=self._COMPUTER_SYSTEM_CLASS,
                                          field=field,
                                          timeframe=timeframe,
                                          filtered_states=filtered_states)
        listener = self._conn.Msvm_ComputerSystem.watch_for(raw_wql=query,
                                                            fields=[field])

        def _handle_events(callback):
            if patcher.is_monkey_patched('thread'):
                # Retrieve one by one all the events that occurred in
                # the checked interval.
                #
                # We use eventlet.tpool for retrieving the events in
                # order to avoid issues caused by greenthread/thread
                # communication. Note that PyMI must use the unpatched
                # threading module.
                listen = functools.partial(tpool.execute, listener,
                                           event_timeout)
            else:
                listen = functools.partial(listener, event_timeout)

            while True:
                try:
                    event = listen()

                    vm_name = event.ElementName
                    vm_state = event.EnabledState
                    vm_power_state = self.get_vm_power_state(vm_state)

                    try:
                        callback(vm_name, vm_power_state)
                    except Exception:
                        err_msg = ("Executing VM power state change "
                                   "event callback failed. "
                                   "VM name: %(vm_name)s, "
                                   "VM power state: %(vm_power_state)s.")
                        LOG.exception(err_msg,
                                      dict(vm_name=vm_name,
                                           vm_power_state=vm_power_state))
                except exceptions.x_wmi_timed_out:
                    pass
                except Exception:
                    LOG.exception(
                        "The VM power state change event listener "
                        "encountered an unexpected exception.")
                    time.sleep(event_timeout / 1000)

        return _handle_events if get_handler else listener

    def _get_event_wql_query(self, cls, field,
                             timeframe, filtered_states=None):
        """Return a WQL query used for polling WMI events.

            :param cls: the WMI class polled for events
            :param field: the field checked
            :param timeframe: check for events that occurred in
                              the specified timeframe
            :param filtered_states: only catch events triggered when a WMI
                                    object transitioned into one of those
                                    states.
        """

        query = ("SELECT %(field)s, TargetInstance "
                 "FROM __InstanceModificationEvent "
                 "WITHIN %(timeframe)s "
                 "WHERE TargetInstance ISA '%(class)s' "
                 "AND TargetInstance.%(field)s != "
                 "PreviousInstance.%(field)s" %
                 {'class': cls,
                  'field': field,
                  'timeframe': timeframe})
        if filtered_states:
            checks = ["TargetInstance.%s = '%s'" % (field, state)
                      for state in filtered_states]
            query += " AND (%s)" % " OR ".join(checks)
        return query

    def _get_instance_notes(self, vm_name):
        vmsettings = self._lookup_vm_check(vm_name)
        vm_notes = vmsettings.Notes or []
        return [note for note in vm_notes if note]

    def get_instance_uuid(self, vm_name):
        instance_notes = self._get_instance_notes(vm_name)
        if instance_notes and uuidutils.is_uuid_like(instance_notes[0]):
            return instance_notes[0]

    def get_vm_power_state(self, vm_enabled_state):
        return self._enabled_states_map.get(vm_enabled_state,
                                            constants.HYPERV_VM_STATE_OTHER)

    def get_vm_generation(self, vm_name):
        vssd = self._lookup_vm_check(vm_name)
        try:
            # expected format: 'Microsoft:Hyper-V:SubType:2'
            return int(vssd.VirtualSystemSubType.split(':')[-1])
        except Exception:
            # NOTE(claudiub): The Msvm_VirtualSystemSettingData object does not
            # contain the VirtualSystemSubType field on Windows Hyper-V /
            # Server 2012.
            pass
        return constants.VM_GEN_1

    def stop_vm_jobs(self, vm_name, timeout=None):
        vm = self._lookup_vm_check(vm_name, as_vssd=False)
        self._jobutils.stop_jobs(vm, timeout)

    def enable_secure_boot(self, vm_name, msft_ca_required):
        """Enables Secure Boot for the instance with the given name.

        :param vm_name: The name of the VM for which Secure Boot will be
                        enabled.
        :param msft_ca_required: boolean specifying whether the VM will
                                 require Microsoft UEFI Certificate
                                 Authority for Secure Boot. Only Linux
                                 guests require this CA.
        """

        vs_data = self._lookup_vm_check(vm_name)
        self._set_secure_boot(vs_data, msft_ca_required)
        self._modify_virtual_system(vs_data)

    def _set_secure_boot(self, vs_data, msft_ca_required):
        vs_data.SecureBootEnabled = True
        if msft_ca_required:
            raise exceptions.HyperVException(
                _('UEFI SecureBoot is supported only on Windows instances for '
                  'this Hyper-V version.'))

    def set_disk_qos_specs(self, disk_path, max_iops=None, min_iops=None):
        """Hyper-V disk QoS policy.

        This feature is supported on Windows / Hyper-V Server 2012 R2 or newer.

        :raises os_win.exceptions.UnsupportedOperation: if the given max_iops
            or min_iops have non-zero values.
        """
        if min_iops or max_iops:
            raise exceptions.UnsupportedOperation(
                reason=_("Virtual disk QoS is not supported on this "
                         "hypervisor version."))

    def _drive_to_boot_source(self, drive_path):
        # We expect the drive path to be the one that was passed to the
        # 'attach_drive' or 'attach_volume_to_controller' methods. In case of
        # passthrough disks, the drive path will be a Msvm_DiskDrive WMI
        # object path while for image files it will be the actual image path.
        #
        # Note that Msvm_DiskDrive objects will also exist for attached disk
        # images, but that's not what we'll get in this situation. If we ever
        # need to accept Msvm_DiskDrive object paths for image files as well,
        # an extra check will be needed, but that may lead to some other
        # inconsistencies.
        is_physical = (r'root\virtualization\v2:Msvm_DiskDrive'.lower() in
                       drive_path.lower())
        drive = self._get_mounted_disk_resource_from_path(
            drive_path, is_physical=is_physical)

        rasd_path = drive.path_() if is_physical else drive.Parent
        bssd = self._conn.Msvm_LogicalIdentity(
            SystemElement=rasd_path)[0].SameElement

        return bssd.path_()

    def set_boot_order(self, vm_name, device_boot_order):
        if self.get_vm_generation(vm_name) == constants.VM_GEN_1:
            self._set_boot_order_gen1(vm_name, device_boot_order)
        else:
            self._set_boot_order_gen2(vm_name, device_boot_order)

    def _set_boot_order_gen1(self, vm_name, device_boot_order):
        vssd = self._lookup_vm_check(vm_name, for_update=True)
        vssd.BootOrder = tuple(device_boot_order)

        self._modify_virtual_system(vssd)

    def _set_boot_order_gen2(self, vm_name, device_boot_order):
        new_boot_order = [(self._drive_to_boot_source(device))
                          for device in device_boot_order if device]

        vssd = self._lookup_vm_check(vm_name)
        old_boot_order = vssd.BootSourceOrder

        # NOTE(abalutoiu): new_boot_order will contain ROOT uppercase
        # in the device paths while old_boot_order will contain root
        # lowercase, which will cause the tuple addition result to contain
        # each device path twice because of the root lowercase and uppercase.
        # Forcing all the device paths to uppercase fixes the issue.
        new_boot_order = [x.upper() for x in new_boot_order]
        old_boot_order = [x.upper() for x in old_boot_order]
        network_boot_devs = set(old_boot_order) ^ set(new_boot_order)
        vssd.BootSourceOrder = tuple(new_boot_order) + tuple(network_boot_devs)
        self._modify_virtual_system(vssd)

    def vm_gen_supports_remotefx(self, vm_gen):
        """RemoteFX is supported only for generation 1 virtual machines

        on Windows 8 / Windows Server 2012 and 2012R2.

        :returns: True if the given vm_gen is 1, False otherwise
        """

        return vm_gen == constants.VM_GEN_1

    def _validate_remotefx_params(self, monitor_count, max_resolution,
                                  vram_bytes=None):
        max_res_value = self._remote_fx_res_map.get(max_resolution)
        if max_res_value is None:
            raise exceptions.HyperVRemoteFXException(
                _("Unsupported RemoteFX resolution: %s") % max_resolution)

        if monitor_count > self._remotefx_max_monitors_map[max_resolution]:
            raise exceptions.HyperVRemoteFXException(
                _("Unsuported RemoteFX monitor count: %(count)s for "
                  "this resolution %(res)s. Hyper-V supports a maximum "
                  "of %(max_monitors)s monitors for this resolution.")
                % {'count': monitor_count,
                   'res': max_resolution,
                   'max_monitors':
                   self._remotefx_max_monitors_map[max_resolution]})

    def _set_remotefx_display_controller(self, vm, remotefx_disp_ctrl_res,
                                         monitor_count, max_resolution,
                                         vram_bytes=None):
        new_wmi_obj = False
        if not remotefx_disp_ctrl_res:
            new_wmi_obj = True
            remotefx_disp_ctrl_res = self._get_new_resource_setting_data(
                self._REMOTEFX_DISP_CTRL_RES_SUB_TYPE,
                self._REMOTEFX_DISP_ALLOCATION_SETTING_DATA_CLASS)

        remotefx_disp_ctrl_res.MaximumMonitors = monitor_count
        remotefx_disp_ctrl_res.MaximumScreenResolution = max_resolution
        self._set_remotefx_vram(remotefx_disp_ctrl_res, vram_bytes)

        if new_wmi_obj:
            self._jobutils.add_virt_resource(remotefx_disp_ctrl_res, vm)
        else:
            self._jobutils.modify_virt_resource(remotefx_disp_ctrl_res)

    def _set_remotefx_vram(self, remotefx_disp_ctrl_res, vram_bytes):
        pass

    def enable_remotefx_video_adapter(self, vm_name, monitor_count,
                                      max_resolution, vram_bytes=None):
        self._validate_remotefx_params(monitor_count, max_resolution,
                                       vram_bytes=vram_bytes)

        vm = self._lookup_vm_check(vm_name)
        rasds = _wqlutils.get_element_associated_class(
            self._compat_conn, self._CIM_RES_ALLOC_SETTING_DATA_CLASS,
            element_instance_id=vm.InstanceID)

        synth_disp_ctrl_res_list = [r for r in rasds if r.ResourceSubType ==
                                    self._SYNTH_DISP_CTRL_RES_SUB_TYPE]
        if synth_disp_ctrl_res_list:
            # we need to remove the generic display controller first.
            self._jobutils.remove_virt_resource(synth_disp_ctrl_res_list[0])

        remotefx_disp_ctrl_res = [r for r in rasds if r.ResourceSubType ==
                                  self._REMOTEFX_DISP_CTRL_RES_SUB_TYPE]
        remotefx_disp_ctrl_res = (remotefx_disp_ctrl_res[0]
                                  if remotefx_disp_ctrl_res else None)

        max_res_value = self._remote_fx_res_map.get(max_resolution)
        self._set_remotefx_display_controller(
            vm, remotefx_disp_ctrl_res, monitor_count, max_res_value,
            vram_bytes)

        if self._vm_has_s3_controller(vm_name):
            s3_disp_ctrl_res = [r for r in rasds if r.ResourceSubType ==
                                self._S3_DISP_CTRL_RES_SUB_TYPE][0]
            if s3_disp_ctrl_res.Address != self._DISP_CTRL_ADDRESS_DX_11:
                s3_disp_ctrl_res.Address = self._DISP_CTRL_ADDRESS_DX_11
                self._jobutils.modify_virt_resource(s3_disp_ctrl_res)

    def disable_remotefx_video_adapter(self, vm_name):
        vm = self._lookup_vm_check(vm_name)
        rasds = _wqlutils.get_element_associated_class(
            self._compat_conn, self._CIM_RES_ALLOC_SETTING_DATA_CLASS,
            element_instance_id=vm.InstanceID)

        remotefx_disp_ctrl_res = [r for r in rasds if r.ResourceSubType ==
                                  self._REMOTEFX_DISP_CTRL_RES_SUB_TYPE]

        if not remotefx_disp_ctrl_res:
            # VM does not have RemoteFX configured.
            return

        # we need to remove the RemoteFX display controller first.
        self._jobutils.remove_virt_resource(remotefx_disp_ctrl_res[0])

        synth_disp_ctrl_res = self._get_new_resource_setting_data(
            self._SYNTH_DISP_CTRL_RES_SUB_TYPE,
            self._SYNTH_DISP_ALLOCATION_SETTING_DATA_CLASS)
        self._jobutils.add_virt_resource(synth_disp_ctrl_res, vm)

        if self._vm_has_s3_controller(vm_name):
            s3_disp_ctrl_res = [r for r in rasds if r.ResourceSubType ==
                                self._S3_DISP_CTRL_RES_SUB_TYPE][0]
            s3_disp_ctrl_res.Address = self._DISP_CTRL_ADDRESS
            self._jobutils.modify_virt_resource(s3_disp_ctrl_res)

    def _vm_has_s3_controller(self, vm_name):
        return True

    def is_secure_vm(self, instance_name):
        return False

    def update_vm_disk_path(self, disk_path, new_disk_path, is_physical=True):
        disk_resource = self._get_mounted_disk_resource_from_path(
            disk_path=disk_path, is_physical=is_physical)
        disk_resource.HostResource = [new_disk_path]
        self._jobutils.modify_virt_resource(disk_resource)

    def add_pci_device(self, vm_name, vendor_id, product_id):
        """Adds the given PCI device to the given VM.

        :raises NotImplemented: PCI passthrough is supported on
            Windows / Hyper-V Server 2016 or newer.
        """
        raise NotImplementedError(_('PCI passthrough is supported on '
                                    'Windows / Hyper-V Server 2016 or newer.'))

    def remove_pci_device(self, vm_name, vendor_id, product_id):
        """Removes the given PCI device from the given VM.

        :raises NotImplemented: PCI passthrough is supported on
            Windows / Hyper-V Server 2016 or newer.
        """
        raise NotImplementedError(_('PCI passthrough is supported on '
                                    'Windows / Hyper-V Server 2016 or newer.'))

    def remove_all_pci_devices(self, vm_name):
        """Removes all the PCI devices from the given VM.

        There are no PCI devices attached to Windows / Hyper-V Server 2012 R2
        or older VMs.
        """

    def _set_vm_snapshot_type(self, vmsettings, snapshot_type):
        # Supported on Windows Server 2016 or newer.
        pass

    def populate_fsk(self, fsk_filepath, fsk_pairs):
        """Writes the given FSK pairs into the give file.

        :raises NotImplementedError: This method is required for Shielded VMs,
            which is supported on Windows / Hyper-V Server 2016 or newer.
        """
        raise NotImplementedError(_('This method is supported on Windows / '
                                    'Hyper-V Server 2016 or newer'))

    def add_vtpm(self, vm_name, pdk_filepath, shielded):
        """Adds a vtpm and enables it with encryption or shielded option.

        :raises NotImplementedError: This method is required for Shielded VMs,
            which is supported on Windows / Hyper-V Server 2016 or newer.
        """
        raise NotImplementedError(_('This method is supported on Windows / '
                                    'Hyper-V Server 2016 or newer'))

    def provision_vm(self, vm_name, fsk_filepath, pdk_filepath):
        """Provisions the given VM with the given FSK and PDK files.

        :raises NotImplementedError: This method is required for Shielded VMs,
            which is supported on Windows / Hyper-V Server 2016 or newer.
        """
        raise NotImplementedError(_('This method is supported on Windows / '
                                    'Hyper-V Server 2016 or newer'))


class VMUtils6_3(VMUtils):

    def set_disk_qos_specs(self, disk_path, max_iops=None, min_iops=None):
        """Sets the disk's QoS policy."""
        if min_iops is None and max_iops is None:
            LOG.debug("Skipping setting disk QoS specs as no "
                      "value was provided.")
            return

        disk_resource = self._get_mounted_disk_resource_from_path(
            disk_path, is_physical=False)

        if max_iops is not None:
            disk_resource.IOPSLimit = max_iops
        if min_iops is not None:
            disk_resource.IOPSReservation = min_iops

        self._jobutils.modify_virt_resource(disk_resource)
