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

"""
Utility class for network related operations.
Based on the "root/virtualization/v2" namespace available starting with
Hyper-V Server / Windows Server 2012.
"""
import functools
import re

from eventlet import patcher
from eventlet import tpool
from oslo_log import log as logging
from oslo_utils import units
import six

from os_win._i18n import _
from os_win import conf
from os_win import constants
from os_win import exceptions
from os_win.utils import _wqlutils
from os_win.utils import baseutils
from os_win.utils import jobutils

CONF = conf.CONF
LOG = logging.getLogger(__name__)

_PORT_PROFILE_ATTR_MAP = {
    "profile_id": "ProfileId",
    "profile_data": "ProfileData",
    "profile_name": "ProfileName",
    "net_cfg_instance_id": "NetCfgInstanceId",
    "cdn_label_id": "CdnLabelId",
    "cdn_label_string": "CdnLabelString",
    "vendor_id": "VendorId",
    "vendor_name": "VendorName",
}


class NetworkUtils(baseutils.BaseUtilsVirt):

    EVENT_TYPE_CREATE = "__InstanceCreationEvent"
    EVENT_TYPE_DELETE = "__InstanceDeletionEvent"

    _VNIC_SET_DATA = 'Msvm_SyntheticEthernetPortSettingData'
    _EXTERNAL_PORT = 'Msvm_ExternalEthernetPort'
    _ETHERNET_SWITCH_PORT = 'Msvm_EthernetSwitchPort'
    _PORT_ALLOC_SET_DATA = 'Msvm_EthernetPortAllocationSettingData'
    _PORT_VLAN_SET_DATA = 'Msvm_EthernetSwitchPortVlanSettingData'
    _PORT_PROFILE_SET_DATA = 'Msvm_EthernetSwitchPortProfileSettingData'
    _PORT_SECURITY_SET_DATA = 'Msvm_EthernetSwitchPortSecuritySettingData'
    _PORT_HW_OFFLOAD_SET_DATA = 'Msvm_EthernetSwitchPortOffloadSettingData'
    _PORT_ALLOC_ACL_SET_DATA = 'Msvm_EthernetSwitchPortAclSettingData'
    _PORT_BANDWIDTH_SET_DATA = 'Msvm_EthernetSwitchPortBandwidthSettingData'
    _PORT_EXT_ACL_SET_DATA = _PORT_ALLOC_ACL_SET_DATA
    _LAN_ENDPOINT = 'Msvm_LANEndpoint'
    _STATE_DISABLED = 3

    _VIRTUAL_SYSTEM_SETTING_DATA = 'Msvm_VirtualSystemSettingData'
    _VM_SUMMARY_ENABLED_STATE = 100
    _HYPERV_VM_STATE_ENABLED = 2

    _OFFLOAD_ENABLED = 100
    _OFFLOAD_DISABLED = 0

    _ACL_DIR_IN = 1
    _ACL_DIR_OUT = 2

    _ACL_TYPE_IPV4 = 2
    _ACL_TYPE_IPV6 = 3

    _ACL_ACTION_ALLOW = 1
    _ACL_ACTION_DENY = 2
    _ACL_ACTION_METER = 3

    _ACL_APPLICABILITY_LOCAL = 1
    _ACL_APPLICABILITY_REMOTE = 2

    _ACL_DEFAULT = 'ANY'
    _IPV4_ANY = '0.0.0.0/0'
    _IPV6_ANY = '::/0'
    _TCP_PROTOCOL = 'tcp'
    _UDP_PROTOCOL = 'udp'
    _ICMP_PROTOCOL = '1'
    _ICMPV6_PROTOCOL = '58'
    _MAX_WEIGHT = 65500

    # 2 directions x 2 address types = 4 ACLs
    _REJECT_ACLS_COUNT = 4

    _VNIC_LISTENER_TIMEOUT_MS = 2000

    _switches = {}
    _switch_ports = {}
    _vlan_sds = {}
    _profile_sds = {}
    _hw_offload_sds = {}
    _vsid_sds = {}
    _sg_acl_sds = {}
    _bandwidth_sds = {}

    def __init__(self):
        super(NetworkUtils, self).__init__()
        self._jobutils = jobutils.JobUtils()
        self._enable_cache = CONF.os_win.cache_temporary_wmi_objects

    def init_caches(self):
        if not self._enable_cache:
            LOG.info('WMI caching is disabled.')
            return

        for vswitch in self._conn.Msvm_VirtualEthernetSwitch():
            self._switches[vswitch.ElementName] = vswitch

        # map between switch port ID and switch port WMI object.
        for port in self._conn.Msvm_EthernetPortAllocationSettingData():
            self._switch_ports[port.ElementName] = port

        # VLAN and VSID setting data's InstanceID will contain the switch
        # port's InstanceID.
        switch_port_id_regex = re.compile(
            "Microsoft:[0-9A-F-]*\\\\[0-9A-F-]*\\\\[0-9A-F-]",
            flags=re.IGNORECASE)

        # map between switch port's InstanceID and their Port Profile settings
        # data WMI objects.
        for profile in self._conn.Msvm_EthernetSwitchPortProfileSettingData():
            match = switch_port_id_regex.match(profile.InstanceID)
            if match:
                self._profile_sds[match.group()] = profile

        # map between switch port's InstanceID and their VLAN setting data WMI
        # objects.
        for vlan_sd in self._conn.Msvm_EthernetSwitchPortVlanSettingData():
            match = switch_port_id_regex.match(vlan_sd.InstanceID)
            if match:
                self._vlan_sds[match.group()] = vlan_sd

        # map between switch port's InstanceID and their VSID setting data WMI
        # objects.
        for vsid_sd in self._conn.Msvm_EthernetSwitchPortSecuritySettingData():
            match = switch_port_id_regex.match(vsid_sd.InstanceID)
            if match:
                self._vsid_sds[match.group()] = vsid_sd

        # map between switch port's InstanceID and their bandwidth setting
        # data WMI objects.
        bandwidths = self._conn.Msvm_EthernetSwitchPortBandwidthSettingData()
        for bandwidth_sd in bandwidths:
            match = switch_port_id_regex.match(bandwidth_sd.InstanceID)
            if match:
                self._bandwidth_sds[match.group()] = bandwidth_sd

        # map between switch port's InstanceID and their HW offload setting
        # data WMI objects.
        hw_offloads = self._conn.Msvm_EthernetSwitchPortOffloadSettingData()
        for hw_offload_sd in hw_offloads:
            match = switch_port_id_regex.match(hw_offload_sd.InstanceID)
            if match:
                self._hw_offload_sds[match.group()] = hw_offload_sd

    def update_cache(self):
        if not self._enable_cache:
            return

        # map between switch port ID and switch port WMI object.
        self._switch_ports.clear()
        for port in self._conn.Msvm_EthernetPortAllocationSettingData():
            self._switch_ports[port.ElementName] = port

    def clear_port_sg_acls_cache(self, switch_port_name):
        self._sg_acl_sds.pop(switch_port_name, None)

    def get_vswitch_id(self, vswitch_name):
        vswitch = self._get_vswitch(vswitch_name)
        return vswitch.Name

    def get_vswitch_extensions(self, vswitch_name):
        vswitch = self._get_vswitch(vswitch_name)

        extensions = self._conn.Msvm_EthernetSwitchExtension(
            SystemName=vswitch.Name)
        dict_ext_list = [
            {'name': ext.ElementName,
             'version': ext.Version,
             'vendor': ext.Vendor,
             'description': ext.Description,
             'enabled_state': ext.EnabledState,
             'extension_type': ext.ExtensionType}
            for ext in extensions]

        return dict_ext_list

    def get_vswitch_external_network_name(self, vswitch_name):
        ext_port = self._get_vswitch_external_port(vswitch_name)
        if ext_port:
            return ext_port.ElementName

    def _get_vswitch(self, vswitch_name):
        if vswitch_name in self._switches:
            return self._switches[vswitch_name]

        vswitch = self._conn.Msvm_VirtualEthernetSwitch(
            ElementName=vswitch_name)
        if not vswitch:
            raise exceptions.HyperVvSwitchNotFound(vswitch_name=vswitch_name)
        if self._enable_cache:
            self._switches[vswitch_name] = vswitch[0]
        return vswitch[0]

    def _get_vswitch_external_port(self, vswitch_name):
        vswitch = self._get_vswitch(vswitch_name)
        ext_ports = self._conn.Msvm_ExternalEthernetPort()
        for ext_port in ext_ports:
            lan_endpoint_assoc_list = (
                self._conn.Msvm_EthernetDeviceSAPImplementation(
                    Antecedent=ext_port.path_()))
            if lan_endpoint_assoc_list:
                lan_endpoint_assoc_list = self._conn.Msvm_ActiveConnection(
                    Dependent=lan_endpoint_assoc_list[0].Dependent.path_())
                if lan_endpoint_assoc_list:
                    lan_endpoint = lan_endpoint_assoc_list[0].Antecedent
                    if lan_endpoint.SystemName == vswitch.Name:
                        return ext_port

    def vswitch_port_needed(self):
        return False

    def get_switch_ports(self, vswitch_name):
        vswitch = self._get_vswitch(vswitch_name)
        vswitch_ports = self._conn.Msvm_EthernetSwitchPort(
            SystemName=vswitch.Name)
        return set(p.Name for p in vswitch_ports)

    def get_port_by_id(self, port_id, vswitch_name):
        vswitch = self._get_vswitch(vswitch_name)
        switch_ports = self._conn.Msvm_EthernetSwitchPort(
            SystemName=vswitch.Name)
        for switch_port in switch_ports:
            if (switch_port.ElementName == port_id):
                return switch_port

    def vnic_port_exists(self, port_id):
        try:
            self._get_vnic_settings(port_id)
        except Exception:
            return False
        return True

    def get_vnic_ids(self):
        return set(
            p.ElementName
            for p in self._conn.Msvm_SyntheticEthernetPortSettingData()
            if p.ElementName is not None)

    def get_vnic_mac_address(self, switch_port_name):
        vnic = self._get_vnic_settings(switch_port_name)
        return vnic.Address

    def _get_vnic_settings(self, vnic_name):
        vnic_settings = self._conn.Msvm_SyntheticEthernetPortSettingData(
            ElementName=vnic_name)
        if not vnic_settings:
            raise exceptions.HyperVvNicNotFound(vnic_name=vnic_name)
        return vnic_settings[0]

    def get_vnic_event_listener(self, event_type):
        query = self._get_event_wql_query(cls=self._VNIC_SET_DATA,
                                          event_type=event_type,
                                          timeframe=2)
        listener = self._conn.Msvm_SyntheticEthernetPortSettingData.watch_for(
            query)

        def _poll_events(callback):
            if patcher.is_monkey_patched('thread'):
                listen = functools.partial(tpool.execute, listener,
                                           self._VNIC_LISTENER_TIMEOUT_MS)
            else:
                listen = functools.partial(listener,
                                           self._VNIC_LISTENER_TIMEOUT_MS)

            while True:
                # Retrieve one by one all the events that occurred in
                # the checked interval.
                try:
                    event = listen()
                    if event.ElementName:
                        callback(event.ElementName)
                    else:
                        LOG.warning("Ignoring port event. "
                                    "The port name is missing.")
                except exceptions.x_wmi_timed_out:
                    # no new event published.
                    pass

        return _poll_events

    def _get_event_wql_query(self, cls, event_type, timeframe=2, **where):
        """Return a WQL query used for polling WMI events.

            :param cls: the Hyper-V class polled for events.
            :param event_type: the type of event expected.
            :param timeframe: check for events that occurred in
                              the specified timeframe.
            :param where: key-value arguments which are to be included in the
                          query. For example: like=dict(foo="bar").
        """
        like = where.pop('like', {})
        like_str = " AND ".join("TargetInstance.%s LIKE '%s%%'" % (k, v)
                                for k, v in like.items())
        like_str = "AND " + like_str if like_str else ""

        query = ("SELECT * FROM %(event_type)s WITHIN %(timeframe)s "
                 "WHERE TargetInstance ISA '%(class)s' %(like)s" % {
                     'class': cls,
                     'event_type': event_type,
                     'like': like_str,
                     'timeframe': timeframe})
        return query

    def connect_vnic_to_vswitch(self, vswitch_name, switch_port_name):
        port, found = self._get_switch_port_allocation(
            switch_port_name, create=True, expected=False)
        if found and port.HostResource and port.HostResource[0]:
            # vswitch port already exists and is connected to vswitch.
            return

        vswitch = self._get_vswitch(vswitch_name)
        vnic = self._get_vnic_settings(switch_port_name)

        port.HostResource = [vswitch.path_()]
        port.Parent = vnic.path_()
        if not found:
            vm = self._get_vm_from_res_setting_data(vnic)
            self._jobutils.add_virt_resource(port, vm)
        else:
            self._jobutils.modify_virt_resource(port)

    def _get_vm_from_res_setting_data(self, res_setting_data):
        vmsettings_instance_id = res_setting_data.InstanceID.split('\\')[0]
        sd = self._conn.Msvm_VirtualSystemSettingData(
            InstanceID=vmsettings_instance_id)
        vm = self._conn.Msvm_ComputerSystem(Name=sd[0].ConfigurationID)
        return vm[0]

    def remove_switch_port(self, switch_port_name, vnic_deleted=False):
        """Removes the switch port."""
        sw_port, found = self._get_switch_port_allocation(switch_port_name,
                                                          expected=False)
        if not sw_port:
            # Port not found. It happens when the VM was already deleted.
            return

        if not vnic_deleted:
            try:
                self._jobutils.remove_virt_resource(sw_port)
            except exceptions.x_wmi:
                # port may have already been destroyed by Hyper-V
                pass

        self._switch_ports.pop(switch_port_name, None)
        self._profile_sds.pop(sw_port.InstanceID, None)
        self._vlan_sds.pop(sw_port.InstanceID, None)
        self._vsid_sds.pop(sw_port.InstanceID, None)
        self._bandwidth_sds.pop(sw_port.InstanceID, None)
        self._hw_offload_sds.pop(sw_port.InstanceID, None)

    def set_vswitch_port_profile_id(self, switch_port_name, profile_id,
                                    profile_data, profile_name, vendor_name,
                                    **kwargs):
        """Sets up the port profile id.

        :param switch_port_name: The ElementName of the vSwitch port.
        :param profile_id: The profile id to be set for the given switch port.
        :param profile_data: Additional data for the Port Profile.
        :param profile_name: The name of the Port Profile.
        :param net_cfg_instance_id: Unique device identifier of the
            sub-interface.
        :param cdn_label_id: The CDN Label Id.
        :param cdn_label_string: The CDN label string.
        :param vendor_id: The id of the Vendor defining the profile.
        :param vendor_name: The name of the Vendor defining the profile.
        """
        port_alloc = self._get_switch_port_allocation(switch_port_name)[0]
        port_profile = self._get_profile_setting_data_from_port_alloc(
            port_alloc)

        new_port_profile = self._prepare_profile_sd(
            profile_id=profile_id, profile_data=profile_data,
            profile_name=profile_name, vendor_name=vendor_name, **kwargs)

        if port_profile:
            # Removing the feature because it cannot be modified
            # due to a wmi exception.
            self._jobutils.remove_virt_feature(port_profile)

            # remove from cache.
            self._profile_sds.pop(port_alloc.InstanceID, None)

        try:
            self._jobutils.add_virt_feature(new_port_profile, port_alloc)
        except Exception as ex:
            raise exceptions.HyperVException(
                'Unable to set port profile settings %(port_profile)s '
                'for port %(port)s. Error: %(error)s' %
                dict(port_profile=new_port_profile, port=port_alloc, error=ex))

    def set_vswitch_port_vlan_id(self, vlan_id=None, switch_port_name=None,
                                 **kwargs):
        """Sets up operation mode, VLAN ID and VLAN trunk for the given port.

        :param vlan_id: the VLAN ID to be set for the given switch port.
        :param switch_port_name: the ElementName of the vSwitch port.
        :param operation_mode: the VLAN operation mode. The acceptable values
            are:
            os_win.constants.VLAN_MODE_ACCESS, os_win.constants.VLAN_TRUNK_MODE
            If not given, VLAN_MODE_ACCESS is used by default.
        :param trunk_vlans: an array of VLAN IDs to be set in trunk mode.
        :raises AttributeError: if an unsupported operation_mode is given, or
            the given operation mode is VLAN_MODE_ACCESS and the given
            trunk_vlans is not None.
        """

        operation_mode = kwargs.get('operation_mode',
                                    constants.VLAN_MODE_ACCESS)
        trunk_vlans = kwargs.get('trunk_vlans')

        if operation_mode not in [constants.VLAN_MODE_ACCESS,
                                  constants.VLAN_MODE_TRUNK]:
            msg = _('Unsupported VLAN operation mode: %s')
            raise AttributeError(msg % operation_mode)

        if (operation_mode == constants.VLAN_MODE_ACCESS and
                trunk_vlans is not None):
            raise AttributeError(_('The given operation mode is ACCESS, '
                                   'cannot set given trunk_vlans.'))

        port_alloc = self._get_switch_port_allocation(switch_port_name)[0]
        vlan_settings = self._get_vlan_setting_data_from_port_alloc(port_alloc)

        if operation_mode == constants.VLAN_MODE_ACCESS:
            new_vlan_settings = self._prepare_vlan_sd_access_mode(
                vlan_settings, vlan_id)
        else:
            new_vlan_settings = self._prepare_vlan_sd_trunk_mode(
                vlan_settings, vlan_id, trunk_vlans)

        if not new_vlan_settings:
            # if no object was returned, it means that the VLAN Setting Data
            # was already added with the desired attributes.
            return

        if vlan_settings:
            # Removing the feature because it cannot be modified
            # due to a wmi exception.
            self._jobutils.remove_virt_feature(vlan_settings)

        # remove from cache.
        self._vlan_sds.pop(port_alloc.InstanceID, None)

        self._jobutils.add_virt_feature(new_vlan_settings, port_alloc)

        # TODO(claudiub): This will help solve the missing VLAN issue, but it
        # comes with a performance cost. The root cause of the problem must
        # be solved.
        vlan_settings = self._get_vlan_setting_data_from_port_alloc(port_alloc)
        if not vlan_settings:
            raise exceptions.HyperVException(
                _('Port VLAN not found: %s') % switch_port_name)

    def _prepare_profile_sd(self, **kwargs):
        profile_id_settings = self._create_default_setting_data(
            self._PORT_PROFILE_SET_DATA)

        for argument_name, attr_name in _PORT_PROFILE_ATTR_MAP.items():
            attribute = kwargs.pop(argument_name, None)
            if attribute is None:
                continue
            setattr(profile_id_settings, attr_name, attribute)

        if kwargs:
            raise TypeError("Unrecognized attributes %r" % kwargs)

        return profile_id_settings

    def _prepare_vlan_sd_access_mode(self, vlan_settings, vlan_id):
        if vlan_settings:
            # the given vlan_id might be None.
            vlan_id = vlan_id or vlan_settings.AccessVlanId
            if (vlan_settings.OperationMode == constants.VLAN_MODE_ACCESS and
                    vlan_settings.AccessVlanId == vlan_id):
                # VLAN already set to correct value, no need to change it.
                return None

        vlan_settings = self._create_default_setting_data(
            self._PORT_VLAN_SET_DATA)
        vlan_settings.AccessVlanId = vlan_id
        vlan_settings.OperationMode = constants.VLAN_MODE_ACCESS

        return vlan_settings

    def _prepare_vlan_sd_trunk_mode(self, vlan_settings, vlan_id, trunk_vlans):
        if vlan_settings:
            # the given vlan_id might be None.
            vlan_id = vlan_id or vlan_settings.NativeVlanId
            trunk_vlans = trunk_vlans or vlan_settings.TrunkVlanIdArray or []
            trunk_vlans = sorted(trunk_vlans)
            if (vlan_settings.OperationMode == constants.VLAN_MODE_TRUNK and
                    vlan_settings.NativeVlanId == vlan_id and
                    sorted(vlan_settings.TrunkVlanIdArray) == trunk_vlans):
                # VLAN already set to correct value, no need to change it.
                return None

        vlan_settings = self._create_default_setting_data(
            self._PORT_VLAN_SET_DATA)
        vlan_settings.NativeVlanId = vlan_id
        vlan_settings.TrunkVlanIdArray = trunk_vlans
        vlan_settings.OperationMode = constants.VLAN_MODE_TRUNK

        return vlan_settings

    def set_vswitch_port_vsid(self, vsid, switch_port_name):
        self._set_switch_port_security_settings(switch_port_name,
                                                VirtualSubnetId=vsid)

    def set_vswitch_port_mac_spoofing(self, switch_port_name, state):
        """Sets the given port's MAC spoofing to the given state.

        :param switch_port_name: the name of the port which will have MAC
            spoofing set to the given state.
        :param state: boolean, if MAC spoofing should be turned on or off.
        """
        self._set_switch_port_security_settings(switch_port_name,
                                                AllowMacSpoofing=state)

    def _set_switch_port_security_settings(self, switch_port_name, **kwargs):
        port_alloc = self._get_switch_port_allocation(switch_port_name)[0]
        sec_settings = self._get_security_setting_data_from_port_alloc(
            port_alloc)

        exists = sec_settings is not None

        if exists:
            if all(getattr(sec_settings, k) == v for k, v in kwargs.items()):
                # All desired properties already properly set. Nothing to do.
                return
        else:
            sec_settings = self._create_default_setting_data(
                self._PORT_SECURITY_SET_DATA)

        for k, v in kwargs.items():
            setattr(sec_settings, k, v)

        if exists:
            self._jobutils.modify_virt_feature(sec_settings)
        else:
            self._jobutils.add_virt_feature(sec_settings, port_alloc)

        # TODO(claudiub): This will help solve the missing VSID issue, but it
        # comes with a performance cost. The root cause of the problem must
        # be solved.
        sec_settings = self._get_security_setting_data_from_port_alloc(
            port_alloc)
        if not sec_settings:
            raise exceptions.HyperVException(
                _('Port Security Settings not found: %s') % switch_port_name)

    def set_vswitch_port_sriov(self, switch_port_name, enabled):
        """Enables / Disables SR-IOV for the given port.

        :param switch_port_name: the name of the port which will have SR-IOV
            enabled or disabled.
        :param enabled: boolean, if SR-IOV should be turned on or off.
        """
        # TODO(claudiub): We have added a different method that sets all sorts
        # of offloading options on a vswitch port, including SR-IOV.
        # Remove this method in S.
        self.set_vswitch_port_offload(switch_port_name, sriov_enabled=enabled)

    def set_vswitch_port_offload(self, switch_port_name, sriov_enabled=None,
                                 iov_queues_requested=None, vmq_enabled=None,
                                 offloaded_sa=None):
        """Enables / Disables different offload options for the given port.

        Optional prameters are ignored if they are None.

        :param switch_port_name: the name of the port which will have VMQ
            enabled or disabled.
        :param sriov_enabled: if SR-IOV should be turned on or off.
        :param iov_queues_requested: the number of IOV queues to use. (> 1)
        :param vmq_enabled: if VMQ should be turned on or off.
        :param offloaded_sa: the number of IPsec SA offloads to use. (> 1)
        :raises os_win.exceptions.InvalidParameterValue: if an invalid value
            is passed for the iov_queues_requested or offloaded_sa parameters.
        """

        if iov_queues_requested is not None and iov_queues_requested < 1:
            raise exceptions.InvalidParameterValue(
                param_name='iov_queues_requested',
                param_value=iov_queues_requested)

        if offloaded_sa is not None and offloaded_sa < 1:
            raise exceptions.InvalidParameterValue(
                param_name='offloaded_sa',
                param_value=offloaded_sa)

        port_alloc = self._get_switch_port_allocation(switch_port_name)[0]

        # NOTE(claudiub): All ports have a HW offload SD.
        hw_offload_sd = self._get_hw_offload_sd_from_port_alloc(port_alloc)
        sd_changed = False

        if sriov_enabled is not None:
            desired_state = (self._OFFLOAD_ENABLED if sriov_enabled else
                             self._OFFLOAD_DISABLED)
            if hw_offload_sd.IOVOffloadWeight != desired_state:
                hw_offload_sd.IOVOffloadWeight = desired_state
                sd_changed = True

        if iov_queues_requested is not None:
            if hw_offload_sd.IOVQueuePairsRequested != iov_queues_requested:
                hw_offload_sd.IOVQueuePairsRequested = iov_queues_requested
                sd_changed = True

        if vmq_enabled is not None:
            desired_state = (self._OFFLOAD_ENABLED if vmq_enabled else
                             self._OFFLOAD_DISABLED)
            if hw_offload_sd.VMQOffloadWeight != desired_state:
                hw_offload_sd.VMQOffloadWeight = desired_state
                sd_changed = True

        if offloaded_sa is not None:
            if hw_offload_sd.IPSecOffloadLimit != offloaded_sa:
                hw_offload_sd.IPSecOffloadLimit = offloaded_sa
                sd_changed = True

        # NOTE(claudiub): The HW offload SD can simply be modified. No need to
        # remove it and create a new one.
        if sd_changed:
            self._jobutils.modify_virt_feature(hw_offload_sd)

    def _get_profile_setting_data_from_port_alloc(self, port_alloc):
        return self._get_setting_data_from_port_alloc(
            port_alloc, self._profile_sds, self._PORT_PROFILE_SET_DATA)

    def _get_vlan_setting_data_from_port_alloc(self, port_alloc):
        return self._get_setting_data_from_port_alloc(
            port_alloc, self._vlan_sds, self._PORT_VLAN_SET_DATA)

    def _get_security_setting_data_from_port_alloc(self, port_alloc):
        return self._get_setting_data_from_port_alloc(
            port_alloc, self._vsid_sds, self._PORT_SECURITY_SET_DATA)

    def _get_hw_offload_sd_from_port_alloc(self, port_alloc):
        return self._get_setting_data_from_port_alloc(
            port_alloc, self._hw_offload_sds, self._PORT_HW_OFFLOAD_SET_DATA)

    def _get_bandwidth_setting_data_from_port_alloc(self, port_alloc):
        return self._get_setting_data_from_port_alloc(
            port_alloc, self._bandwidth_sds, self._PORT_BANDWIDTH_SET_DATA)

    def _get_setting_data_from_port_alloc(self, port_alloc, cache, data_class):
        if port_alloc.InstanceID in cache:
            return cache[port_alloc.InstanceID]

        setting_data = self._get_first_item(
            _wqlutils.get_element_associated_class(
                self._conn, data_class,
                element_instance_id=port_alloc.InstanceID))
        if setting_data and self._enable_cache:
            cache[port_alloc.InstanceID] = setting_data
        return setting_data

    def _get_switch_port_allocation(self, switch_port_name, create=False,
                                    expected=True):
        if switch_port_name in self._switch_ports:
            return self._switch_ports[switch_port_name], True

        switch_port, found = self._get_setting_data(
            self._PORT_ALLOC_SET_DATA,
            switch_port_name, create)

        if found:
            # newly created setting data cannot be cached, they do not
            # represent real objects yet.
            # if it was found, it means that it was not created.
            if self._enable_cache:
                self._switch_ports[switch_port_name] = switch_port
        elif expected:
            raise exceptions.HyperVPortNotFoundException(
                port_name=switch_port_name)
        return switch_port, found

    def _get_setting_data(self, class_name, element_name, create=True):
        element_name = element_name.replace("'", '"')
        q = self._compat_conn.query("SELECT * FROM %(class_name)s WHERE "
                                    "ElementName = '%(element_name)s'" %
                                    {"class_name": class_name,
                                     "element_name": element_name})
        data = self._get_first_item(q)
        found = data is not None
        if not data and create:
            data = self._get_default_setting_data(class_name)
            data.ElementName = element_name
        return data, found

    def _get_default_setting_data(self, class_name):
        return self._compat_conn.query("SELECT * FROM %s WHERE InstanceID "
                                       "LIKE '%%\\Default'" % class_name)[0]

    def _create_default_setting_data(self, class_name):
        return getattr(self._compat_conn, class_name).new()

    def _get_first_item(self, obj):
        if obj:
            return obj[0]

    def add_metrics_collection_acls(self, switch_port_name):
        port = self._get_switch_port_allocation(switch_port_name)[0]

        # Add the ACLs only if they don't already exist
        acls = _wqlutils.get_element_associated_class(
            self._conn, self._PORT_ALLOC_ACL_SET_DATA,
            element_instance_id=port.InstanceID)
        for acl_type in [self._ACL_TYPE_IPV4, self._ACL_TYPE_IPV6]:
            for acl_dir in [self._ACL_DIR_IN, self._ACL_DIR_OUT]:
                _acls = self._filter_acls(
                    acls, self._ACL_ACTION_METER, acl_dir, acl_type)

                if not _acls:
                    acl = self._create_acl(
                        acl_dir, acl_type, self._ACL_ACTION_METER)
                    self._jobutils.add_virt_feature(acl, port)

    def is_metrics_collection_allowed(self, switch_port_name):
        port = self._get_switch_port_allocation(switch_port_name)[0]

        if not self._is_port_vm_started(port):
            return False

        # all 4 meter ACLs must be existent first. (2 x direction)
        acls = _wqlutils.get_element_associated_class(
            self._conn, self._PORT_ALLOC_ACL_SET_DATA,
            element_instance_id=port.InstanceID)
        acls = [a for a in acls if a.Action == self._ACL_ACTION_METER]
        if len(acls) < 2:
            return False
        return True

    def _is_port_vm_started(self, port):
        vmsettings_instance_id = port.InstanceID.split('\\')[0]
        vmsettings = self._conn.Msvm_VirtualSystemSettingData(
            InstanceID=vmsettings_instance_id)
        # See http://msdn.microsoft.com/en-us/library/cc160706%28VS.85%29.aspx
        (ret_val, summary_info) = self._vs_man_svc.GetSummaryInformation(
            [self._VM_SUMMARY_ENABLED_STATE],
            [v.path_() for v in vmsettings])
        if ret_val or not summary_info:
            raise exceptions.HyperVException(_('Cannot get VM summary data '
                                               'for: %s') % port.ElementName)

        return summary_info[0].EnabledState == self._HYPERV_VM_STATE_ENABLED

    def create_security_rules(self, switch_port_name, sg_rules):
        port = self._get_switch_port_allocation(switch_port_name)[0]

        self._bind_security_rules(port, sg_rules)

    def remove_security_rules(self, switch_port_name, sg_rules):
        port = self._get_switch_port_allocation(switch_port_name)[0]

        acls = _wqlutils.get_element_associated_class(
            self._conn, self._PORT_EXT_ACL_SET_DATA,
            element_instance_id=port.InstanceID)
        remove_acls = []
        for sg_rule in sg_rules:
            filtered_acls = self._filter_security_acls(sg_rule, acls)
            remove_acls.extend(filtered_acls)

        if remove_acls:
            self._jobutils.remove_multiple_virt_features(remove_acls)

            # remove the old ACLs from the cache.
            new_acls = [a for a in acls if a not in remove_acls]
            self._sg_acl_sds[port.ElementName] = new_acls

    def remove_all_security_rules(self, switch_port_name):
        port = self._get_switch_port_allocation(switch_port_name)[0]

        acls = _wqlutils.get_element_associated_class(
            self._conn, self._PORT_EXT_ACL_SET_DATA,
            element_instance_id=port.InstanceID)
        filtered_acls = [a for a in acls if
                         a.Action != self._ACL_ACTION_METER]

        if filtered_acls:
            self._jobutils.remove_multiple_virt_features(filtered_acls)

            # clear the cache.
            self._sg_acl_sds[port.ElementName] = []

    def _bind_security_rules(self, port, sg_rules):
        acls = _wqlutils.get_element_associated_class(
            self._conn, self._PORT_EXT_ACL_SET_DATA,
            element_instance_id=port.InstanceID)

        # Add the ACL only if it don't already exist.
        add_acls = []
        processed_sg_rules = []
        weights = self._get_new_weights(sg_rules, acls)
        index = 0

        for sg_rule in sg_rules:
            filtered_acls = self._filter_security_acls(sg_rule, acls)
            if filtered_acls:
                # ACL already exists.
                continue

            acl = self._create_security_acl(sg_rule, weights[index])
            add_acls.append(acl)
            index += 1

            # append sg_rule the acls list, to make sure that the same rule
            # is not processed twice.
            processed_sg_rules.append(sg_rule)

        if add_acls:
            self._jobutils.add_multiple_virt_features(add_acls, port)

            # caching the Security Group Rules that have been processed and
            # added to the port. The list should only be used to check the
            # existence of rules, nothing else.
            acls.extend(processed_sg_rules)

    def _get_port_security_acls(self, port):
        """Returns a mutable list of Security Group Rule objects.

        Returns the list of Security Group Rule objects from the cache,
        otherwise it fetches and caches from the port's associated class.
        """

        if port.ElementName in self._sg_acl_sds:
            return self._sg_acl_sds[port.ElementName]

        acls = _wqlutils.get_element_associated_class(
            self._conn, self._PORT_EXT_ACL_SET_DATA,
            element_instance_id=port.InstanceID)
        if self._enable_cache:
            self._sg_acl_sds[port.ElementName] = acls

        return acls

    def _create_acl(self, direction, acl_type, action):
        acl = self._create_default_setting_data(self._PORT_ALLOC_ACL_SET_DATA)
        acl.set(Direction=direction,
                AclType=acl_type,
                Action=action,
                Applicability=self._ACL_APPLICABILITY_LOCAL)
        return acl

    def _create_security_acl(self, sg_rule, weight):
        # Acl instance can be created new each time, the object should be
        # of type ExtendedEthernetSettingsData.
        acl = self._create_default_setting_data(self._PORT_EXT_ACL_SET_DATA)
        acl.set(**sg_rule.to_dict())
        return acl

    def _filter_acls(self, acls, action, direction, acl_type, remote_addr=""):
        return [v for v in acls
                if v.Action == action and
                v.Direction == direction and
                v.AclType == acl_type and
                v.RemoteAddress == remote_addr]

    def _filter_security_acls(self, sg_rule, acls):
        return [a for a in acls if sg_rule == a]

    def _get_new_weights(self, sg_rules, existent_acls):
        """Computes the weights needed for given sg_rules.

        :param sg_rules: ACLs to be added. They must have the same Action.
        :existent_acls: ACLs already bound to a switch port.
        :return: list of weights which will be used to create ACLs. List will
                 have the recommended order for sg_rules' Action.
        """
        return [0] * len(sg_rules)

    def set_port_qos_rule(self, port_id, qos_rule):
        """Sets the QoS rule for the given port.

        :param port_id: the port's ID to which the QoS rule will be applied to.
        :param qos_rule: a dictionary containing the following keys:
            min_kbps, max_kbps, max_burst_kbps, max_burst_size_kb.
        :raises exceptions.HyperVInvalidException: if
            - min_kbps is smaller than 10MB.
            - max_kbps is smaller than min_kbps.
            - max_burst_kbps is smaller than max_kbps.
        :raises exceptions.HyperVException: if the QoS rule cannot be set.
        """

        # Hyper-V stores bandwidth limits in bytes.
        min_bps = qos_rule.get("min_kbps", 0) * units.Ki
        max_bps = qos_rule.get("max_kbps", 0) * units.Ki
        max_burst_bps = qos_rule.get("max_burst_kbps", 0) * units.Ki
        max_burst_sz = qos_rule.get("max_burst_size_kb", 0) * units.Ki

        if not (min_bps or max_bps or max_burst_bps or max_burst_sz):
            # no limits need to be set
            return

        if min_bps and min_bps < 10 * units.Mi:
            raise exceptions.InvalidParameterValue(
                param_name="min_kbps", param_value=min_bps)
        if max_bps and max_bps < min_bps:
            raise exceptions.InvalidParameterValue(
                param_name="max_kbps", param_value=max_bps)
        if max_burst_bps and max_burst_bps < max_bps:
            raise exceptions.InvalidParameterValue(
                param_name="max_burst_kbps", param_value=max_burst_bps)

        port_alloc = self._get_switch_port_allocation(port_id)[0]
        bandwidth = self._get_bandwidth_setting_data_from_port_alloc(
            port_alloc)
        if bandwidth:
            # Removing the feature because it cannot be modified
            # due to a wmi exception.
            self._jobutils.remove_virt_feature(bandwidth)

            # remove from cache.
            self._bandwidth_sds.pop(port_alloc.InstanceID, None)

        bandwidth = self._get_default_setting_data(
            self._PORT_BANDWIDTH_SET_DATA)
        bandwidth.Reservation = min_bps
        bandwidth.Limit = max_bps
        bandwidth.BurstLimit = max_burst_bps
        bandwidth.BurstSize = max_burst_sz

        try:
            self._jobutils.add_virt_feature(bandwidth, port_alloc)
        except Exception as ex:
            if '0x80070057' in six.text_type(ex):
                raise exceptions.InvalidParameterValue(
                    param_name="qos_rule", param_value=qos_rule)
            raise exceptions.HyperVException(
                'Unable to set qos rule %(qos_rule)s for port %(port)s. '
                'Error: %(error)s' %
                dict(qos_rule=qos_rule, port=port_alloc, error=ex))

    def remove_port_qos_rule(self, port_id):
        """Removes the QoS rule from the given port.

        :param port_id: the port's ID from which the QoS rule will be removed.
        """
        port_alloc = self._get_switch_port_allocation(port_id)[0]
        bandwidth = self._get_bandwidth_setting_data_from_port_alloc(
            port_alloc)
        if bandwidth:
            self._jobutils.remove_virt_feature(bandwidth)
            # remove from cache.
            self._bandwidth_sds.pop(port_alloc.InstanceID, None)


