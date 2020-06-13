#  Copyright 2014 Cloudbase Solutions Srl
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
from oslo_utils import units

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import _wqlutils
from os_win.utils.network import networkutils


@ddt.ddt
class NetworkUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V NetworkUtils class."""

    _autospec_classes = [
        networkutils.jobutils.JobUtils,
    ]

    _FAKE_VSWITCH_NAME = "fake_vswitch_name"
    _FAKE_PORT_NAME = "fake_port_name"
    _FAKE_JOB_PATH = 'fake_job_path'
    _FAKE_RET_VAL = 0
    _FAKE_RES_PATH = "fake_res_path"
    _FAKE_VSWITCH = "fake_vswitch"
    _FAKE_VLAN_ID = "fake_vlan_id"
    _FAKE_CLASS_NAME = "fake_class_name"
    _FAKE_ELEMENT_NAME = "fake_element_name"
    _FAKE_HYPERV_VM_STATE = 'fake_hyperv_state'

    _FAKE_ACL_ACT = 'fake_acl_action'
    _FAKE_ACL_DIR = 'fake_acl_dir'
    _FAKE_ACL_TYPE = 'fake_acl_type'
    _FAKE_LOCAL_PORT = 'fake_local_port'
    _FAKE_PROTOCOL = 'fake_port_protocol'
    _FAKE_REMOTE_ADDR = '0.0.0.0/0'
    _FAKE_WEIGHT = 'fake_weight'

    _FAKE_BAD_INSTANCE_ID = 'bad_instance_id'
    _FAKE_INSTANCE_ID = (
        r"Microsoft:609CBAAD-BC13-4A65-AADE-AD95861FE394\\55349F56-72AB-4FA3-"
        "B5FE-6A30A511A419\\C\\776E0BA7-94A1-41C8-8F28-951F524251B5\\77A43184-"
        "5444-49BF-ABE0-2210B72ABA73")

    _MSVM_VIRTUAL_SWITCH = 'Msvm_VirtualEthernetSwitch'

    def setUp(self):
        super(NetworkUtilsTestCase, self).setUp()
        self.netutils = networkutils.NetworkUtils()
        self.netutils._conn_attr = mock.MagicMock()

    def test_init_caches_disabled(self):
        self.netutils._enable_cache = False
        self.netutils._switches = {}
        self.netutils.init_caches()

        self.netutils._conn.Msvm_VirtualEthernetSwitch.assert_not_called()
        self.assertEqual({}, self.netutils._switches)

    def test_init_caches(self):
        self.netutils._enable_cache = True

        self.netutils._switches = {}
        self.netutils._switch_ports = {}
        self.netutils._vlan_sds = {}
        self.netutils._profile_sds = {}
        self.netutils._hw_offload_sds = {}
        self.netutils._vsid_sds = {}
        self.netutils._bandwidth_sds = {}
        conn = self.netutils._conn

        mock_vswitch = mock.MagicMock(ElementName=mock.sentinel.vswitch_name)
        conn.Msvm_VirtualEthernetSwitch.return_value = [mock_vswitch]

        mock_port = mock.MagicMock(ElementName=mock.sentinel.port_name)
        conn.Msvm_EthernetPortAllocationSettingData.return_value = [
            mock_port]

        mock_sd = mock.MagicMock(InstanceID=self._FAKE_INSTANCE_ID)
        mock_bad_sd = mock.MagicMock(InstanceID=self._FAKE_BAD_INSTANCE_ID)
        conn.Msvm_EthernetSwitchPortProfileSettingData.return_value = [
            mock_bad_sd, mock_sd]
        conn.Msvm_EthernetSwitchPortVlanSettingData.return_value = [
            mock_bad_sd, mock_sd]
        conn.Msvm_EthernetSwitchPortSecuritySettingData.return_value = [
            mock_bad_sd, mock_sd]
        conn.Msvm_EthernetSwitchPortBandwidthSettingData.return_value = [
            mock_bad_sd, mock_sd]
        conn.Msvm_EthernetSwitchPortOffloadSettingData.return_value = [
            mock_bad_sd, mock_sd]

        self.netutils.init_caches()

        self.assertEqual({mock.sentinel.vswitch_name: mock_vswitch},
                         self.netutils._switches)
        self.assertEqual({mock.sentinel.port_name: mock_port},
                         self.netutils._switch_ports)
        self.assertEqual([mock_sd], list(self.netutils._profile_sds.values()))
        self.assertEqual([mock_sd], list(self.netutils._vlan_sds.values()))
        self.assertEqual([mock_sd], list(self.netutils._vsid_sds.values()))
        self.assertEqual([mock_sd],
                         list(self.netutils._bandwidth_sds.values()))
        self.assertEqual([mock_sd],
                         list(self.netutils._hw_offload_sds.values()))

    def test_update_cache_disabled(self):
        self.netutils._enable_cache = False
        self.netutils._switch_ports = {}
        self.netutils.update_cache()

        conn = self.netutils._conn
        conn.Msvm_EthernetPortAllocationSettingData.assert_not_called()
        self.assertEqual({}, self.netutils._switch_ports)

    def test_update_cache(self):
        self.netutils._enable_cache = True

        self.netutils._switch_ports[mock.sentinel.other] = mock.sentinel.port
        conn = self.netutils._conn
        mock_port = mock.MagicMock(ElementName=mock.sentinel.port_name)
        conn.Msvm_EthernetPortAllocationSettingData.return_value = [
            mock_port]

        self.netutils.update_cache()

        self.assertEqual({mock.sentinel.port_name: mock_port},
                         self.netutils._switch_ports)

        # assert that other networkutils have the same cache.
        netutils = networkutils.NetworkUtils()
        self.assertEqual({mock.sentinel.port_name: mock_port},
                         netutils._switch_ports)

    def test_clear_port_sg_acls_cache(self):
        self.netutils._sg_acl_sds[mock.sentinel.port_id] = [mock.sentinel.acl]
        self.netutils.clear_port_sg_acls_cache(mock.sentinel.port_id)
        self.assertNotIn(mock.sentinel.acl, self.netutils._sg_acl_sds)

    @mock.patch.object(networkutils.NetworkUtils, '_get_vswitch_external_port')
    def test_get_vswitch_external_network_name(self, mock_get_vswitch_port):
        mock_get_vswitch_port.return_value.ElementName = (
            mock.sentinel.network_name)
        result = self.netutils.get_vswitch_external_network_name(
            mock.sentinel.vswitch_name)
        self.assertEqual(mock.sentinel.network_name, result)

    def test_get_vswitch_external_port(self):
        vswitch = mock.MagicMock(Name=mock.sentinel.vswitch_name)
        self.netutils._conn.Msvm_VirtualEthernetSwitch.return_value = [vswitch]

        conn = self.netutils._conn
        ext_port = mock.MagicMock()
        lan_endpoint_assoc1 = mock.MagicMock()
        lan_endpoint_assoc2 = mock.Mock(SystemName=mock.sentinel.vswitch_name)
        self.netutils._conn.Msvm_ExternalEthernetPort.return_value = [ext_port]
        conn.Msvm_EthernetDeviceSAPImplementation.return_value = [
            lan_endpoint_assoc1]
        conn.Msvm_ActiveConnection.return_value = [
            mock.Mock(Antecedent=lan_endpoint_assoc2)]

        result = self.netutils._get_vswitch_external_port(mock.sentinel.name)
        self.assertEqual(ext_port, result)
        conn.Msvm_EthernetDeviceSAPImplementation.assert_called_once_with(
            Antecedent=ext_port.path_.return_value)
        conn.Msvm_ActiveConnection.assert_called_once_with(
            Dependent=lan_endpoint_assoc1.Dependent.path_.return_value)

    def test_vswitch_port_needed(self):
        self.assertFalse(self.netutils.vswitch_port_needed())

    @mock.patch.object(networkutils.NetworkUtils, '_get_vnic_settings')
    def test_get_vnic_mac_address(self, mock_get_vnic_settings):
        mock_vnic = mock.MagicMock(Address=mock.sentinel.mac_address)
        mock_get_vnic_settings.return_value = mock_vnic

        actual_mac_address = self.netutils.get_vnic_mac_address(
            mock.sentinel.switch_port_name)
        self.assertEqual(mock.sentinel.mac_address, actual_mac_address)

    @ddt.data([], [mock.sentinel.nic_sd])
    def test_get_vnic_settings(self, nic_sds):
        mock_nic_sd = self.netutils._conn.Msvm_SyntheticEthernetPortSettingData
        mock_nic_sd.return_value = nic_sds

        if not nic_sds:
            self.assertRaises(exceptions.HyperVvNicNotFound,
                              self.netutils._get_vnic_settings,
                              mock.sentinel.vnic_name)
        else:
            nic_sd = self.netutils._get_vnic_settings(mock.sentinel.vnic_name)
            self.assertEqual(mock.sentinel.nic_sd, nic_sd)

        mock_nic_sd.assert_called_once_with(
            ElementName=mock.sentinel.vnic_name)

    @mock.patch.object(networkutils, 'patcher')
    @mock.patch.object(networkutils.tpool, 'execute')
    @mock.patch.object(networkutils.NetworkUtils, '_get_event_wql_query')
    def test_get_vnic_event_listener(self, mock_get_event_query,
                                     mock_execute, mock_patcher):
        event = mock.MagicMock()
        # This event should be ignored.
        unnamed_port_event = mock.MagicMock(ElementName=None)
        port_class = self.netutils._conn.Msvm_SyntheticEthernetPortSettingData
        wmi_event_listener = port_class.watch_for.return_value
        mock_execute.side_effect = [exceptions.x_wmi_timed_out,
                                    unnamed_port_event, event]

        # callback will raise an exception in order to stop iteration in the
        # listener.
        callback = mock.MagicMock(side_effect=TypeError)

        returned_listener = self.netutils.get_vnic_event_listener(
            self.netutils.EVENT_TYPE_CREATE)
        self.assertRaises(TypeError, returned_listener, callback)

        mock_get_event_query.assert_called_once_with(
            cls=self.netutils._VNIC_SET_DATA,
            event_type=self.netutils.EVENT_TYPE_CREATE,
            timeframe=2)
        port_class.watch_for.assert_called_once_with(
            mock_get_event_query.return_value)
        mock_execute.assert_has_calls(
            [mock.call(wmi_event_listener,
                       self.netutils._VNIC_LISTENER_TIMEOUT_MS)] * 3)
        callback.assert_called_once_with(event.ElementName)

    def test_get_event_wql_query(self):
        expected = ("SELECT * FROM %(event_type)s WITHIN %(timeframe)s "
                    "WHERE TargetInstance ISA '%(class)s' AND "
                    "%(like)s" % {
                        'class': "FakeClass",
                        'event_type': self.netutils.EVENT_TYPE_CREATE,
                        'like': "TargetInstance.foo LIKE 'bar%'",
                        'timeframe': 2})

        query = self.netutils._get_event_wql_query(
            "FakeClass", self.netutils.EVENT_TYPE_CREATE, like=dict(foo="bar"))

        self.assertEqual(expected, query)

    def test_connect_vnic_to_vswitch_found(self):
        self._test_connect_vnic_to_vswitch(True)

    def test_connect_vnic_to_vswitch_not_found(self):
        self._test_connect_vnic_to_vswitch(False)

    def _test_connect_vnic_to_vswitch(self, found):
        self.netutils._get_vnic_settings = mock.MagicMock()

        if not found:
            mock_vm = mock.MagicMock()
            self.netutils._get_vm_from_res_setting_data = mock.MagicMock(
                return_value=mock_vm)
            self.netutils._add_virt_resource = mock.MagicMock()
        else:
            self.netutils._modify_virt_resource = mock.MagicMock()

        self.netutils._get_vswitch = mock.MagicMock()
        mock_port = self._mock_get_switch_port_alloc(found=found)
        mock_port.HostResource = []

        self.netutils.connect_vnic_to_vswitch(self._FAKE_VSWITCH_NAME,
                                              self._FAKE_PORT_NAME)

        if not found:
            mock_add_resource = self.netutils._jobutils.add_virt_resource
            mock_add_resource.assert_called_once_with(mock_port, mock_vm)
        else:
            mock_modify_resource = self.netutils._jobutils.modify_virt_resource
            mock_modify_resource.assert_called_once_with(mock_port)

    def test_connect_vnic_to_vswitch_already_connected(self):
        mock_port = self._mock_get_switch_port_alloc()
        mock_port.HostResource = [mock.sentinel.vswitch_path]

        self.netutils.connect_vnic_to_vswitch(mock.sentinel.switch_name,
                                              mock.sentinel.port_name)

        self.assertFalse(self.netutils._jobutils.modify_virt_resource.called)

    def _mock_get_switch_port_alloc(self, found=True):
        mock_port = mock.MagicMock()
        patched = mock.patch.object(
            self.netutils, '_get_switch_port_allocation',
            return_value=(mock_port, found))
        patched.start()
        self.addCleanup(patched.stop)
        return mock_port

    def test_get_vm_from_res_setting_data(self):
        fake_res_set_instance_id = "Microsoft:GUID\\SpecificData"
        fake_vm_set_instance_id = "Microsoft:GUID"
        res_setting_data = mock.Mock(InstanceID=fake_res_set_instance_id)
        conn = self.netutils._conn
        mock_setting_data = conn.Msvm_VirtualSystemSettingData.return_value

        resulted_vm = self.netutils._get_vm_from_res_setting_data(
            res_setting_data)

        conn.Msvm_VirtualSystemSettingData.assert_called_once_with(
            InstanceID=fake_vm_set_instance_id)
        conn.Msvm_ComputerSystem.assert_called_once_with(
            Name=mock_setting_data[0].ConfigurationID)
        expected_result = conn.Msvm_ComputerSystem.return_value[0]
        self.assertEqual(expected_result, resulted_vm)

    def test_remove_switch_port(self):
        mock_sw_port = self._mock_get_switch_port_alloc()
        self.netutils._switch_ports[self._FAKE_PORT_NAME] = mock_sw_port
        self.netutils._vlan_sds[mock_sw_port.InstanceID] = mock.MagicMock()
        self.netutils._jobutils.remove_virt_resource.side_effect = (
            exceptions.x_wmi)

        self.netutils.remove_switch_port(self._FAKE_PORT_NAME, False)

        self.netutils._jobutils.remove_virt_resource.assert_called_once_with(
            mock_sw_port)
        self.assertNotIn(self._FAKE_PORT_NAME, self.netutils._switch_ports)
        self.assertNotIn(mock_sw_port.InstanceID, self.netutils._vlan_sds)

    @ddt.data(True, False)
    def test_get_vswitch(self, enable_cache):
        self.netutils._enable_cache = enable_cache
        self.netutils._switches = {}
        self.netutils._conn.Msvm_VirtualEthernetSwitch.return_value = [
            self._FAKE_VSWITCH]
        vswitch = self.netutils._get_vswitch(self._FAKE_VSWITCH_NAME)

        expected_cache = ({self._FAKE_VSWITCH_NAME: self._FAKE_VSWITCH} if
                          enable_cache else {})
        self.assertEqual(expected_cache, self.netutils._switches)
        self.assertEqual(self._FAKE_VSWITCH, vswitch)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_vswitch')
    def test_get_vswitch_extensions(self, mock_get_vswitch):
        mock_vswitch = mock_get_vswitch.return_value
        mock_ext = mock.Mock()
        ext_cls = self.netutils._conn.Msvm_EthernetSwitchExtension
        ext_cls.return_value = [mock_ext] * 2

        extensions = self.netutils.get_vswitch_extensions(
            mock.sentinel.vswitch_name)
        exp_extensions = [
            {'name': mock_ext.ElementName,
             'version': mock_ext.Version,
             'vendor': mock_ext.Vendor,
             'description': mock_ext.Description,
             'enabled_state': mock_ext.EnabledState,
             'extension_type': mock_ext.ExtensionType}] * 2

        self.assertEqual(exp_extensions, extensions)

        mock_get_vswitch.assert_called_once_with(
            mock.sentinel.vswitch_name)
        ext_cls.assert_called_once_with(
            SystemName=mock_vswitch.Name)

    def test_get_vswitch_cache(self):
        self.netutils._switches = {
            self._FAKE_VSWITCH_NAME: mock.sentinel.vswitch}

        vswitch = self.netutils._get_vswitch(self._FAKE_VSWITCH_NAME)
        self.assertEqual(mock.sentinel.vswitch, vswitch)

    def test_get_vswitch_not_found(self):
        self.netutils._switches = {}
        self.netutils._conn.Msvm_VirtualEthernetSwitch.return_value = []
        self.assertRaises(exceptions.HyperVvSwitchNotFound,
                          self.netutils._get_vswitch,
                          self._FAKE_VSWITCH_NAME)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_prepare_profile_sd')
    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_profile_setting_data_from_port_alloc')
    def _test_set_vswitch_port_profile_id(
            self, mock_get_profile_setting_data_from_port_alloc,
            mock_prepare_profile_sd, found, side_effect=None):
        mock_port_profile = mock.MagicMock()
        mock_new_port_profile = mock.MagicMock()
        mock_port_alloc = self._mock_get_switch_port_alloc()

        mock_add_feature = self.netutils._jobutils.add_virt_feature
        mock_remove_feature = self.netutils._jobutils.remove_virt_feature

        mock_get_profile_setting_data_from_port_alloc.return_value = (
            mock_port_profile if found else None
        )
        mock_prepare_profile_sd.return_value = mock_new_port_profile
        mock_add_feature.side_effect = side_effect

        fake_params = {
            "switch_port_name": self._FAKE_PORT_NAME,
            "profile_id": mock.sentinel.profile_id,
            "profile_data": mock.sentinel.profile_data,
            "profile_name": mock.sentinel.profile_name,
            "net_cfg_instance_id": None,
            "cdn_label_id": None,
            "cdn_label_string": None,
            "vendor_id": None,
            "vendor_name": mock.sentinel.vendor_name,
        }

        if side_effect:
            self.assertRaises(
                exceptions.HyperVException,
                self.netutils.set_vswitch_port_profile_id,
                **fake_params)
        else:
            self.netutils.set_vswitch_port_profile_id(**fake_params)

        fake_params.pop("switch_port_name")
        mock_prepare_profile_sd.assert_called_once_with(**fake_params)

        if found:
            mock_remove_feature.assert_called_once_with(mock_port_profile)
            self.assertNotIn(self._FAKE_INSTANCE_ID,
                             self.netutils._profile_sds)

        mock_get_profile_setting_data_from_port_alloc.assert_called_with(
            mock_port_alloc)

        self.assertNotIn(mock_port_alloc, self.netutils._profile_sds)
        mock_add_feature.assert_called_once_with(mock_new_port_profile,
                                                 mock_port_alloc)

    def test_set_vswitch_port_profile_id(self):
        self._test_set_vswitch_port_profile_id(found=True)

    def test_set_vswitch_port_profile_id_not_found(self):
        self._test_set_vswitch_port_profile_id(found=False)

    def test_set_vswitch_port_profile_id_failed(self):
        self._test_set_vswitch_port_profile_id(found=False,
                                               side_effect=Exception)

    def test_set_vswitch_port_vlan_id_invalid_mode(self):
        self.assertRaises(
            AttributeError, self.netutils.set_vswitch_port_vlan_id,
            mock.sentinel.vlan_id, mock.sentinel.switch_port_name,
            operation_mode=mock.sentinel.invalid_mode)

    def test_set_vswitch_port_vlan_id_access_mode_trunked(self):
        self.assertRaises(
            AttributeError, self.netutils.set_vswitch_port_vlan_id,
            mock.sentinel.vlan_id, mock.sentinel.switch_port_name,
            trunk_vlans=[mock.sentinel.vlan_id])

    @mock.patch.object(networkutils.NetworkUtils,
                       '_prepare_vlan_sd_trunk_mode')
    @mock.patch.object(networkutils.NetworkUtils,
                       '_prepare_vlan_sd_access_mode')
    def _check_set_vswitch_port_vlan_id(self, mock_prepare_vlan_sd_access,
                                        mock_prepare_vlan_sd_trunk,
                                        op_mode=constants.VLAN_MODE_ACCESS,
                                        missing_vlan=False):
        mock_port = self._mock_get_switch_port_alloc(found=True)
        old_vlan_settings = mock.MagicMock()
        if missing_vlan:
            side_effect = [old_vlan_settings, None]
        else:
            side_effect = [old_vlan_settings, old_vlan_settings]
        self.netutils._get_vlan_setting_data_from_port_alloc = mock.MagicMock(
            side_effect=side_effect)
        mock_vlan_settings = mock.MagicMock()
        mock_prepare_vlan_sd_access.return_value = mock_vlan_settings
        mock_prepare_vlan_sd_trunk.return_value = mock_vlan_settings

        if missing_vlan:
            self.assertRaises(exceptions.HyperVException,
                              self.netutils.set_vswitch_port_vlan_id,
                              self._FAKE_VLAN_ID, self._FAKE_PORT_NAME,
                              operation_mode=op_mode)
        else:
            self.netutils.set_vswitch_port_vlan_id(
                self._FAKE_VLAN_ID, self._FAKE_PORT_NAME,
                operation_mode=op_mode)

        if op_mode == constants.VLAN_MODE_ACCESS:
            mock_prepare_vlan_sd_access.assert_called_once_with(
                old_vlan_settings, self._FAKE_VLAN_ID)
        else:
            mock_prepare_vlan_sd_trunk.assert_called_once_with(
                old_vlan_settings, self._FAKE_VLAN_ID, None)

        mock_remove_feature = self.netutils._jobutils.remove_virt_feature
        mock_remove_feature.assert_called_once_with(old_vlan_settings)
        mock_add_feature = self.netutils._jobutils.add_virt_feature
        mock_add_feature.assert_called_once_with(mock_vlan_settings, mock_port)

    def test_set_vswitch_port_vlan_id_access(self):
        self._check_set_vswitch_port_vlan_id()

    def test_set_vswitch_port_vlan_id_trunk(self):
        self._check_set_vswitch_port_vlan_id(op_mode=constants.VLAN_MODE_TRUNK)

    def test_set_vswitch_port_vlan_id_missing(self):
        self._check_set_vswitch_port_vlan_id(missing_vlan=True)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_prepare_vlan_sd_access_mode')
    def test_set_vswitch_port_vlan_id_already_set(self, mock_prepare_vlan_sd):
        self._mock_get_switch_port_alloc()
        mock_prepare_vlan_sd.return_value = None

        self.netutils.set_vswitch_port_vlan_id(mock.sentinel.vlan_id,
                                               mock.sentinel.port_name)

        mock_remove_feature = self.netutils._jobutils.remove_virt_feature
        self.assertFalse(mock_remove_feature.called)

    def test_prepare_vlan_sd_access_mode_already_set(self):
        mock_vlan_sd = mock.MagicMock(OperationMode=constants.VLAN_MODE_ACCESS,
                                      AccessVlanId=mock.sentinel.vlan_id)

        actual_vlan_sd = self.netutils._prepare_vlan_sd_access_mode(
            mock_vlan_sd, mock.sentinel.vlan_id)
        self.assertIsNone(actual_vlan_sd)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_create_default_setting_data')
    def test_prepare_vlan_sd_access_mode(self, mock_create_default_sd):
        mock_vlan_sd = mock_create_default_sd.return_value
        actual_vlan_sd = self.netutils._prepare_vlan_sd_access_mode(
            None, mock.sentinel.vlan_id)

        self.assertEqual(mock_vlan_sd, actual_vlan_sd)
        self.assertEqual(mock.sentinel.vlan_id, mock_vlan_sd.AccessVlanId)
        self.assertEqual(constants.VLAN_MODE_ACCESS,
                         mock_vlan_sd.OperationMode)
        mock_create_default_sd.assert_called_once_with(
            self.netutils._PORT_VLAN_SET_DATA)

    def test_prepare_vlan_sd_trunk_mode_already_set(self):
        mock_vlan_sd = mock.MagicMock(OperationMode=constants.VLAN_MODE_TRUNK,
                                      NativeVlanId=mock.sentinel.vlan_id,
                                      TrunkVlanIdArray=[100, 99])

        actual_vlan_sd = self.netutils._prepare_vlan_sd_trunk_mode(
            mock_vlan_sd, None, [99, 100])
        self.assertIsNone(actual_vlan_sd)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_create_default_setting_data')
    def test_prepare_vlan_sd_trunk_mode(self, mock_create_default_sd):
        mock_vlan_sd = mock_create_default_sd.return_value
        actual_vlan_sd = self.netutils._prepare_vlan_sd_trunk_mode(
            None, mock.sentinel.vlan_id, mock.sentinel.trunk_vlans)

        self.assertEqual(mock_vlan_sd, actual_vlan_sd)
        self.assertEqual(mock.sentinel.vlan_id, mock_vlan_sd.NativeVlanId)
        self.assertEqual(mock.sentinel.trunk_vlans,
                         mock_vlan_sd.TrunkVlanIdArray)
        self.assertEqual(constants.VLAN_MODE_TRUNK, mock_vlan_sd.OperationMode)
        mock_create_default_sd.assert_called_once_with(
            self.netutils._PORT_VLAN_SET_DATA)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_set_switch_port_security_settings')
    def test_set_vswitch_port_vsid(self, mock_set_port_sec_settings):
        self.netutils.set_vswitch_port_vsid(mock.sentinel.vsid,
                                            mock.sentinel.switch_port_name)
        mock_set_port_sec_settings.assert_called_once_with(
            mock.sentinel.switch_port_name, VirtualSubnetId=mock.sentinel.vsid)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_set_switch_port_security_settings')
    def test_set_vswitch_port_mac_spoofing(self, mock_set_port_sec_settings):
        self.netutils.set_vswitch_port_mac_spoofing(
            mock.sentinel.switch_port_name, mock.sentinel.state)
        mock_set_port_sec_settings.assert_called_once_with(
            mock.sentinel.switch_port_name,
            AllowMacSpoofing=mock.sentinel.state)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_security_setting_data_from_port_alloc')
    @mock.patch.object(networkutils.NetworkUtils,
                       '_create_default_setting_data')
    def _check_set_switch_port_security_settings(self, mock_create_default_sd,
                                                 mock_get_security_sd,
                                                 missing_sec=False):
        mock_port_alloc = self._mock_get_switch_port_alloc()

        mock_sec_settings = mock.MagicMock()
        mock_get_security_sd.return_value = (
            None if missing_sec else mock_sec_settings)
        mock_create_default_sd.return_value = mock_sec_settings

        if missing_sec:
            self.assertRaises(exceptions.HyperVException,
                              self.netutils._set_switch_port_security_settings,
                              mock.sentinel.switch_port_name,
                              VirtualSubnetId=mock.sentinel.vsid)
            mock_create_default_sd.assert_called_once_with(
                self.netutils._PORT_SECURITY_SET_DATA)
        else:
            self.netutils._set_switch_port_security_settings(
                mock.sentinel.switch_port_name,
                VirtualSubnetId=mock.sentinel.vsid)

        self.assertEqual(mock.sentinel.vsid,
                         mock_sec_settings.VirtualSubnetId)
        if missing_sec:
            mock_add_feature = self.netutils._jobutils.add_virt_feature
            mock_add_feature.assert_called_once_with(mock_sec_settings,
                                                     mock_port_alloc)
        else:
            mock_modify_feature = self.netutils._jobutils.modify_virt_feature
            mock_modify_feature.assert_called_once_with(mock_sec_settings)

    def test_set_switch_port_security_settings(self):
        self._check_set_switch_port_security_settings()

    def test_set_switch_port_security_settings_missing(self):
        self._check_set_switch_port_security_settings(missing_sec=True)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_security_setting_data_from_port_alloc')
    def test_set_switch_port_security_settings_already_set(self,
                                                           mock_get_sec_sd):
        self._mock_get_switch_port_alloc()
        mock_sec_sd = mock.MagicMock(VirtualSubnetId=mock.sentinel.vsid,
                                     AllowMacSpoofing=mock.sentinel.state)
        mock_get_sec_sd.return_value = mock_sec_sd

        self.netutils._set_switch_port_security_settings(
            mock.sentinel.switch_port_name,
            VirtualSubnetId=mock.sentinel.vsid,
            AllowMacSpoofing=mock.sentinel.state)

        self.assertFalse(self.netutils._jobutils.remove_virt_feature.called)
        self.assertFalse(self.netutils._jobutils.add_virt_feature.called)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_set_vswitch_port_vsid_already_set(self, mock_get_elem_assoc_cls):
        self._mock_get_switch_port_alloc()

        mock_sec_settings = mock.MagicMock(
            AllowMacSpoofing=mock.sentinel.state)
        mock_get_elem_assoc_cls.return_value = (mock_sec_settings, True)

        self.netutils.set_vswitch_port_mac_spoofing(
            mock.sentinel.switch_port_name, mock.sentinel.state)

        self.assertFalse(self.netutils._jobutils.add_virt_feature.called)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_hw_offload_sd_from_port_alloc')
    def test_set_vswitch_port_sriov_already_set(self, mock_get_hw_offload_sd):
        mock_port_alloc = self._mock_get_switch_port_alloc()
        mock_hw_offload_sd = mock_get_hw_offload_sd.return_value
        mock_hw_offload_sd.IOVOffloadWeight = self.netutils._OFFLOAD_ENABLED

        self.netutils.set_vswitch_port_sriov(mock.sentinel.port_name,
                                             True)

        mock_get_hw_offload_sd.assert_called_once_with(mock_port_alloc)
        self.netutils._jobutils.modify_virt_feature.assert_not_called()

    @ddt.data(True, False)
    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_hw_offload_sd_from_port_alloc')
    def test_set_vswitch_port_sriov(self, state, mock_get_hw_offload_sd):
        mock_port_alloc = self._mock_get_switch_port_alloc()
        mock_hw_offload_sd = mock_get_hw_offload_sd.return_value

        self.netutils.set_vswitch_port_sriov(mock.sentinel.port_name,
                                             state)

        mock_get_hw_offload_sd.assert_called_once_with(mock_port_alloc)
        self.netutils._jobutils.modify_virt_feature.assert_called_with(
            mock_hw_offload_sd)
        desired_state = (self.netutils._OFFLOAD_ENABLED if state else
                         self.netutils._OFFLOAD_DISABLED)
        self.assertEqual(desired_state, mock_hw_offload_sd.IOVOffloadWeight)

    @ddt.data({'iov_queues_requested': 0},
              {'offloaded_sa': 0})
    @ddt.unpack
    def test_set_vswitch_port_offload_invalid(self, iov_queues_requested=1,
                                              offloaded_sa=1024):
        self.assertRaises(exceptions.InvalidParameterValue,
                          self.netutils.set_vswitch_port_offload,
                          mock.sentinel.port_name,
                          iov_queues_requested=iov_queues_requested,
                          offloaded_sa=offloaded_sa)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_hw_offload_sd_from_port_alloc')
    def test_set_vswitch_port_offload_noop(self, mock_get_hw_offload_sd):
        self._mock_get_switch_port_alloc()
        self.netutils.set_vswitch_port_offload(mock.sentinel.port_name)
        self.netutils._jobutils.modify_virt_feature.assert_not_called()

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_hw_offload_sd_from_port_alloc')
    def test_set_vswitch_port_offload(self, mock_get_hw_offload_sd):
        mock_port_alloc = self._mock_get_switch_port_alloc()
        mock_hw_offload_sd = mock_get_hw_offload_sd.return_value
        iov_queues = 1
        offloaded_sa = 1

        self.netutils.set_vswitch_port_offload(
            mock.sentinel.port_name, True, iov_queues, True, offloaded_sa)

        mock_get_hw_offload_sd.assert_called_once_with(mock_port_alloc)
        self.netutils._jobutils.modify_virt_feature.assert_called_with(
            mock_hw_offload_sd)
        self.assertEqual(self.netutils._OFFLOAD_ENABLED,
                         mock_hw_offload_sd.IOVOffloadWeight)
        self.assertEqual(iov_queues,
                         mock_hw_offload_sd.IOVQueuePairsRequested)
        self.assertEqual(self.netutils._OFFLOAD_ENABLED,
                         mock_hw_offload_sd.VMQOffloadWeight)
        self.assertEqual(offloaded_sa,
                         mock_hw_offload_sd.IPSecOffloadLimit)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_setting_data_from_port_alloc')
    def test_get_profile_setting_data_from_port_alloc(self, mock_get_sd):
        result = self.netutils._get_profile_setting_data_from_port_alloc(
            mock.sentinel.port)

        self.assertEqual(mock_get_sd.return_value, result)
        mock_get_sd.assert_called_once_with(
            mock.sentinel.port, self.netutils._profile_sds,
            self.netutils._PORT_PROFILE_SET_DATA)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_setting_data_from_port_alloc')
    def test_get_vlan_setting_data_from_port_alloc(self, mock_get_sd):
        mock_port = mock.MagicMock()
        result = self.netutils._get_vlan_setting_data_from_port_alloc(
            mock_port)

        self.assertEqual(mock_get_sd.return_value, result)
        mock_get_sd.assert_called_once_with(mock_port, self.netutils._vsid_sds,
                                            self.netutils._PORT_VLAN_SET_DATA)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_setting_data_from_port_alloc')
    def test_get_security_setting_data_from_port_alloc(self, mock_get_sd):
        mock_port = mock.MagicMock()
        result = self.netutils._get_security_setting_data_from_port_alloc(
            mock_port)

        self.assertEqual(mock_get_sd.return_value, result)
        mock_get_sd.assert_called_once_with(
            mock_port, self.netutils._vsid_sds,
            self.netutils._PORT_SECURITY_SET_DATA)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_setting_data_from_port_alloc')
    def test_get_hw_offload_sd_from_port_alloc(self, mock_get_sd):
        mock_port = mock.MagicMock()
        result = self.netutils._get_hw_offload_sd_from_port_alloc(mock_port)

        self.assertEqual(mock_get_sd.return_value, result)
        mock_get_sd.assert_called_once_with(
            mock_port, self.netutils._hw_offload_sds,
            self.netutils._PORT_HW_OFFLOAD_SET_DATA)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_setting_data_from_port_alloc')
    def test_get_bandwidth_setting_data_from_port_alloc(self, mock_get_sd):
        mock_port = mock.MagicMock()
        result = self.netutils._get_bandwidth_setting_data_from_port_alloc(
            mock_port)

        self.assertEqual(mock_get_sd.return_value, result)
        mock_get_sd.assert_called_once_with(
            mock_port, self.netutils._bandwidth_sds,
            self.netutils._PORT_BANDWIDTH_SET_DATA)

    def test_get_setting_data_from_port_alloc_cached(self):
        mock_port = mock.MagicMock(InstanceID=mock.sentinel.InstanceID)
        cache = {mock_port.InstanceID: mock.sentinel.sd_object}

        result = self.netutils._get_setting_data_from_port_alloc(
            mock_port, cache, mock.sentinel.data_class)

        self.assertEqual(mock.sentinel.sd_object, result)

    @ddt.data(True, False)
    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_setting_data_from_port_alloc(self, enable_cache,
                                              mock_get_elem_assoc_cls):
        self.netutils._enable_cache = enable_cache
        sd_object = mock.MagicMock()
        mock_port = mock.MagicMock(InstanceID=mock.sentinel.InstanceID)
        mock_get_elem_assoc_cls.return_value = [sd_object]
        cache = {}
        result = self.netutils._get_setting_data_from_port_alloc(
            mock_port, cache, mock.sentinel.data_class)

        mock_get_elem_assoc_cls.assert_called_once_with(
            self.netutils._conn, mock.sentinel.data_class,
            element_instance_id=mock.sentinel.InstanceID)
        self.assertEqual(sd_object, result)

        expected_cache = ({mock.sentinel.InstanceID: sd_object}
                          if enable_cache else {})
        self.assertEqual(expected_cache, cache)

    def test_get_switch_port_allocation_cached(self):
        self.netutils._switch_ports[mock.sentinel.port_name] = (
            mock.sentinel.port)

        port, found = self.netutils._get_switch_port_allocation(
            mock.sentinel.port_name)

        self.assertEqual(mock.sentinel.port, port)
        self.assertTrue(found)

    @ddt.data(True, False)
    @mock.patch.object(networkutils.NetworkUtils, '_get_setting_data')
    def test_get_switch_port_allocation(self, enable_cache, mock_get_set_data):
        self.netutils._enable_cache = enable_cache
        self.netutils._switch_ports = {}
        mock_get_set_data.return_value = (mock.sentinel.port, True)

        port, found = self.netutils._get_switch_port_allocation(
            mock.sentinel.port_name)

        self.assertEqual(mock.sentinel.port, port)
        self.assertTrue(found)
        expected_cache = ({mock.sentinel.port_name: port}
                          if enable_cache else {})
        self.assertEqual(expected_cache, self.netutils._switch_ports)
        mock_get_set_data.assert_called_once_with(
            self.netutils._PORT_ALLOC_SET_DATA, mock.sentinel.port_name, False)

    @mock.patch.object(networkutils.NetworkUtils, '_get_setting_data')
    def test_get_switch_port_allocation_expected(self, mock_get_set_data):
        self.netutils._switch_ports = {}
        mock_get_set_data.return_value = (None, False)

        self.assertRaises(exceptions.HyperVPortNotFoundException,
                          self.netutils._get_switch_port_allocation,
                          mock.sentinel.port_name, expected=True)
        mock_get_set_data.assert_called_once_with(
            self.netutils._PORT_ALLOC_SET_DATA, mock.sentinel.port_name, False)

    def test_get_setting_data(self):
        self.netutils._get_first_item = mock.MagicMock(return_value=None)

        mock_data = mock.MagicMock()
        self.netutils._get_default_setting_data = mock.MagicMock(
            return_value=mock_data)

        ret_val = self.netutils._get_setting_data(self._FAKE_CLASS_NAME,
                                                  self._FAKE_ELEMENT_NAME,
                                                  True)

        self.assertEqual(ret_val, (mock_data, False))

    def test_create_default_setting_data(self):
        result = self.netutils._create_default_setting_data('FakeClass')

        fake_class = self.netutils._conn.FakeClass
        self.assertEqual(fake_class.new.return_value, result)
        fake_class.new.assert_called_once_with()

    def test_add_metrics_collection_acls(self):
        mock_port = self._mock_get_switch_port_alloc()
        mock_acl = mock.MagicMock()

        with mock.patch.multiple(
            self.netutils,
            _create_default_setting_data=mock.Mock(
                return_value=mock_acl)):

            self.netutils.add_metrics_collection_acls(self._FAKE_PORT_NAME)

            mock_add_feature = self.netutils._jobutils.add_virt_feature
            actual_calls = len(mock_add_feature.mock_calls)
            self.assertEqual(4, actual_calls)
            mock_add_feature.assert_called_with(mock_acl, mock_port)

    @mock.patch.object(networkutils.NetworkUtils, '_is_port_vm_started')
    def test_is_metrics_collection_allowed_true(self, mock_is_started):
        mock_acl = mock.MagicMock()
        mock_acl.Action = self.netutils._ACL_ACTION_METER
        self._test_is_metrics_collection_allowed(
            mock_vm_started=mock_is_started,
            acls=[mock_acl, mock_acl],
            expected_result=True)

    @mock.patch.object(networkutils.NetworkUtils, '_is_port_vm_started')
    def test_test_is_metrics_collection_allowed_false(self, mock_is_started):
        self._test_is_metrics_collection_allowed(
            mock_vm_started=mock_is_started,
            acls=[],
            expected_result=False)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def _test_is_metrics_collection_allowed(self, mock_get_elem_assoc_cls,
                                            mock_vm_started, acls,
                                            expected_result):
        mock_port = self._mock_get_switch_port_alloc()
        mock_acl = mock.MagicMock()
        mock_acl.Action = self.netutils._ACL_ACTION_METER

        mock_get_elem_assoc_cls.return_value = acls
        mock_vm_started.return_value = True

        result = self.netutils.is_metrics_collection_allowed(
            self._FAKE_PORT_NAME)
        self.assertEqual(expected_result, result)
        mock_get_elem_assoc_cls.assert_called_once_with(
            self.netutils._conn, self.netutils._PORT_ALLOC_ACL_SET_DATA,
            element_instance_id=mock_port.InstanceID)

    def test_is_port_vm_started_true(self):
        self._test_is_port_vm_started(self.netutils._HYPERV_VM_STATE_ENABLED,
                                      True)

    def test_is_port_vm_started_false(self):
        self._test_is_port_vm_started(self._FAKE_HYPERV_VM_STATE, False)

    def _test_is_port_vm_started(self, vm_state, expected_result):
        mock_svc = self.netutils._conn.Msvm_VirtualSystemManagementService()[0]
        mock_port = mock.MagicMock()
        mock_vmsettings = mock.MagicMock()
        mock_summary = mock.MagicMock()
        mock_summary.EnabledState = vm_state
        mock_vmsettings.path_.return_value = self._FAKE_RES_PATH

        self.netutils._conn.Msvm_VirtualSystemSettingData.return_value = [
            mock_vmsettings]
        mock_svc.GetSummaryInformation.return_value = (self._FAKE_RET_VAL,
                                                       [mock_summary])

        result = self.netutils._is_port_vm_started(mock_port)
        self.assertEqual(expected_result, result)
        mock_svc.GetSummaryInformation.assert_called_once_with(
            [self.netutils._VM_SUMMARY_ENABLED_STATE],
            [self._FAKE_RES_PATH])

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(networkutils.NetworkUtils, '_bind_security_rules')
    def test_create_security_rules(self, mock_bind, mock_get_elem_assoc_cls):
        (m_port, m_acl) = self._setup_security_rule_test(
            mock_get_elem_assoc_cls)
        fake_rule = mock.MagicMock()

        self.netutils.create_security_rules(self._FAKE_PORT_NAME, fake_rule)
        mock_bind.assert_called_once_with(m_port, fake_rule)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(networkutils.NetworkUtils, '_create_security_acl')
    @mock.patch.object(networkutils.NetworkUtils, '_get_new_weights')
    @mock.patch.object(networkutils.NetworkUtils, '_filter_security_acls')
    def test_bind_security_rules(self, mock_filtered_acls, mock_get_weights,
                                 mock_create_acl, mock_get_elem_assoc_cls):
        m_port = mock.MagicMock()
        m_acl = mock.MagicMock()
        mock_get_elem_assoc_cls.return_value = [m_acl]
        mock_filtered_acls.return_value = []
        mock_get_weights.return_value = [mock.sentinel.FAKE_WEIGHT]
        mock_create_acl.return_value = m_acl
        fake_rule = mock.MagicMock()

        self.netutils._bind_security_rules(m_port, [fake_rule])

        mock_create_acl.assert_called_once_with(fake_rule,
                                                mock.sentinel.FAKE_WEIGHT)
        mock_add_features = self.netutils._jobutils.add_multiple_virt_features
        mock_add_features.assert_called_once_with([m_acl], m_port)
        mock_get_elem_assoc_cls.assert_called_once_with(
            self.netutils._conn, self.netutils._PORT_EXT_ACL_SET_DATA,
            element_instance_id=m_port.InstanceID)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(networkutils.NetworkUtils, '_get_new_weights')
    @mock.patch.object(networkutils.NetworkUtils, '_filter_security_acls')
    def test_bind_security_rules_existent(self, mock_filtered_acls,
                                          mock_get_weights,
                                          mock_get_elem_assoc_cls):
        m_port = mock.MagicMock()
        m_acl = mock.MagicMock()
        mock_get_elem_assoc_cls.return_value = [m_acl]
        mock_filtered_acls.return_value = [m_acl]
        fake_rule = mock.MagicMock()

        self.netutils._bind_security_rules(m_port, [fake_rule])
        mock_filtered_acls.assert_called_once_with(fake_rule, [m_acl])
        mock_get_weights.assert_called_once_with([fake_rule], [m_acl])
        mock_get_elem_assoc_cls.assert_called_once_with(
            self.netutils._conn, self.netutils._PORT_EXT_ACL_SET_DATA,
            element_instance_id=m_port.InstanceID)

    def test_get_port_security_acls_cached(self):
        mock_port = mock.MagicMock(ElementName=mock.sentinel.port_name)
        self.netutils._sg_acl_sds = {
            mock.sentinel.port_name: [mock.sentinel.fake_acl]}

        acls = self.netutils._get_port_security_acls(mock_port)

        self.assertEqual([mock.sentinel.fake_acl], acls)

    @ddt.data(True, False)
    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_get_port_security_acls(self, enable_cache,
                                    mock_get_elem_assoc_cls):
        self.netutils._enable_cache = enable_cache
        self.netutils._sg_acl_sds = {}
        mock_port = mock.MagicMock()
        mock_get_elem_assoc_cls.return_value = [mock.sentinel.fake_acl]

        acls = self.netutils._get_port_security_acls(mock_port)

        self.assertEqual([mock.sentinel.fake_acl], acls)
        expected_cache = ({mock_port.ElementName: [mock.sentinel.fake_acl]}
                          if enable_cache else {})
        self.assertEqual(expected_cache,
                         self.netutils._sg_acl_sds)
        mock_get_elem_assoc_cls.assert_called_once_with(
            self.netutils._conn, self.netutils._PORT_EXT_ACL_SET_DATA,
            element_instance_id=mock_port.InstanceID)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(networkutils.NetworkUtils, '_filter_security_acls')
    def test_remove_security_rules(self, mock_filter, mock_get_elem_assoc_cls):
        mock_acl = self._setup_security_rule_test(mock_get_elem_assoc_cls)[1]
        fake_rule = mock.MagicMock()
        mock_filter.return_value = [mock_acl]

        self.netutils.remove_security_rules(self._FAKE_PORT_NAME, [fake_rule])

        mock_remove_features = (
            self.netutils._jobutils.remove_multiple_virt_features)
        mock_remove_features.assert_called_once_with([mock_acl])

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    def test_remove_all_security_rules(self, mock_get_elem_assoc_cls):
        mock_acl = self._setup_security_rule_test(mock_get_elem_assoc_cls)[1]
        self.netutils.remove_all_security_rules(self._FAKE_PORT_NAME)
        mock_remove_features = (
            self.netutils._jobutils.remove_multiple_virt_features)
        mock_remove_features.assert_called_once_with([mock_acl])

    @mock.patch.object(networkutils.NetworkUtils,
                       '_create_default_setting_data')
    def test_create_security_acl(self, mock_get_set_data):
        mock_acl = mock_get_set_data.return_value
        fake_rule = mock.MagicMock()
        fake_rule.to_dict.return_value = {"Action": self._FAKE_ACL_ACT}

        self.netutils._create_security_acl(fake_rule, self._FAKE_WEIGHT)
        mock_acl.set.assert_called_once_with(Action=self._FAKE_ACL_ACT)

    def _setup_security_rule_test(self, mock_get_elem_assoc_cls):
        mock_port = self._mock_get_switch_port_alloc()
        mock_acl = mock.MagicMock()
        mock_get_elem_assoc_cls.return_value = [mock_acl]

        self.netutils._filter_security_acls = mock.MagicMock(
            return_value=[mock_acl])

        return (mock_port, mock_acl)

    def test_filter_acls(self):
        mock_acl = mock.MagicMock()
        mock_acl.Action = self._FAKE_ACL_ACT
        mock_acl.Applicability = self.netutils._ACL_APPLICABILITY_LOCAL
        mock_acl.Direction = self._FAKE_ACL_DIR
        mock_acl.AclType = self._FAKE_ACL_TYPE
        mock_acl.RemoteAddress = self._FAKE_REMOTE_ADDR

        acls = [mock_acl, mock_acl]
        good_acls = self.netutils._filter_acls(
            acls, self._FAKE_ACL_ACT, self._FAKE_ACL_DIR,
            self._FAKE_ACL_TYPE, self._FAKE_REMOTE_ADDR)
        bad_acls = self.netutils._filter_acls(
            acls, self._FAKE_ACL_ACT, self._FAKE_ACL_DIR, self._FAKE_ACL_TYPE)

        self.assertEqual(acls, good_acls)
        self.assertEqual([], bad_acls)

    def test_get_new_weights_allow(self):
        actual = self.netutils._get_new_weights([mock.ANY, mock.ANY], mock.ANY)
        self.assertEqual([0, 0], actual)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_bandwidth_setting_data_from_port_alloc')
    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_default_setting_data')
    def test_set_port_qos_rule_hyperv_exc(self, mock_get_default_sd,
                                          mock_get_bandwidth_sd):
        mock_port_alloc = self._mock_get_switch_port_alloc()

        self.netutils._bandwidth_sds = {
            mock_port_alloc.InstanceID: mock.sentinel.InstanceID}
        mock_remove_feature = self.netutils._jobutils.remove_virt_feature
        mock_add_feature = self.netutils._jobutils.add_virt_feature
        mock_add_feature.side_effect = exceptions.HyperVException

        qos_rule = dict(min_kbps=20000, max_kbps=30000,
                        max_burst_kbps=40000, max_burst_size_kb=50000)

        self.assertRaises(exceptions.HyperVException,
                          self.netutils.set_port_qos_rule,
                          mock.sentinel.port_id, qos_rule)

        mock_get_bandwidth_sd.assert_called_once_with(mock_port_alloc)
        mock_get_default_sd.assert_called_once_with(
            self.netutils._PORT_BANDWIDTH_SET_DATA)
        mock_remove_feature.assert_called_once_with(
            mock_get_bandwidth_sd.return_value)
        mock_add_feature.assert_called_once_with(
            mock_get_default_sd.return_value, mock_port_alloc)

        bw = mock_get_default_sd.return_value
        self.assertEqual(qos_rule['min_kbps'] * units.Ki,
                         bw.Reservation)
        self.assertEqual(qos_rule['max_kbps'] * units.Ki,
                         bw.Limit)
        self.assertEqual(qos_rule['max_burst_kbps'] * units.Ki,
                         bw.BurstLimit)
        self.assertEqual(qos_rule['max_burst_size_kb'] * units.Ki,
                         bw.BurstSize)
        self.assertNotIn(mock_port_alloc.InstanceID,
                         self.netutils._bandwidth_sds)

    @ddt.data({'min_kbps': 100},
              {'min_kbps': 10 * units.Ki, 'max_kbps': 100},
              {'max_kbps': 10 * units.Ki, 'max_burst_kbps': 100})
    def test_set_port_qos_rule_invalid_params_exception(self, qos_rule):
        self.assertRaises(exceptions.InvalidParameterValue,
                          self.netutils.set_port_qos_rule,
                          mock.sentinel.port_id,
                          qos_rule)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_bandwidth_setting_data_from_port_alloc')
    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_default_setting_data')
    def test_set_port_qos_rule_invalid_qos_rule_exc(self, mock_get_default_sd,
                                                    mock_get_bandwidth_sd):
        self._mock_get_switch_port_alloc()

        mock_add_feature = self.netutils._jobutils.add_virt_feature
        mock_add_feature.side_effect = exceptions.InvalidParameterValue(
            '0x80070057')

        qos_rule = dict(min_kbps=20000, max_kbps=30000,
                        max_burst_kbps=40000, max_burst_size_kb=50000)

        self.assertRaises(exceptions.InvalidParameterValue,
                          self.netutils.set_port_qos_rule,
                          mock.sentinel.port_id, qos_rule)

    def test_set_empty_port_qos_rule(self):
        self._mock_get_switch_port_alloc()

        self.netutils.set_port_qos_rule(mock.sentinel.port_id, {})
        self.assertFalse(self.netutils._get_switch_port_allocation.called)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_get_bandwidth_setting_data_from_port_alloc')
    def test_remove_port_qos_rule(self, mock_get_bandwidth_sd):
        mock_port_alloc = self._mock_get_switch_port_alloc()
        mock_bandwidth_settings = mock_get_bandwidth_sd.return_value

        self.netutils.remove_port_qos_rule(mock.sentinel.port_id)

        mock_get_bandwidth_sd.assert_called_once_with(mock_port_alloc)
        mock_remove_feature = self.netutils._jobutils.remove_virt_feature
        mock_remove_feature.assert_called_once_with(
            mock_bandwidth_settings)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_create_default_setting_data')
    def test_prepare_profile_sd(self, mock_create_default_sd):
        mock_profile_sd = mock_create_default_sd.return_value

        actual_profile_sd = self.netutils._prepare_profile_sd(
            profile_id=mock.sentinel.profile_id,
            profile_data=mock.sentinel.profile_data,
            profile_name=mock.sentinel.profile_name,
            net_cfg_instance_id=mock.sentinel.net_cfg_instance_id,
            cdn_label_id=mock.sentinel.cdn_label_id,
            cdn_label_string=mock.sentinel.cdn_label_string,
            vendor_id=mock.sentinel.vendor_id,
            vendor_name=mock.sentinel.vendor_name)

        self.assertEqual(mock_profile_sd, actual_profile_sd)
        self.assertEqual(mock.sentinel.profile_id,
                         mock_profile_sd.ProfileId)
        self.assertEqual(mock.sentinel.profile_data,
                         mock_profile_sd.ProfileData)
        self.assertEqual(mock.sentinel.profile_name,
                         mock_profile_sd.ProfileName)
        self.assertEqual(mock.sentinel.net_cfg_instance_id,
                         mock_profile_sd.NetCfgInstanceId)
        self.assertEqual(mock.sentinel.cdn_label_id,
                         mock_profile_sd.CdnLabelId)
        self.assertEqual(mock.sentinel.cdn_label_string,
                         mock_profile_sd.CdnLabelString)
        self.assertEqual(mock.sentinel.vendor_id,
                         mock_profile_sd.VendorId)
        self.assertEqual(mock.sentinel.vendor_name,
                         mock_profile_sd.VendorName)
        mock_create_default_sd.assert_called_once_with(
            self.netutils._PORT_PROFILE_SET_DATA)

    @mock.patch.object(networkutils.NetworkUtils,
                       '_create_default_setting_data')
    def test_prepare_profile_sd_failed(self, mock_create_default_sd):
        self.assertRaises(TypeError, self.netutils._prepare_profile_sd,
                          invalid_argument=mock.sentinel.invalid_argument)


class TestNetworkUtilsR2(test_base.OsWinBaseTestCase):

    def setUp(self):
        super(TestNetworkUtilsR2, self).setUp()
        self.netutils = networkutils.NetworkUtilsR2()
        self.netutils._conn_attr = mock.MagicMock()

    @mock.patch.object(networkutils.NetworkUtilsR2,
                       '_create_default_setting_data')
    def test_create_security_acl(self, mock_create_default_setting_data):
        sg_rule = mock.MagicMock()
        sg_rule.to_dict.return_value = {}

        acl = self.netutils._create_security_acl(sg_rule, mock.sentinel.weight)

        self.assertEqual(mock.sentinel.weight, acl.Weight)

    def test_get_new_weights_no_acls_deny(self):
        mock_rule = mock.MagicMock(Action=self.netutils._ACL_ACTION_DENY)
        actual = self.netutils._get_new_weights([mock_rule], [])
        self.assertEqual([1], actual)

    def test_get_new_weights_no_acls_allow(self):
        mock_rule = mock.MagicMock(Action=self.netutils._ACL_ACTION_ALLOW)
        actual = self.netutils._get_new_weights([mock_rule, mock_rule], [])

        expected = [self.netutils._MAX_WEIGHT - 1,
                    self.netutils._MAX_WEIGHT - 2]
        self.assertEqual(expected, actual)

    def test_get_new_weights_deny(self):
        mock_rule = mock.MagicMock(Action=self.netutils._ACL_ACTION_DENY)
        mockacl1 = mock.MagicMock(Action=self.netutils._ACL_ACTION_DENY,
                                  Weight=1)
        mockacl2 = mock.MagicMock(Action=self.netutils._ACL_ACTION_DENY,
                                  Weight=3)

        actual = self.netutils._get_new_weights([mock_rule, mock_rule],
                                                [mockacl1, mockacl2])

        self.assertEqual([2, 4], actual)

    def test_get_new_weights_allow(self):
        mock_rule = mock.MagicMock(Action=self.netutils._ACL_ACTION_ALLOW)
        mockacl = mock.MagicMock(Action=self.netutils._ACL_ACTION_ALLOW,
                                 Weight=self.netutils._MAX_WEIGHT - 3)

        actual = self.netutils._get_new_weights([mock_rule, mock_rule],
                                                [mockacl])

        expected = [self.netutils._MAX_WEIGHT - 4,
                    self.netutils._MAX_WEIGHT - 5]
        self.assertEqual(expected, actual)

    def test_get_new_weights_search_available(self):
        mock_rule = mock.MagicMock(Action=self.netutils._ACL_ACTION_ALLOW)
        mockacl1 = mock.MagicMock(Action=self.netutils._ACL_ACTION_ALLOW,
                                  Weight=self.netutils._REJECT_ACLS_COUNT + 1)
        mockacl2 = mock.MagicMock(Action=self.netutils._ACL_ACTION_ALLOW,
                                  Weight=self.netutils._MAX_WEIGHT - 1)

        actual = self.netutils._get_new_weights([mock_rule],
                                                [mockacl1, mockacl2])

        self.assertEqual([self.netutils._MAX_WEIGHT - 2], actual)
