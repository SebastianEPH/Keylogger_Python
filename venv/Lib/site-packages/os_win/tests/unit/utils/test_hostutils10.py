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

import re

import mock

from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import hostutils10


class HostUtils10TestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V HostUtils10 class."""

    def setUp(self):
        super(HostUtils10TestCase, self).setUp()
        self._hostutils = hostutils10.HostUtils10()
        self._hostutils._conn_hgs_attr = mock.MagicMock()
        self._hostutils._conn_attr = mock.MagicMock()
        self._hostutils._conn_cimv2 = mock.MagicMock()

    @mock.patch.object(hostutils10.HostUtils10, '_get_wmi_conn')
    def test_conn_hgs(self, mock_get_wmi_conn):
        self._hostutils._conn_hgs_attr = None
        self.assertEqual(mock_get_wmi_conn.return_value,
                         self._hostutils._conn_hgs)

        mock_get_wmi_conn.assert_called_once_with(
            self._hostutils._HGS_NAMESPACE % self._hostutils._host)

    @mock.patch.object(hostutils10.HostUtils10, '_get_wmi_conn')
    def test_conn_hgs_no_namespace(self, mock_get_wmi_conn):
        self._hostutils._conn_hgs_attr = None

        mock_get_wmi_conn.side_effect = [exceptions.OSWinException]
        self.assertRaises(exceptions.OSWinException,
                          lambda: self._hostutils._conn_hgs)
        mock_get_wmi_conn.assert_called_once_with(
            self._hostutils._HGS_NAMESPACE % self._hostutils._host)

    def _test_is_host_guarded(self, return_code=0, is_host_guarded=True):
        hgs_config = self._hostutils._conn_hgs.MSFT_HgsClientConfiguration
        hgs_config.Get.return_value = (return_code,
                                       mock.MagicMock
                                       (IsHostGuarded=is_host_guarded))
        expected_result = is_host_guarded and not return_code

        result = self._hostutils.is_host_guarded()
        self.assertEqual(expected_result, result)

    def test_is_guarded_host_config_error(self):
        self._test_is_host_guarded(return_code=mock.sentinel.return_code)

    def test_is_guarded_host(self):
        self._test_is_host_guarded()

    def test_is_not_guarded_host(self):
        self._test_is_host_guarded(is_host_guarded=False)

    def test_supports_nested_virtualization(self):
        self.assertTrue(self._hostutils.supports_nested_virtualization())

    @mock.patch.object(hostutils10.HostUtils10, '_get_pci_device_address')
    def test_get_pci_passthrough_devices(self, mock_get_pci_device_address):
        mock_pci_dev = mock.MagicMock(
            DeviceInstancePath='PCIP\\VEN_15B3&DEV_1007&SUBSYS_001815B3')
        self._hostutils._conn.Msvm_PciExpress.return_value = [mock_pci_dev] * 3
        mock_get_pci_device_address.side_effect = [
            None, mock.sentinel.address, mock.sentinel.address]

        pci_devices = self._hostutils.get_pci_passthrough_devices()

        expected_pci_dev = {
            'address': mock.sentinel.address,
            'vendor_id': '15B3',
            'product_id': '1007',
            'dev_id': mock_pci_dev.DeviceID}
        self.assertEqual([expected_pci_dev], pci_devices)
        self._hostutils._conn.Msvm_PciExpress.assert_called_once_with()
        mock_get_pci_device_address.has_calls(
            [mock.call(mock_pci_dev.DeviceInstancePath)] * 3)

    def _check_get_pci_device_address_None(self, return_code=0):
        pnp_device = mock.MagicMock()
        pnp_device.GetDeviceProperties.return_value = (
            return_code, [mock.MagicMock()])
        self._hostutils._conn_cimv2.Win32_PnPEntity.return_value = [pnp_device]

        pci_dev_address = self._hostutils._get_pci_device_address(
            mock.sentinel.pci_device_path)
        self.assertIsNone(pci_dev_address)

    def test_get_pci_device_address_error(self):
        self._check_get_pci_device_address_None(return_code=1)

    def test_get_pci_device_address_exception(self):
        self._check_get_pci_device_address_None()

    def test_get_pci_device_address(self):
        pnp_device = mock.MagicMock()
        pnp_device_properties = [
            mock.MagicMock(KeyName='DEVPKEY_Device_LocationInfo',
                           Data="bus 2, domain 4, function 0"),
            mock.MagicMock(KeyName='DEVPKEY_Device_Address',
                           Data=0)]
        pnp_device.GetDeviceProperties.return_value = (
            0, pnp_device_properties)
        self._hostutils._conn_cimv2.Win32_PnPEntity.return_value = [pnp_device]

        result = self._hostutils._get_pci_device_address(
            mock.sentinel.device_instance_path)

        pnp_props = {prop.KeyName: prop.Data for prop in pnp_device_properties}
        location_info = pnp_props['DEVPKEY_Device_LocationInfo']
        slot = pnp_props['DEVPKEY_Device_Address']
        [bus, domain, function] = re.findall(r'\b\d+\b', location_info)
        expected_result = "%04x:%02x:%02x.%1x" % (
            int(domain), int(bus), int(slot), int(function))

        self.assertEqual(expected_result, result)
        self._hostutils._conn_cimv2.Win32_PnPEntity.assert_called_once_with(
            DeviceID=mock.sentinel.device_instance_path)
