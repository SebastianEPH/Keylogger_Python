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

"""
Utility class for VM related operations on Hyper-V.
"""

import sys

from os_win._i18n import _

# Define WMI specific exceptions, so WMI won't have to be imported in any
# module that expects those exceptions.
if sys.platform == 'win32':
    from six.moves.builtins import WindowsError
    import wmi

    x_wmi = wmi.x_wmi
    x_wmi_timed_out = wmi.x_wmi_timed_out
else:
    class WindowsError(Exception):
        def __init__(self, winerror=None):
            self.winerror = winerror

    class x_wmi(Exception):
        def __init__(self, info='', com_error=None):
            super(x_wmi, self).__init__(info)
            self.info = info
            self.com_error = com_error

    class x_wmi_timed_out(x_wmi):
        pass


class OSWinException(Exception):
    msg_fmt = 'An exception has been encountered.'

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs
        self.error_code = kwargs.get('error_code')

        if not message:
            message = self.msg_fmt % kwargs

        self.message = message
        super(OSWinException, self).__init__(message)


class NotFound(OSWinException):
    msg_fmt = _("Resource could not be found: %(resource)s")


class PciDeviceNotFound(NotFound):
    msg_fmt = _("No assignable PCI device with vendor id: %(vendor_id)s and "
                "product id: %(product_id)s was found.")


class HyperVException(OSWinException):
    pass


# TODO(alexpilotti): Add a storage exception base class
class VHDResizeException(HyperVException):
    msg_fmt = _("Exception encountered while resizing the VHD %(vhd_path)s."
                "Reason: %(reason)s")


class HyperVAuthorizationException(HyperVException):
    msg_fmt = _("The Windows account running nova-compute on this Hyper-V "
                "host doesn't have the required permissions to perform "
                "Hyper-V related operations.")


class HyperVVMNotFoundException(NotFound, HyperVException):
    msg_fmt = _("VM not found: %(vm_name)s")


class HyperVPortNotFoundException(NotFound, HyperVException):
    msg_fmt = _("Switch port not found: %(port_name)s")


class HyperVvNicNotFound(NotFound, HyperVException):
    msg_fmt = _("vNic not found: %(vnic_name)s")


class HyperVvSwitchNotFound(NotFound, HyperVException):
    msg_fmt = _("vSwitch not found: %(vswitch_name)s.")


class Invalid(OSWinException):
    pass


class UnsupportedOperation(Invalid):
    msg_fmt = _("The operation failed due to the reason: %(reason)s")


class InvalidParameterValue(Invalid):
    msg_fmt = _("Invalid parameter value for: "
                "%(param_name)s=%(param_value)s")


class InvalidVMVersion(Invalid):
    msg_fmt = _("VM '%(vm_name)s' has an invalid version for this operation: "
                "%(version)s. Version is expected to be between: "
                "%(min_version)s and %(max_version)s.")


class SMBException(OSWinException):
    pass


class Win32Exception(OSWinException):
    msg_fmt = _("Executing Win32 API function %(func_name)s failed. "
                "Error code: %(error_code)s. "
                "Error message: %(error_message)s")


class VHDException(OSWinException):
    pass


class VHDWin32APIException(VHDException, Win32Exception):
    pass


class FCException(OSWinException):
    pass


class FCWin32Exception(FCException, Win32Exception):
    pass


class WMIException(OSWinException):
    def __init__(self, message=None, wmi_exc=None):
        if wmi_exc:
            try:
                wmi_exc_message = wmi_exc.com_error.excepinfo[2].strip()
                message = "%s WMI exception message: %s" % (message,
                                                            wmi_exc_message)
            except AttributeError:
                pass
            except IndexError:
                pass
        super(WMIException, self).__init__(message)


class WqlException(OSWinException):
    pass


class ISCSITargetException(OSWinException):
    pass


class ISCSITargetWMIException(ISCSITargetException, WMIException):
    pass


class ISCSIInitiatorAPIException(Win32Exception):
    pass


class ISCSILunNotAvailable(ISCSITargetException):
    msg_fmt = _("Could not find lun %(target_lun)s "
                "for iSCSI target %(target_iqn)s.")


class Win32IOException(Win32Exception):
    pass


class DiskNotFound(NotFound):
    pass


class HyperVRemoteFXException(HyperVException):
    pass


class HyperVClusterException(HyperVException):
    pass


class DNSException(OSWinException):
    pass


class Timeout(OSWinException):
    msg_fmt = _("Timed out waiting for the specified resource.")


class DNSZoneNotFound(NotFound, DNSException):
    msg_fmt = _("DNS Zone not found: %(zone_name)s")


class DNSZoneAlreadyExists(DNSException):
    msg_fmt = _("DNS Zone already exists: %(zone_name)s")


class WMIJobFailed(HyperVException):
    msg_fmt = _("WMI job failed with status %(job_state)s. "
                "Error summary description: %(error_summ_desc)s. "
                "Error description: %(error_desc)s "
                "Error code: %(error_code)s.")

    def __init__(self, message=None, **kwargs):
        self.error_code = kwargs.get('error_code', None)
        self.job_state = kwargs.get('job_state', None)

        super(WMIJobFailed, self).__init__(message, **kwargs)


class JobTerminateFailed(HyperVException):
    msg_fmt = _("Could not terminate the requested job(s).")


class ClusterException(OSWinException):
    pass


class ClusterObjectNotFound(NotFound, ClusterException):
    pass


class ClusterWin32Exception(ClusterException, Win32Exception):
    pass


class ClusterGroupMigrationFailed(ClusterException):
    msg_fmt = _("Failed to migrate cluster group %(group_name)s. "
                "Expected state %(expected_state)s. "
                "Expected owner node: %(expected_node)s. "
                "Current group state: %(group_state)s. "
                "Current owner node: %(owner_node)s.")


class ClusterGroupMigrationTimeOut(ClusterGroupMigrationFailed):
    msg_fmt = _("Cluster group '%(group_name)s' migration "
                "timed out after %(time_elapsed)0.3fs. ")


class ClusterPropertyRetrieveFailed(ClusterException):
    msg_fmt = _("Failed to retrieve a cluster property.")


class ClusterPropertyListEntryNotFound(ClusterPropertyRetrieveFailed):
    msg_fmt = _("The specified cluster property list does not contain "
                "an entry named '%(property_name)s'")


class ClusterPropertyListParsingError(ClusterPropertyRetrieveFailed):
    msg_fmt = _("Parsing a cluster property list failed.")


class SCSIPageParsingError(Invalid):
    msg_fmt = _("Parsing SCSI Page %(page)s failed. "
                "Reason: %(reason)s.")


class SCSIIdDescriptorParsingError(Invalid):
    msg_fmt = _("Parsing SCSI identification descriptor failed. "
                "Reason: %(reason)s.")


class ResourceUpdateError(OSWinException):
    msg_fmt = _("Failed to update the specified resource.")


class DiskUpdateError(OSWinException):
    msg_fmt = _("Failed to update the specified disk.")
