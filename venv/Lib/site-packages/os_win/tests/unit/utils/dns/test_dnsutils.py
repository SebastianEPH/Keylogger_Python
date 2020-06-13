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

import mock

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils.dns import dnsutils


class DNSUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V DNSUtils class."""

    def setUp(self):
        super(DNSUtilsTestCase, self).setUp()
        self._dnsutils = dnsutils.DNSUtils()
        self._dnsutils._dns_manager_attr = mock.MagicMock()

    @mock.patch.object(dnsutils.DNSUtils, '_get_wmi_obj')
    def test_dns_manager(self, mock_get_wmi_obj):
        self._dnsutils._dns_manager_attr = None

        self.assertEqual(mock_get_wmi_obj.return_value,
                         self._dnsutils._dns_manager)

        mock_get_wmi_obj.assert_called_once_with(
            self._dnsutils._DNS_NAMESPACE % self._dnsutils._host)

    @mock.patch.object(dnsutils.DNSUtils, '_get_wmi_obj')
    def test_dns_manager_fail(self, mock_get_wmi_obj):
        self._dnsutils._dns_manager_attr = None
        expected_exception = exceptions.DNSException
        mock_get_wmi_obj.side_effect = expected_exception

        self.assertRaises(expected_exception,
                          lambda: self._dnsutils._dns_manager)

        mock_get_wmi_obj.assert_called_once_with(
            self._dnsutils._DNS_NAMESPACE % self._dnsutils._host)

    def test_get_zone(self):
        zone_manager = self._dnsutils._dns_manager.MicrosoftDNS_Zone
        zone_manager.return_value = [mock.sentinel.zone]

        zone_found = self._dnsutils._get_zone(mock.sentinel.zone_name)

        zone_manager.assert_called_once_with(Name=mock.sentinel.zone_name)
        self.assertEqual(mock.sentinel.zone, zone_found)

    def test_get_zone_ignore_missing(self):
        zone_manager = self._dnsutils._dns_manager.MicrosoftDNS_Zone
        zone_manager.return_value = []

        zone_found = self._dnsutils._get_zone(mock.sentinel.zone_name)

        zone_manager.assert_called_once_with(Name=mock.sentinel.zone_name)
        self.assertIsNone(zone_found)

    def test_get_zone_missing(self):
        zone_manager = self._dnsutils._dns_manager.MicrosoftDNS_Zone
        zone_manager.return_value = []

        self.assertRaises(exceptions.DNSZoneNotFound,
                          self._dnsutils._get_zone,
                          mock.sentinel.zone_name,
                          ignore_missing=False)
        zone_manager.assert_called_once_with(Name=mock.sentinel.zone_name)

    def test_zone_list(self):
        zone_manager = self._dnsutils._dns_manager.MicrosoftDNS_Zone
        zone_manager.return_value = [mock.Mock(Name=mock.sentinel.fake_name1),
                                     mock.Mock(Name=mock.sentinel.fake_name2)]

        zone_list = self._dnsutils.zone_list()

        expected_zone_list = [mock.sentinel.fake_name1,
                              mock.sentinel.fake_name2]
        self.assertEqual(expected_zone_list, zone_list)
        zone_manager.assert_called_once_with()

    @mock.patch.object(dnsutils.DNSUtils, '_get_zone')
    def test_zone_exists(self, mock_get_zone):
        zone_already_exists = self._dnsutils.zone_exists(
            mock.sentinel.zone_name)
        mock_get_zone.assert_called_once_with(mock.sentinel.zone_name)

        self.assertTrue(zone_already_exists)

    @mock.patch.object(dnsutils.DNSUtils, '_get_zone')
    def test_zone_exists_false(self, mock_get_zone):
        mock_get_zone.return_value = None

        zone_already_exists = self._dnsutils.zone_exists(
            mock.sentinel.zone_name)
        mock_get_zone.assert_called_once_with(mock.sentinel.zone_name)

        self.assertFalse(zone_already_exists)

    @mock.patch.object(dnsutils.DNSUtils, '_get_zone')
    def test_get_zone_properties(self, mock_get_zone):
        mock_get_zone.return_value = mock.Mock(
            ZoneType=mock.sentinel.zone_type,
            DsIntegrated=mock.sentinel.ds_integrated,
            DataFile=mock.sentinel.data_file_name,
            MasterServers=[mock.sentinel.ip_addrs])

        zone_properties = self._dnsutils.get_zone_properties(
            mock.sentinel.zone_name)
        expected_zone_props = {
            'zone_type': mock.sentinel.zone_type,
            'ds_integrated': mock.sentinel.ds_integrated,
            'master_servers': [mock.sentinel.ip_addrs],
            'data_file_name': mock.sentinel.data_file_name
        }
        self.assertEqual(expected_zone_props, zone_properties)
        mock_get_zone.assert_called_once_with(mock.sentinel.zone_name,
                                              ignore_missing=False)

    @mock.patch.object(dnsutils.DNSUtils, 'zone_exists')
    def test_zone_create(self, mock_zone_exists):
        mock_zone_exists.return_value = False
        zone_manager = self._dnsutils._dns_manager.MicrosoftDNS_Zone
        zone_manager.CreateZone.return_value = (mock.sentinel.zone_path,)

        zone_path = self._dnsutils.zone_create(
            zone_name=mock.sentinel.zone_name,
            zone_type=mock.sentinel.zone_type,
            ds_integrated=mock.sentinel.ds_integrated,
            data_file_name=mock.sentinel.data_file_name,
            ip_addrs=mock.sentinel.ip_addrs,
            admin_email_name=mock.sentinel.admin_email_name)

        zone_manager.CreateZone.assert_called_once_with(
            ZoneName=mock.sentinel.zone_name,
            ZoneType=mock.sentinel.zone_type,
            DsIntegrated=mock.sentinel.ds_integrated,
            DataFileName=mock.sentinel.data_file_name,
            IpAddr=mock.sentinel.ip_addrs,
            AdminEmailname=mock.sentinel.admin_email_name)
        mock_zone_exists.assert_called_once_with(mock.sentinel.zone_name)
        self.assertEqual(mock.sentinel.zone_path, zone_path)

    @mock.patch.object(dnsutils.DNSUtils, 'zone_exists')
    def test_zone_create_existing_zone(self, mock_zone_exists):
        self.assertRaises(exceptions.DNSZoneAlreadyExists,
                          self._dnsutils.zone_create,
                          zone_name=mock.sentinel.zone_name,
                          zone_type=mock.sentinel.zone_type,
                          ds_integrated=mock.sentinel.ds_integrated)
        mock_zone_exists.assert_called_once_with(mock.sentinel.zone_name)

    @mock.patch.object(dnsutils.DNSUtils, '_get_zone')
    def test_zone_delete(self, mock_get_zone):
        self._dnsutils.zone_delete(mock.sentinel.zone_name)

        mock_get_zone.assert_called_once_with(mock.sentinel.zone_name)
        mock_get_zone.return_value.Delete_.assert_called_once_with()

    @mock.patch.object(dnsutils.DNSUtils, '_get_zone')
    def test_zone_modify(self, mock_get_zone):
        mock_zone = mock.MagicMock(
            AllowUpdate=mock.sentinel.allowupdate,
            DisableWINSRecordReplication=mock.sentinel.disablewins,
            Notify=mock.sentinel.notify,
            SecureSecondaries=mock.sentinel.securesecondaries)
        mock_get_zone.return_value = mock_zone

        self._dnsutils.zone_modify(
            mock.sentinel.zone_name,
            allow_update=None,
            disable_wins=mock.sentinel.disable_wins,
            notify=None,
            reverse=mock.sentinel.reverse,
            secure_secondaries=None)

        self.assertEqual(mock.sentinel.allowupdate, mock_zone.AllowUpdate)
        self.assertEqual(mock.sentinel.disable_wins,
                         mock_zone.DisableWINSRecordReplication)
        self.assertEqual(mock.sentinel.notify, mock_zone.Notify)
        self.assertEqual(mock.sentinel.reverse,
                         mock_zone.Reverse)
        self.assertEqual(mock.sentinel.securesecondaries,
                         mock_zone.SecureSecondaries)
        mock_zone.put.assert_called_once_with()

    @mock.patch.object(dnsutils.DNSUtils, '_get_zone')
    def test_zone_update_force_refresh(self, mock_get_zone):
        mock_zone = mock.MagicMock(DsIntegrated=False,
                                   ZoneType=constants.DNS_ZONE_TYPE_SECONDARY)
        mock_get_zone.return_value = mock_zone

        self._dnsutils.zone_update(mock.sentinel.zone_name)

        mock_get_zone.assert_called_once_with(
            mock.sentinel.zone_name,
            ignore_missing=False)
        mock_zone.ForceRefresh.assert_called_once_with()

    @mock.patch.object(dnsutils.DNSUtils, '_get_zone')
    def test_zone_update_from_ds(self, mock_get_zone):
        mock_zone = mock.MagicMock(DsIntegrated=True,
                                   ZoneType=constants.DNS_ZONE_TYPE_PRIMARY)
        mock_get_zone.return_value = mock_zone

        self._dnsutils.zone_update(mock.sentinel.zone_name)

        mock_get_zone.assert_called_once_with(
            mock.sentinel.zone_name,
            ignore_missing=False)
        mock_zone.UpdateFromDS.assert_called_once_with()

    @mock.patch.object(dnsutils.DNSUtils, '_get_zone')
    def test_zone_update_reload_zone(self, mock_get_zone):
        mock_zone = mock.MagicMock(DsIntegrated=False,
                                   ZoneType=constants.DNS_ZONE_TYPE_PRIMARY)
        mock_get_zone.return_value = mock_zone

        self._dnsutils.zone_update(mock.sentinel.zone_name)

        mock_get_zone.assert_called_once_with(
            mock.sentinel.zone_name,
            ignore_missing=False)
        mock_zone.ReloadZone.assert_called_once_with()

    @mock.patch.object(dnsutils.DNSUtils, 'zone_exists')
    def test_get_zone_serial(self, mock_zone_exists):
        mock_zone_exists.return_value = True
        fake_serial_number = 1
        msdns_soatype = self._dnsutils._dns_manager.MicrosoftDNS_SOAType
        msdns_soatype.return_value = [
            mock.Mock(SerialNumber=fake_serial_number)]

        serial_number = self._dnsutils.get_zone_serial(mock.sentinel.zone_name)

        expected_serial_number = fake_serial_number
        self.assertEqual(expected_serial_number, serial_number)
        msdns_soatype.assert_called_once_with(
            ContainerName=mock.sentinel.zone_name)
        mock_zone_exists.assert_called_once_with(mock.sentinel.zone_name)

    @mock.patch.object(dnsutils.DNSUtils, 'zone_exists')
    def test_get_zone_serial_zone_not_found(self, mock_zone_exists):
        mock_zone_exists.return_value = False

        serial_number = self._dnsutils.get_zone_serial(mock.sentinel.zone_name)

        self.assertIsNone(serial_number)
        mock_zone_exists.assert_called_once_with(mock.sentinel.zone_name)

    @mock.patch.object(dnsutils.DNSUtils, 'zone_exists')
    def test_get_zone_serial_zone_soatype_not_found(self, mock_zone_exists):
        mock_zone_exists.return_value = True
        self._dnsutils._dns_manager.MicrosoftDNS_SOAType.return_value = []

        serial_number = self._dnsutils.get_zone_serial(mock.sentinel.zone_name)

        self.assertIsNone(serial_number)
        mock_zone_exists.assert_called_once_with(mock.sentinel.zone_name)
