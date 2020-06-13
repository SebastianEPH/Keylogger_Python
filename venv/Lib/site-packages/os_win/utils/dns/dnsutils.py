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

from oslo_log import log as logging

from os_win._i18n import _
from os_win import constants
from os_win import exceptions
from os_win.utils import baseutils

LOG = logging.getLogger(__name__)


class DNSUtils(baseutils.BaseUtils):

    _DNS_NAMESPACE = '//%s/root/MicrosoftDNS'

    def __init__(self, host='.'):
        self._dns_manager_attr = None
        self._host = host

    @property
    def _dns_manager(self):
        if not self._dns_manager_attr:
            try:
                namespace = self._DNS_NAMESPACE % self._host
                self._dns_manager_attr = self._get_wmi_obj(namespace)
            except Exception:
                raise exceptions.DNSException(
                    _("Namespace %(namespace)s not found. Make sure "
                      "DNS Server feature is installed.") %
                    {'namespace': namespace})

        return self._dns_manager_attr

    def _get_zone(self, zone_name, ignore_missing=True):
        zones = self._dns_manager.MicrosoftDNS_Zone(Name=zone_name)
        if zones:
            return zones[0]
        if not ignore_missing:
            raise exceptions.DNSZoneNotFound(zone_name=zone_name)

    def zone_list(self):
        """Returns the current list of DNS Zones.

        """

        zones = self._dns_manager.MicrosoftDNS_Zone()
        return [x.Name for x in zones]

    def zone_exists(self, zone_name):
        return self._get_zone(zone_name) is not None

    def get_zone_properties(self, zone_name):
        zone = self._get_zone(zone_name, ignore_missing=False)

        zone_properties = {}
        zone_properties['zone_type'] = zone.ZoneType
        zone_properties['ds_integrated'] = zone.DsIntegrated
        zone_properties['data_file_name'] = zone.DataFile
        zone_properties['master_servers'] = zone.MasterServers or []

        return zone_properties

    def zone_create(self, zone_name, zone_type, ds_integrated,
                    data_file_name=None, ip_addrs=None,
                    admin_email_name=None):
        """Creates a DNS Zone and returns the path to the associated object.

        :param zone_name: string representing the name of the zone.
        :param zone_type: type of zone
            0 = Primary zone
            1 = Secondary zone, MUST include at least one master IP
            2 = Stub zone, MUST include at least one master IP
            3 = Zone forwarder, MUST include at least one master IP
        :param ds_integrated: Only Primary zones can be stored in AD
            True = the zone data is stored in the Active Directory
            False = the data zone is stored in files
        :param data_file_name(Optional): name of the data file associated
            with the zone.
        :param ip_addrs(Optional): IP addresses of the master DNS servers
            for this zone. Parameter type MUST be list
        :param admin_email_name(Optional): email address of the administrator
            responsible for the zone.
        """
        LOG.debug("Creating DNS Zone '%s'" % zone_name)
        if self.zone_exists(zone_name):
            raise exceptions.DNSZoneAlreadyExists(zone_name=zone_name)

        dns_zone_manager = self._dns_manager.MicrosoftDNS_Zone
        (zone_path,) = dns_zone_manager.CreateZone(
            ZoneName=zone_name,
            ZoneType=zone_type,
            DsIntegrated=ds_integrated,
            DataFileName=data_file_name,
            IpAddr=ip_addrs,
            AdminEmailname=admin_email_name)
        return zone_path

    def zone_delete(self, zone_name):
        LOG.debug("Deleting DNS Zone '%s'" % zone_name)

        zone_to_be_deleted = self._get_zone(zone_name)
        if zone_to_be_deleted:
            zone_to_be_deleted.Delete_()

    def zone_modify(self, zone_name, allow_update=None, disable_wins=None,
                    notify=None, reverse=None, secure_secondaries=None):
        """Modifies properties of an existing zone. If any parameter is None,

        then that parameter will be skipped and will not be taken into
        consideration.

        :param zone_name: string representing the name of the zone.
        :param allow_update:
            0 = No updates allowed.
            1 = Zone accepts both secure and nonsecure updates.
            2 = Zone accepts secure updates only.
        :param disable_wins: Indicates whether the WINS record is replicated.
            If set to TRUE, WINS record replication is disabled.
        :param notify:
            0 = Do not notify secondaries
            1 = Notify Servers listed on the Name Servers Tab
            2 = Notify the specified servers
        :param reverse: Indicates whether the Zone is reverse (TRUE)
            or forward (FALSE).
        :param secure_secondaries:
            0 = Allowed to Any host
            1 = Only to the Servers listed on the Name Servers tab
            2 = To the following servers (destination servers IP addresses
                are specified in SecondaryServers value)
            3 = Zone transfers not allowed
        """

        zone = self._get_zone(zone_name, ignore_missing=False)

        if allow_update is not None:
            zone.AllowUpdate = allow_update
        if disable_wins is not None:
            zone.DisableWINSRecordReplication = disable_wins
        if notify is not None:
            zone.Notify = notify
        if reverse is not None:
            zone.Reverse = reverse
        if secure_secondaries is not None:
            zone.SecureSecondaries = secure_secondaries

        zone.put()

    def zone_update(self, zone_name):
        LOG.debug("Updating DNS Zone '%s'" % zone_name)

        zone = self._get_zone(zone_name, ignore_missing=False)
        if (zone.DsIntegrated and
                zone.ZoneType == constants.DNS_ZONE_TYPE_PRIMARY):
            zone.UpdateFromDS()
        elif zone.ZoneType in [constants.DNS_ZONE_TYPE_SECONDARY,
                               constants.DNS_ZONE_TYPE_STUB]:
            zone.ForceRefresh()
        elif zone.ZoneType in [constants.DNS_ZONE_TYPE_PRIMARY,
                               constants.DNS_ZONE_TYPE_FORWARD]:
            zone.ReloadZone()

    def get_zone_serial(self, zone_name):
        # Performing a manual check to make sure the zone exists before
        # trying to retrieve the MicrosoftDNS_SOAType object. Otherwise,
        # the query for MicrosoftDNS_SOAType will fail with "Generic Failure"
        if not self.zone_exists(zone_name):
            # Return None if zone was not found
            return None

        zone_soatype = self._dns_manager.MicrosoftDNS_SOAType(
            ContainerName=zone_name)
        if not zone_soatype:
            return None
        # Serial number of the SOA record
        SOA = zone_soatype[0].SerialNumber
        return int(SOA)
