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

import re

from oslo_log import log as logging
import six

from os_win._i18n import _
from os_win import _utils
from os_win import constants
from os_win import exceptions
from os_win.utils import _wqlutils
from os_win.utils.compute import vmutils
from oslo_utils import units

LOG = logging.getLogger(__name__)


class VMUtils10(vmutils.VMUtils6_3):

    _UEFI_CERTIFICATE_AUTH = 'MicrosoftUEFICertificateAuthority'
    _SERIAL_PORT_SETTING_DATA_CLASS = "Msvm_SerialPortSettingData"
    _SECURITY_SETTING_DATA = 'Msvm_SecuritySettingData'
    _PCI_EXPRESS_SETTING_DATA = 'Msvm_PciExpressSettingData'
    _MSPS_NAMESPACE = '//%s/root/msps'

    _remote_fx_res_map = {
        constants.REMOTEFX_MAX_RES_1024x768: 0,
        constants.REMOTEFX_MAX_RES_1280x1024: 1,
        constants.REMOTEFX_MAX_RES_1600x1200: 2,
        constants.REMOTEFX_MAX_RES_1920x1200: 3,
        constants.REMOTEFX_MAX_RES_2560x1600: 4,
        constants.REMOTEFX_MAX_RES_3840x2160: 5
    }

    _remotefx_max_monitors_map = {
        # defines the maximum number of monitors for a given
        # resolution
        constants.REMOTEFX_MAX_RES_1024x768: 8,
        constants.REMOTEFX_MAX_RES_1280x1024: 8,
        constants.REMOTEFX_MAX_RES_1600x1200: 4,
        constants.REMOTEFX_MAX_RES_1920x1200: 4,
        constants.REMOTEFX_MAX_RES_2560x1600: 2,
        constants.REMOTEFX_MAX_RES_3840x2160: 1
    }

    _remotefx_vram_vals = [64 * units.Mi, 128 * units.Mi, 256 * units.Mi,
                           512 * units.Mi, 1024 * units.Mi]

    def __init__(self, host='.'):
        super(VMUtils10, self).__init__(host)
        self._conn_msps_attr = None
        self._sec_svc_attr = None

    @property
    def _conn_msps(self):
        if not self._conn_msps_attr:
            try:
                namespace = self._MSPS_NAMESPACE % self._host
                self._conn_msps_attr = self._get_wmi_conn(namespace)
            except Exception:
                raise exceptions.OSWinException(
                    _("Namespace %(namespace)s not found. Make sure "
                      "FabricShieldedTools feature is installed.") %
                    {'namespace': namespace})

        return self._conn_msps_attr

    @property
    def _sec_svc(self):
        if not self._sec_svc_attr:
            self._sec_svc_attr = self._conn.Msvm_SecurityService()[0]
        return self._sec_svc_attr

    def set_nested_virtualization(self, vm_name, state):
        """Enables nested virtualization for the given VM.

        :param vm_name: the name of the VM.
        :param state: boolean, if True, nested virtualization will be enabled,
            disabled otherwise.
        """
        vmsettings = self._lookup_vm_check(vm_name)
        procsettings = _wqlutils.get_element_associated_class(
            self._conn, self._PROCESSOR_SETTING_DATA_CLASS,
            element_instance_id=vmsettings.InstanceID)[0]

        procsettings.ExposeVirtualizationExtensions = state
        self._jobutils.modify_virt_resource(procsettings)

    def vm_gen_supports_remotefx(self, vm_gen):
        """RemoteFX is supported on both generation 1 and 2 virtual

        machines for Windows 10 / Windows Server 2016.

        :returns: True
        """

        return True

    def _validate_remotefx_params(self, monitor_count, max_resolution,
                                  vram_bytes=None):
        super(VMUtils10, self)._validate_remotefx_params(monitor_count,
                                                         max_resolution)
        if vram_bytes and vram_bytes not in self._remotefx_vram_vals:
            raise exceptions.HyperVRemoteFXException(
                _("Unsuported RemoteFX VRAM value: %(requested_value)s."
                  "The supported VRAM values are: %(supported_values)s") %
                {'requested_value': vram_bytes,
                 'supported_values': self._remotefx_vram_vals})

    def _set_remotefx_vram(self, remotefx_disp_ctrl_res, vram_bytes):
        if vram_bytes:
            remotefx_disp_ctrl_res.VRAMSizeBytes = six.text_type(vram_bytes)

    def _vm_has_s3_controller(self, vm_name):
        return self.get_vm_generation(vm_name) == constants.VM_GEN_1

    def _set_secure_boot(self, vs_data, msft_ca_required):
        vs_data.SecureBootEnabled = True
        if msft_ca_required:
            uefi_data = self._conn.Msvm_VirtualSystemSettingData(
                ElementName=self._UEFI_CERTIFICATE_AUTH)[0]
            vs_data.SecureBootTemplateId = uefi_data.SecureBootTemplateId

    def populate_fsk(self, fsk_filepath, fsk_pairs):
        """Writes in the fsk file all the substitution strings and their

        values which will populate the unattended file used when
        creating the pdk.
        """

        fabric_data_pairs = []
        for fsk_key, fsk_value in fsk_pairs.items():
            fabricdata = self._conn_msps.Msps_FabricData.new()
            fabricdata.key = fsk_key
            fabricdata.Value = fsk_value
            fabric_data_pairs.append(fabricdata)

        fsk = self._conn_msps.Msps_FSK.new()
        fsk.FabricDataPairs = fabric_data_pairs
        msps_pfp = self._conn_msps.Msps_ProvisioningFileProcessor

        msps_pfp.SerializeToFile(fsk_filepath, fsk)

    def add_vtpm(self, vm_name, pdk_filepath, shielded):
        """Adds a vtpm and enables it with encryption or shielded option."""

        vm = self._lookup_vm_check(vm_name)

        msps_pfp = self._conn_msps.Msps_ProvisioningFileProcessor
        provisioning_file = msps_pfp.PopulateFromFile(pdk_filepath)[0]
        # key_protector: array of bytes
        key_protector = provisioning_file.KeyProtector
        # policy_data: array of bytes
        policy_data = provisioning_file.PolicyData

        security_profile = _wqlutils.get_element_associated_class(
            self._conn, self._SECURITY_SETTING_DATA,
            element_uuid=vm.ConfigurationID)[0]

        security_profile.EncryptStateAndVmMigrationTraffic = True
        security_profile.TpmEnabled = True
        security_profile.ShieldingRequested = shielded

        sec_profile_serialized = security_profile.GetText_(1)
        (job_path, ret_val) = self._sec_svc.SetKeyProtector(
            key_protector, sec_profile_serialized)
        self._jobutils.check_ret_val(ret_val, job_path)

        (job_path, ret_val) = self._sec_svc.SetSecurityPolicy(
            policy_data, sec_profile_serialized)
        self._jobutils.check_ret_val(ret_val, job_path)

        (job_path, ret_val) = self._sec_svc.ModifySecuritySettings(
            sec_profile_serialized)
        self._jobutils.check_ret_val(ret_val, job_path)

    def provision_vm(self, vm_name, fsk_filepath, pdk_filepath):
        vm = self._lookup_vm_check(vm_name)
        provisioning_service = self._conn_msps.Msps_ProvisioningService

        (job_path, ret_val) = provisioning_service.ProvisionMachine(
            fsk_filepath, vm.ConfigurationID, pdk_filepath)
        self._jobutils.check_ret_val(ret_val, job_path)

    def is_secure_vm(self, instance_name):
        inst_id = self.get_vm_id(instance_name)
        security_profile = _wqlutils.get_element_associated_class(
            self._conn, self._SECURITY_SETTING_DATA,
            element_uuid=inst_id)
        if security_profile:
            return security_profile[0].EncryptStateAndVmMigrationTraffic
        return False

    def add_pci_device(self, vm_name, vendor_id, product_id):
        """Adds the given PCI device to the given VM.

        :param vm_name: the name of the VM to which the PCI device will be
            attached to.
        :param vendor_id: the PCI device's vendor ID.
        :param product_id: the PCI device's product ID.
        :raises exceptions.PciDeviceNotFound: if there is no PCI device
            identifiable by the given vendor_id and product_id, or it was
            already assigned.
        """
        vmsettings = self._lookup_vm_check(vm_name)
        pci_setting_data = self._get_new_setting_data(
            self._PCI_EXPRESS_SETTING_DATA)
        pci_device = self._get_assignable_pci_device(vendor_id, product_id)
        pci_setting_data.HostResource = [pci_device.path_()]

        self._jobutils.add_virt_resource(pci_setting_data, vmsettings)

    def _get_assignable_pci_device(self, vendor_id, product_id):
        pci_devices = self._conn.Msvm_PciExpress()

        pattern = re.compile(
            "^(.*)VEN_%(vendor_id)s&DEV_%(product_id)s&(.*)$" % {
                'vendor_id': vendor_id, 'product_id': product_id},
            re.IGNORECASE)
        for dev in pci_devices:
            if pattern.match(dev.DeviceID):
                # NOTE(claudiub): if the given PCI device is already assigned,
                # the pci_devices list will contain PCI device with the same
                # LocationPath.
                pci_devices_found = [d for d in pci_devices if
                                     d.LocationPath == dev.LocationPath]

                LOG.debug('PCI devices found: %s',
                          [d.DeviceID for d in pci_devices_found])

                # device is not in use by other VM
                if len(pci_devices_found) == 1:
                    return pci_devices_found[0]

        raise exceptions.PciDeviceNotFound(vendor_id=vendor_id,
                                           product_id=product_id)

    def remove_pci_device(self, vm_name, vendor_id, product_id):
        """Removes the given PCI device from the given VM.

        :param vm_name: the name of the VM from which the PCI device will be
            attached from.
        :param vendor_id: the PCI device's vendor ID.
        :param product_id: the PCI device's product ID.
        """
        vmsettings = self._lookup_vm_check(vm_name)

        pattern = re.compile(
            "^(.*)VEN_%(vendor_id)s&DEV_%(product_id)s&(.*)$" % {
                'vendor_id': vendor_id, 'product_id': product_id},
            re.IGNORECASE)

        pci_sds = _wqlutils.get_element_associated_class(
            self._conn, self._PCI_EXPRESS_SETTING_DATA,
            vmsettings.InstanceID)
        pci_sds = [sd for sd in pci_sds if pattern.match(sd.HostResource[0])]

        if pci_sds:
            self._jobutils.remove_virt_resource(pci_sds[0])
        else:
            LOG.debug("PCI device with vendor ID %(vendor_id)s and "
                      "%(product_id)s is not attached to %(vm_name)s",
                      {'vendor_id': vendor_id, 'product_id': product_id,
                       'vm_name': vm_name})

    def remove_all_pci_devices(self, vm_name):
        """Removes all the PCI devices from the given VM.

        :param vm_name: the name of the VM from which all the PCI devices will
            be detached from.
        """
        vmsettings = self._lookup_vm_check(vm_name)

        pci_sds = _wqlutils.get_element_associated_class(
            self._conn, self._PCI_EXPRESS_SETTING_DATA,
            vmsettings.InstanceID)

        if pci_sds:
            self._jobutils.remove_multiple_virt_resources(pci_sds)

    @_utils.required_vm_version(min_version=constants.VM_VERSION_6_2)
    def _set_vm_snapshot_type(self, vmsettings, snapshot_type):
        # We expect the caller to actually push the vmsettings update.
        vmsettings.UserSnapshotType = snapshot_type
