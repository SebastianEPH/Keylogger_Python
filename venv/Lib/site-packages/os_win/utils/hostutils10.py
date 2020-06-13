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

from os_win._i18n import _
from os_win import exceptions
from os_win.utils import hostutils
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class HostUtils10(hostutils.HostUtils):

    _HGS_NAMESPACE = '//%s/Root/Microsoft/Windows/Hgs'

    _PCI_VENDOR_ID_REGEX = re.compile('VEN_(.*)&DEV', re.IGNORECASE)
    _PCI_PRODUCT_ID_REGEX = re.compile('DEV_(.*)&SUBSYS', re.IGNORECASE)
    _PCI_ADDRESS_REGEX = re.compile(r'\b\d+\b')

    def __init__(self, host='.'):
        super(HostUtils10, self).__init__(host)
        self._conn_hgs_attr = None

    @property
    def _conn_hgs(self):
        if not self._conn_hgs_attr:
            try:
                namespace = self._HGS_NAMESPACE % self._host
                self._conn_hgs_attr = self._get_wmi_conn(namespace)
            except Exception:
                raise exceptions.OSWinException(
                    _("Namespace %(namespace)s is not supported on this "
                      "Windows version.") %
                    {'namespace': namespace})

        return self._conn_hgs_attr

    def is_host_guarded(self):
        """Checks the host is guarded so it can run Shielded VMs"""

        (return_code,
         host_config) = self._conn_hgs.MSFT_HgsClientConfiguration.Get()
        if return_code:
            LOG.warning('Retrieving the local Host Guardian Service '
                        'Client configuration failed with code: %s',
                        return_code)
            return False
        return host_config.IsHostGuarded

    def supports_nested_virtualization(self):
        """Checks if the host supports nested virtualization.

        :returns: True, Windows / Hyper-V Server 2016 or newer supports nested
            virtualization.
        """
        return True

    def get_pci_passthrough_devices(self):
        """Get host's assignable PCI devices.

        :returns: a list of the assignable PCI devices.
        """
        # NOTE(claudiub): pci_device_objects contains all available PCI
        # devices. When a PCI device is used, another object containing the
        # same devices_instance_path is added.
        pci_device_objects = self._conn.Msvm_PciExpress()

        pci_devices = []
        processed_pci_dev_path = []
        for pci_obj in pci_device_objects:
            pci_path = pci_obj.DeviceInstancePath
            if pci_path in processed_pci_dev_path:
                continue

            address = self._get_pci_device_address(pci_path)
            vendor_id = self._PCI_VENDOR_ID_REGEX.findall(pci_path)
            product_id = self._PCI_PRODUCT_ID_REGEX.findall(pci_path)

            if not (address and vendor_id and product_id):
                # vendor_id / product_id / address not found.
                # skip this PCI device.
                continue

            pci_devices.append({
                'address': address,
                'vendor_id': vendor_id[0],
                'product_id': product_id[0],
                'dev_id': pci_obj.DeviceID,
            })
            processed_pci_dev_path.append(pci_path)

        return pci_devices

    def _get_pci_device_address(self, pci_device_path):
        pnp_device = self._conn_cimv2.Win32_PnPEntity(DeviceID=pci_device_path)
        (return_code, pnp_device_props) = pnp_device[0].GetDeviceProperties()
        if return_code:
            # The properties of the Plug and Play device could not be retrieved
            LOG.debug('Failed to get PnP Device Properties for the PCI '
                      'device: %(pci_dev)s. (return_code=%(return_code)s',
                      {'pci_dev': pci_device_path, 'return_code': return_code})
            return None

        pnp_props = {prop.KeyName: prop.Data for prop in pnp_device_props}
        location_info = pnp_props.get('DEVPKEY_Device_LocationInfo')
        slot = pnp_props.get('DEVPKEY_Device_Address')

        try:
            [bus, domain, funct] = self._PCI_ADDRESS_REGEX.findall(
                location_info)
            address = "%04x:%02x:%02x.%1x" % (
                int(domain), int(bus), int(slot), int(funct))
            return address
        except Exception as ex:
            LOG.debug('Failed to get PCI device address. Device path: '
                      '%(device_path)s. Exception: %(ex)s',
                      {'device_path': pci_device_path, 'ex': ex})
            return None
