#  Copyright 2015 Cloudbase Solutions Srl
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
import six

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import _wqlutils
from os_win.utils.compute import vmutils10
from os_win.utils import jobutils


@ddt.ddt
class VMUtils10TestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V VMUtils10 class."""

    _autospec_classes = [
        jobutils.JobUtils,
    ]

    _FAKE_PCI_ID = 'Microsoft:ED28B-7BDD0\\PCIP\\VEN_15B3&DEV_1007&SUBSYS_00'
    _FAKE_VENDOR_ID = '15B3'
    _FAKE_PRODUCT_ID = '1007'

    def setUp(self):
        super(VMUtils10TestCase, self).setUp()
        self._vmutils = vmutils10.VMUtils10()
        self._vmutils._conn_attr = mock.MagicMock()
        self._vmutils._conn_msps_attr = mock.MagicMock()

    @mock.patch.object(vmutils10.VMUtils10, '_get_wmi_conn')
    def test_conn_msps(self, mock_get_wmi_conn):
        self._vmutils._conn_msps_attr = None
        self.assertEqual(mock_get_wmi_conn.return_value,
                         self._vmutils._conn_msps)

        mock_get_wmi_conn.assert_called_with(
            self._vmutils._MSPS_NAMESPACE % self._vmutils._host)

    @mock.patch.object(vmutils10.VMUtils10, '_get_wmi_conn')
    def test_conn_msps_no_namespace(self, mock_get_wmi_conn):
        self._vmutils._conn_msps_attr = None

        mock_get_wmi_conn.side_effect = [exceptions.OSWinException]
        self.assertRaises(exceptions.OSWinException,
                          lambda: self._vmutils._conn_msps)
        mock_get_wmi_conn.assert_called_with(
            self._vmutils._MSPS_NAMESPACE % self._vmutils._host)

    def test_sec_svc(self):
        self._vmutils._sec_svc_attr = None
        self.assertEqual(
            self._vmutils._conn.Msvm_SecurityService.return_value[0],
            self._vmutils._sec_svc)

        self._vmutils._conn.Msvm_SecurityService.assert_called_with()

    def test_set_secure_boot_CA_required(self):
        vs_data = mock.MagicMock()
        mock_vssd = self._vmutils._conn.Msvm_VirtualSystemSettingData
        mock_vssd.return_value = [
            mock.MagicMock(SecureBootTemplateId=mock.sentinel.template_id)]

        self._vmutils._set_secure_boot(vs_data, msft_ca_required=True)

        self.assertTrue(vs_data.SecureBootEnabled)
        self.assertEqual(mock.sentinel.template_id,
                         vs_data.SecureBootTemplateId)
        mock_vssd.assert_called_once_with(
            ElementName=self._vmutils._UEFI_CERTIFICATE_AUTH)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(vmutils10.VMUtils10, '_lookup_vm_check')
    def test_set_nested_virtualization(self, mock_lookup_vm_check,
                                       mock_get_element_associated_class):
        mock_vmsettings = mock_lookup_vm_check.return_value
        mock_procsettings = mock_get_element_associated_class.return_value[0]

        self._vmutils.set_nested_virtualization(mock.sentinel.vm_name,
                                                mock.sentinel.state)

        mock_lookup_vm_check.assert_called_once_with(mock.sentinel.vm_name)
        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn, self._vmutils._PROCESSOR_SETTING_DATA_CLASS,
            element_instance_id=mock_vmsettings.InstanceID)
        self.assertEqual(mock.sentinel.state,
                         mock_procsettings.ExposeVirtualizationExtensions)
        self._vmutils._jobutils.modify_virt_resource.assert_called_once_with(
            mock_procsettings)

    def test_vm_gen_supports_remotefx(self):
        ret = self._vmutils.vm_gen_supports_remotefx(mock.sentinel.VM_GEN)

        self.assertTrue(ret)

    def test_validate_remotefx_monitor_count(self):
        self.assertRaises(exceptions.HyperVRemoteFXException,
                          self._vmutils._validate_remotefx_params,
                          10, constants.REMOTEFX_MAX_RES_1024x768)

    def test_validate_remotefx_max_resolution(self):
        self.assertRaises(exceptions.HyperVRemoteFXException,
                          self._vmutils._validate_remotefx_params,
                          1, '1024x700')

    def test_validate_remotefx_vram(self):
        self.assertRaises(exceptions.HyperVRemoteFXException,
                          self._vmutils._validate_remotefx_params,
                          1, constants.REMOTEFX_MAX_RES_1024x768,
                          vram_bytes=10000)

    def test_validate_remotefx(self):
        self._vmutils._validate_remotefx_params(
            1, constants.REMOTEFX_MAX_RES_1024x768)

    def test_set_remotefx_vram(self):
        remotefx_ctrl_res = mock.MagicMock()
        vram_bytes = 512

        self._vmutils._set_remotefx_vram(remotefx_ctrl_res, vram_bytes)
        self.assertEqual(six.text_type(vram_bytes),
                         remotefx_ctrl_res.VRAMSizeBytes)

    @mock.patch.object(vmutils10.VMUtils10, 'get_vm_generation')
    def _test_vm_has_s3_controller(self, vm_gen, mock_get_vm_gen):
        mock_get_vm_gen.return_value = vm_gen
        return self._vmutils._vm_has_s3_controller(mock.sentinel.fake_vm_name)

    def test_vm_has_s3_controller_gen1(self):
        self.assertTrue(self._test_vm_has_s3_controller(constants.VM_GEN_1))

    def test_vm_has_s3_controller_gen2(self):
        self.assertFalse(self._test_vm_has_s3_controller(constants.VM_GEN_2))

    def test_populate_fsk(self):
        fsk_pairs = {mock.sentinel.computer: mock.sentinel.computer_value}

        mock_fabricdata = (
            self._vmutils._conn_msps.Msps_FabricData.new.return_value)

        fsk = self._vmutils._conn_msps.Msps_FSK.new.return_value
        mock_msps_pfp = self._vmutils._conn_msps.Msps_ProvisioningFileProcessor

        self._vmutils.populate_fsk(mock.sentinel.fsk_filepath, fsk_pairs)

        mock_msps_pfp.SerializeToFile.assert_called_once_with(
            mock.sentinel.fsk_filepath, fsk)
        self.assertEqual([mock_fabricdata], fsk.FabricDataPairs)
        self.assertEqual(mock.sentinel.computer, mock_fabricdata.key)
        self.assertEqual(mock.sentinel.computer_value,
                         mock_fabricdata.Value)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(vmutils10.VMUtils10, '_lookup_vm_check')
    def test_add_vtpm(self, mock_lookup_vm_check,
                      mock_get_element_associated_class):
        mock_lookup_vm_check.return_value = mock.Mock(
            ConfigurationID=mock.sentinel.configuration_id)

        mock_msps_pfp = self._vmutils._conn_msps.Msps_ProvisioningFileProcessor
        provisioning_file = mock.Mock(KeyProtector=mock.sentinel.keyprotector,
                                      PolicyData=mock.sentinel.policy)
        mock_msps_pfp.PopulateFromFile.return_value = [provisioning_file]
        security_profile = mock.Mock()

        mock_get_element_associated_class.return_value = [security_profile]
        sec_profile_serialization = security_profile.GetText_.return_value

        mock_sec_svc = self._vmutils._sec_svc
        mock_sec_svc.SetKeyProtector.return_value = (
            mock.sentinel.job_path_SetKeyProtector,
            mock.sentinel.ret_val_SetKeyProtector)
        mock_sec_svc.SetSecurityPolicy.return_value = (
            mock.sentinel.job_path_SetSecurityPolicy,
            mock.sentinel.ret_val_SetSecurityPolicy)
        mock_sec_svc.ModifySecuritySettings.return_value = (
            mock.sentinel.job_path_ModifySecuritySettings,
            mock.sentinel.ret_val_ModifySecuritySettings)

        self._vmutils.add_vtpm(mock.sentinel.VM_NAME,
                               mock.sentinel.pdk_filepath,
                               shielded=True)

        mock_lookup_vm_check.assert_called_with(mock.sentinel.VM_NAME)
        mock_msps_pfp.PopulateFromFile.assert_called_once_with(
            mock.sentinel.pdk_filepath)
        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn,
            self._vmutils._SECURITY_SETTING_DATA,
            element_uuid=mock.sentinel.configuration_id)
        mock_sec_svc.SetKeyProtector.assert_called_once_with(
            mock.sentinel.keyprotector,
            sec_profile_serialization)
        mock_sec_svc.SetSecurityPolicy.assert_called_once_with(
            mock.sentinel.policy, sec_profile_serialization)
        mock_sec_svc.ModifySecuritySettings.assert_called_once_with(
            sec_profile_serialization)

        expected_call = [
            mock.call(mock.sentinel.job_path_SetKeyProtector,
                      mock.sentinel.ret_val_SetKeyProtector),
            mock.call(mock.sentinel.job_path_SetSecurityPolicy,
                      mock.sentinel.ret_val_SetSecurityPolicy),
            mock.call(mock.sentinel.job_path_ModifySecuritySettings,
                      mock.sentinel.ret_val_ModifySecuritySettings)]
        self._vmutils._jobutils.check_ret_val.has_calls(expected_call)
        self.assertTrue(security_profile.EncryptStateAndVmMigrationTraffic)
        self.assertTrue(security_profile.TpmEnabled)
        self.assertTrue(security_profile.ShieldingRequested)

    @mock.patch.object(vmutils10.VMUtils10, '_lookup_vm_check')
    def test_provision_vm(self, mock_lookup_vm_check):
        mock_vm = mock_lookup_vm_check.return_value
        provisioning_srv = self._vmutils._conn_msps.Msps_ProvisioningService

        provisioning_srv.ProvisionMachine.return_value = (
            mock.sentinel.job_path_ProvisionMachine,
            mock.sentinel.ret_val_ProvisionMachine)

        self._vmutils.provision_vm(mock.sentinel.vm_name,
                                   mock.sentinel.fsk_file,
                                   mock.sentinel.pdk_file)

        provisioning_srv.ProvisionMachine.assert_called_once_with(
            mock.sentinel.fsk_file,
            mock_vm.ConfigurationID,
            mock.sentinel.pdk_file)
        self._vmutils._jobutils.check_ret_val.assert_called_once_with(
            mock.sentinel.ret_val_ProvisionMachine,
            mock.sentinel.job_path_ProvisionMachine)

        mock_lookup_vm_check.assert_called_with(mock.sentinel.vm_name)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(vmutils10.VMUtils10, 'get_vm_id')
    def _test_secure_vm(self, mock_get_vm_id,
                        mock_get_element_associated_class,
                        is_encrypted_vm=True):
        inst_id = mock_get_vm_id.return_value
        security_profile = mock.MagicMock()
        mock_get_element_associated_class.return_value = [security_profile]
        security_profile.EncryptStateAndVmMigrationTraffic = is_encrypted_vm

        response = self._vmutils.is_secure_vm(mock.sentinel.instance_name)
        self.assertEqual(is_encrypted_vm, response)

        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn,
            self._vmutils._SECURITY_SETTING_DATA,
            element_uuid=inst_id)

    def test_is_secure_shielded_vm(self):
        self._test_secure_vm()

    def test_not_secure_vm(self):
        self._test_secure_vm(is_encrypted_vm=False)

    @mock.patch.object(vmutils10.VMUtils10, '_get_assignable_pci_device')
    @mock.patch.object(vmutils10.VMUtils10, '_get_new_setting_data')
    @mock.patch.object(vmutils10.VMUtils10, '_lookup_vm_check')
    def test_add_pci_device(self, mock_lookup_vm_check,
                            mock_get_new_setting_data,
                            mock_get_pci_device):
        vmsettings = mock_lookup_vm_check.return_value
        pci_setting_data = mock_get_new_setting_data.return_value
        pci_device = mock_get_pci_device.return_value

        self._vmutils.add_pci_device(mock.sentinel.vm_name,
                                     mock.sentinel.vendor_id,
                                     mock.sentinel.product_id)

        self.assertEqual(pci_setting_data.HostResource,
                         [pci_device.path_.return_value])
        mock_lookup_vm_check.assert_called_once_with(mock.sentinel.vm_name)
        mock_get_new_setting_data.assert_called_once_with(
            self._vmutils._PCI_EXPRESS_SETTING_DATA)
        mock_get_pci_device.assert_called_once_with(
            mock.sentinel.vendor_id, mock.sentinel.product_id)
        self._vmutils._jobutils.add_virt_resource.assert_called_once_with(
            pci_setting_data, vmsettings)

    @ddt.data(True, False)
    def test_get_assignable_pci_device_exception(self, matched):
        product_id = self._FAKE_PRODUCT_ID if matched else '0000'
        pci_dev = mock.MagicMock(DeviceID=self._FAKE_PCI_ID)
        pci_devs = [pci_dev] * 2 if matched else [pci_dev]
        self._vmutils._conn.Msvm_PciExpress.return_value = pci_devs

        self.assertRaises(exceptions.PciDeviceNotFound,
                          self._vmutils._get_assignable_pci_device,
                          self._FAKE_VENDOR_ID, product_id)

        self._vmutils._conn.Msvm_PciExpress.assert_called_once_with()

    def test_get_assignable_pci_device(self):
        pci_dev = mock.MagicMock(DeviceID=self._FAKE_PCI_ID)
        self._vmutils._conn.Msvm_PciExpress.return_value = [pci_dev]

        result = self._vmutils._get_assignable_pci_device(
            self._FAKE_VENDOR_ID, self._FAKE_PRODUCT_ID)

        self.assertEqual(pci_dev, result)
        self._vmutils._conn.Msvm_PciExpress.assert_called_once_with()

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(vmutils10.VMUtils10, '_lookup_vm_check')
    def test_remove_pci_device(self, mock_lookup_vm_check,
                               mock_get_element_associated_class):
        vmsettings = mock_lookup_vm_check.return_value
        pci_setting_data = mock.MagicMock(HostResource=(self._FAKE_PCI_ID, ))
        bad_pci_setting_data = mock.MagicMock(HostResource=('', ))
        mock_get_element_associated_class.return_value = [
            bad_pci_setting_data, pci_setting_data]

        self._vmutils.remove_pci_device(mock.sentinel.vm_name,
                                        self._FAKE_VENDOR_ID,
                                        self._FAKE_PRODUCT_ID)

        mock_lookup_vm_check.assert_called_once_with(mock.sentinel.vm_name)
        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn, self._vmutils._PCI_EXPRESS_SETTING_DATA,
            vmsettings.InstanceID)
        self._vmutils._jobutils.remove_virt_resource.assert_called_once_with(
            pci_setting_data)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(vmutils10.VMUtils10, '_lookup_vm_check')
    def test_remove_all_pci_devices(self, mock_lookup_vm_check,
                                    mock_get_element_associated_class):
        vmsettings = mock_lookup_vm_check.return_value

        self._vmutils.remove_all_pci_devices(mock.sentinel.vm_name)

        mock_lookup_vm_check.assert_called_once_with(mock.sentinel.vm_name)
        mock_get_element_associated_class.assert_called_once_with(
            self._vmutils._conn, self._vmutils._PCI_EXPRESS_SETTING_DATA,
            vmsettings.InstanceID)
        mock_remove_multiple_virt_resource = (
            self._vmutils._jobutils.remove_multiple_virt_resources)
        mock_remove_multiple_virt_resource.assert_called_once_with(
            mock_get_element_associated_class.return_value)

    def test_set_snapshot_type(self):
        vmsettings = mock.Mock(Version='6.2')

        self._vmutils._set_vm_snapshot_type(
            vmsettings, mock.sentinel.snapshot_type)

        self.assertEqual(mock.sentinel.snapshot_type,
                         vmsettings.UserSnapshotType)