class NetworkUtilsR2(NetworkUtils):
    _PORT_EXT_ACL_SET_DATA = 'Msvm_EthernetSwitchPortExtendedAclSettingData'
    _MAX_WEIGHT = 65500

    # 2 directions x 2 address types x 4 protocols = 16 ACLs
    _REJECT_ACLS_COUNT = 16

    def _create_security_acl(self, sg_rule, weight):
        acl = super(NetworkUtilsR2, self)._create_security_acl(sg_rule,
                                                               weight)
        acl.Weight = weight
        sg_rule.Weight = weight
        return acl

    def _get_new_weights(self, sg_rules, existent_acls):
        sg_rule = sg_rules[0]
        num_rules = len(sg_rules)
        existent_acls = [a for a in existent_acls
                         if a.Action == sg_rule.Action]
        if not existent_acls:
            if sg_rule.Action == self._ACL_ACTION_DENY:
                return list(range(1, 1 + num_rules))
            else:
                return list(range(self._MAX_WEIGHT - 1,
                                  self._MAX_WEIGHT - 1 - num_rules, - 1))

        # there are existent ACLs.
        weights = [a.Weight for a in existent_acls]
        if sg_rule.Action == self._ACL_ACTION_DENY:
            return [i for i in list(range(1, self._REJECT_ACLS_COUNT + 1))
                    if i not in weights][:num_rules]

        min_weight = min(weights)
        last_weight = min_weight - num_rules - 1
        if last_weight > self._REJECT_ACLS_COUNT:
            return list(range(min_weight - 1, last_weight, - 1))

        # not enough weights. Must search for available weights.
        # if it is this case, num_rules is a small number.
        current_weight = self._MAX_WEIGHT - 1
        new_weights = []
        for i in list(range(num_rules)):
            while current_weight in weights:
                current_weight -= 1
            new_weights.append(current_weight)

        return new_weights
