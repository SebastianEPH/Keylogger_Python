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

import collections
import ctypes
import os
import re
import threading

from oslo_log import log as logging

from os_win._i18n import _
from os_win import _utils
from os_win import constants
from os_win import exceptions
from os_win.utils import baseutils
from os_win.utils import pathutils
from os_win.utils import win32utils
from os_win.utils.winapi import libs as w_lib

kernel32 = w_lib.get_shared_lib_handle(w_lib.KERNEL32)

LOG = logging.getLogger(__name__)


class DEVICE_ID_VPD_PAGE(ctypes.BigEndianStructure):
    _fields_ = [
        ('DeviceType', ctypes.c_ubyte, 5),
        ('Qualifier', ctypes.c_ubyte, 3),
        ('PageCode', ctypes.c_ubyte),
        ('PageLength', ctypes.c_uint16)
    ]


class IDENTIFICATION_DESCRIPTOR(ctypes.Structure):
    _fields_ = [
        ('CodeSet', ctypes.c_ubyte, 4),
        ('ProtocolIdentifier', ctypes.c_ubyte, 4),
        ('IdentifierType', ctypes.c_ubyte, 4),
        ('Association', ctypes.c_ubyte, 2),
        ('_reserved', ctypes.c_ubyte, 1),
        ('Piv', ctypes.c_ubyte, 1),
        ('_reserved', ctypes.c_ubyte),
        ('IdentifierLength', ctypes.c_ubyte)
    ]


PDEVICE_ID_VPD_PAGE = ctypes.POINTER(DEVICE_ID_VPD_PAGE)
PIDENTIFICATION_DESCRIPTOR = ctypes.POINTER(IDENTIFICATION_DESCRIPTOR)

SCSI_ID_ASSOC_TYPE_DEVICE = 0
SCSI_ID_CODE_SET_BINARY = 1
SCSI_ID_CODE_SET_ASCII = 2

BUS_FILE_BACKED_VIRTUAL = 15

_RESCAN_LOCK = threading.Lock()


class DiskUtils(baseutils.BaseUtils):

    _wmi_cimv2_namespace = 'root/cimv2'
    _wmi_storage_namespace = 'root/microsoft/windows/storage'

    def __init__(self):
        self._conn_cimv2 = self._get_wmi_conn(self._wmi_cimv2_namespace)
        self._conn_storage = self._get_wmi_conn(self._wmi_storage_namespace)
        self._win32_utils = win32utils.Win32Utils()

        # Physical device names look like \\.\PHYSICALDRIVE1
        self._phys_dev_name_regex = re.compile(r'\\\\.*\\[a-zA-Z]*([\d]+)')
        self._pathutils = pathutils.PathUtils()

    def _get_disk_by_number(self, disk_number, msft_disk_cls=True):
        if msft_disk_cls:
            disk = self._conn_storage.Msft_Disk(Number=disk_number)
        else:
            disk = self._conn_cimv2.Win32_DiskDrive(Index=disk_number)

        if not disk:
            err_msg = _("Could not find the disk number %s")
            raise exceptions.DiskNotFound(err_msg % disk_number)
        return disk[0]

    def _get_disks_by_unique_id(self, unique_id, unique_id_format):
        # In some cases, multiple disks having the same unique id may be
        # exposed to the OS. This may happen if there are multiple paths
        # to the LUN and MPIO is not properly configured. This can be
        # valuable information to the caller.
        disks = self._conn_storage.Msft_Disk(UniqueId=unique_id,
                                             UniqueIdFormat=unique_id_format)
        if not disks:
            err_msg = _("Could not find any disk having unique id "
                        "'%(unique_id)s' and unique id format "
                        "'%(unique_id_format)s'")
            raise exceptions.DiskNotFound(err_msg % dict(
                unique_id=unique_id,
                unique_id_format=unique_id_format))
        return disks

    def get_attached_virtual_disk_files(self):
        """Retrieve a list of virtual disks attached to the host.

        This doesn't include disks attached to Hyper-V VMs directly.
        """
        disks = self._conn_storage.Msft_Disk(BusType=BUS_FILE_BACKED_VIRTUAL)
        return [
            dict(location=disk.Location,
                 number=disk.Number,
                 offline=disk.IsOffline,
                 readonly=disk.IsReadOnly)
            for disk in disks]

    def is_virtual_disk_file_attached(self, path):
        # There are multiple ways of checking this. The easiest way would be to
        # query the disk using virtdisk.dll:GetVirtualDiskInformation and look
        # for the IsLoaded attribute. The issue with that is that in some
        # cases, it won't be able to open in-use images.
        #
        # Instead, we'll get a list of attached virtual disks and see if the
        # path we got points to any of those, thus properly handling the
        # situation in which multiple paths can point to the same file
        # (e.g. when having symlinks, shares, UNC paths, etc). We still have
        # to open the files but at least we have better control over the open
        # flags.
        if not os.path.exists(path):
            LOG.debug("Image %s could not be found.", path)
            return False

        attached_disks = self.get_attached_virtual_disk_files()
        for disk in attached_disks:
            if self._pathutils.is_same_file(path, disk['location']):
                return True
        return False

    def get_disk_numbers_by_unique_id(self, unique_id, unique_id_format):
        disks = self._get_disks_by_unique_id(unique_id, unique_id_format)
        return [disk.Number for disk in disks]

    def get_disk_uid_and_uid_type(self, disk_number):
        disk = self._get_disk_by_number(disk_number)
        return disk.UniqueId, disk.UniqueIdFormat

    def is_mpio_disk(self, disk_number):
        disk = self._get_disk_by_number(disk_number)
        return disk.Path.lower().startswith(r'\\?\mpio')

    def refresh_disk(self, disk_number):
        disk = self._get_disk_by_number(disk_number)
        disk.Refresh()

    def get_device_name_by_device_number(self, device_number):
        disk = self._get_disk_by_number(device_number,
                                        msft_disk_cls=False)
        return disk.Name

    def get_device_number_from_device_name(self, device_name):
        matches = self._phys_dev_name_regex.findall(device_name)
        if matches:
            return matches[0]

        err_msg = _("Could not find device number for device: %s")
        raise exceptions.DiskNotFound(err_msg % device_name)

    def rescan_disks(self, merge_requests=False):
        """Perform a disk rescan.

        :param merge_requests: If this flag is set and a disk rescan is
                               already pending, we'll just wait for it to
                               finish without issuing a new rescan request.
        """
        if merge_requests:
            rescan_pending = _RESCAN_LOCK.locked()
            if rescan_pending:
                LOG.debug("A disk rescan is already pending. "
                          "Waiting for it to complete.")

            with _RESCAN_LOCK:
                if not rescan_pending:
                    self._rescan_disks()
        else:
            self._rescan_disks()

    @_utils.retry_decorator(exceptions=(exceptions.x_wmi,
                                        exceptions.OSWinException))
    def _rescan_disks(self):
        LOG.debug("Rescanning disks.")

        ret = self._conn_storage.Msft_StorageSetting.UpdateHostStorageCache()

        if isinstance(ret, collections.Iterable):
            ret = ret[0]

        if ret:
            err_msg = _("Rescanning disks failed. Error code: %s.")
            raise exceptions.OSWinException(err_msg % ret)

        LOG.debug("Finished rescanning disks.")

    def get_disk_capacity(self, path, ignore_errors=False):
        """Returns total/free space for a given directory."""
        norm_path = os.path.abspath(path)

        total_bytes = ctypes.c_ulonglong(0)
        free_bytes = ctypes.c_ulonglong(0)

        try:
            self._win32_utils.run_and_check_output(
                kernel32.GetDiskFreeSpaceExW,
                ctypes.c_wchar_p(norm_path),
                None,
                ctypes.pointer(total_bytes),
                ctypes.pointer(free_bytes),
                kernel32_lib_func=True)
            return total_bytes.value, free_bytes.value
        except exceptions.Win32Exception as exc:
            LOG.error("Could not get disk %(path)s capacity info. "
                      "Exception: %(exc)s",
                      dict(path=path,
                           exc=exc))
            if ignore_errors:
                return 0, 0
            else:
                raise exc

    def get_disk_size(self, disk_number):
        """Returns the disk size, given a physical disk number."""
        disk = self._get_disk_by_number(disk_number)
        return disk.Size

    def _parse_scsi_page_83(self, buff,
                            select_supported_identifiers=False):
        """Parse SCSI Device Identification VPD (page 0x83 data).

        :param buff: a byte array containing the SCSI page 0x83 data.
        :param select_supported_identifiers: select identifiers supported
            by Windows, in the order of precedence.
        :returns: a list of identifiers represented as dicts, containing
                  SCSI Unique IDs.
        """
        identifiers = []

        buff_sz = len(buff)
        buff = (ctypes.c_ubyte * buff_sz)(*bytearray(buff))

        vpd_pg_struct_sz = ctypes.sizeof(DEVICE_ID_VPD_PAGE)

        if buff_sz < vpd_pg_struct_sz:
            reason = _('Invalid VPD page data.')
            raise exceptions.SCSIPageParsingError(page='0x83',
                                                  reason=reason)

        vpd_page = ctypes.cast(buff, PDEVICE_ID_VPD_PAGE).contents
        vpd_page_addr = ctypes.addressof(vpd_page)
        total_page_sz = vpd_page.PageLength + vpd_pg_struct_sz

        if vpd_page.PageCode != 0x83:
            reason = _('Unexpected page code: %s') % vpd_page.PageCode
            raise exceptions.SCSIPageParsingError(page='0x83',
                                                  reason=reason)
        if total_page_sz > buff_sz:
            reason = _('VPD page overflow.')
            raise exceptions.SCSIPageParsingError(page='0x83',
                                                  reason=reason)
        if not vpd_page.PageLength:
            LOG.info('Page 0x83 data does not contain any '
                     'identification descriptors.')
            return identifiers

        id_desc_offset = vpd_pg_struct_sz
        while id_desc_offset < total_page_sz:
            id_desc_addr = vpd_page_addr + id_desc_offset
            # Remaining buffer size
            id_desc_buff_sz = buff_sz - id_desc_offset

            identifier = self._parse_scsi_id_desc(id_desc_addr,
                                                  id_desc_buff_sz)
            identifiers.append(identifier)

            id_desc_offset += identifier['raw_id_desc_size']

        if select_supported_identifiers:
            identifiers = self._select_supported_scsi_identifiers(identifiers)

        return identifiers

    def _parse_scsi_id_desc(self, id_desc_addr, buff_sz):
        """Parse SCSI VPD identification descriptor."""
        id_desc_struct_sz = ctypes.sizeof(IDENTIFICATION_DESCRIPTOR)

        if buff_sz < id_desc_struct_sz:
            reason = _('Identifier descriptor overflow.')
            raise exceptions.SCSIIdDescriptorParsingError(reason=reason)

        id_desc = IDENTIFICATION_DESCRIPTOR.from_address(id_desc_addr)
        id_desc_sz = id_desc_struct_sz + id_desc.IdentifierLength
        identifier_addr = id_desc_addr + id_desc_struct_sz

        if id_desc_sz > buff_sz:
            reason = _('Identifier overflow.')
            raise exceptions.SCSIIdDescriptorParsingError(reason=reason)

        identifier = (ctypes.c_ubyte *
                      id_desc.IdentifierLength).from_address(
                          identifier_addr)
        raw_id = bytearray(identifier)

        if id_desc.CodeSet == SCSI_ID_CODE_SET_ASCII:
            parsed_id = bytes(
                bytearray(identifier)).decode('ascii').strip('\x00')
        else:
            parsed_id = _utils.byte_array_to_hex_str(raw_id)

        id_dict = {
            'code_set': id_desc.CodeSet,
            'protocol': (id_desc.ProtocolIdentifier
                         if id_desc.Piv else None),
            'type': id_desc.IdentifierType,
            'association': id_desc.Association,
            'raw_id': raw_id,
            'id': parsed_id,
            'raw_id_desc_size': id_desc_sz,
        }
        return id_dict

    def _select_supported_scsi_identifiers(self, identifiers):
        # This method will filter out unsupported SCSI identifiers,
        # also sorting them based on the order of precedence.
        selected_identifiers = []

        for id_type in constants.SUPPORTED_SCSI_UID_FORMATS:
            for identifier in identifiers:
                if identifier['type'] == id_type:
                    selected_identifiers.append(identifier)

        return selected_identifiers

    def get_new_disk_policy(self):
        # This policy is also known as the 'SAN policy', describing
        # how new disks will be handled.
        storsetting = self._conn_storage.MSFT_StorageSetting.Get()[1]
        return storsetting.NewDiskPolicy

    def set_new_disk_policy(self, policy):
        """Sets the new disk policy, also known as SAN policy.

        :param policy: an integer value, one of the DISK_POLICY_*
                       values defined in os_win.constants.
        """
        self._conn_storage.MSFT_StorageSetting.Set(
            NewDiskPolicy=policy)

    def set_disk_online(self, disk_number):
        disk = self._get_disk_by_number(disk_number)
        err_code = disk.Online()[1]
        if err_code:
            err_msg = (_("Failed to bring disk '%(disk_number)s' online. "
                         "Error code: %(err_code)s.") %
                       dict(disk_number=disk_number,
                            err_code=err_code))
            raise exceptions.DiskUpdateError(message=err_msg)

    def set_disk_offline(self, disk_number):
        disk = self._get_disk_by_number(disk_number)
        err_code = disk.Offline()[1]
        if err_code:
            err_msg = (_("Failed to bring disk '%(disk_number)s' offline. "
                         "Error code: %(err_code)s.") %
                       dict(disk_number=disk_number,
                            err_code=err_code))
            raise exceptions.DiskUpdateError(message=err_msg)

    def set_disk_readonly_status(self, disk_number, read_only):
        disk = self._get_disk_by_number(disk_number)
        err_code = disk.SetAttributes(IsReadOnly=bool(read_only))[1]
        if err_code:
            err_msg = (_("Failed to set disk '%(disk_number)s' read-only "
                         "status to '%(read_only)s'. "
                         "Error code: %(err_code)s.") %
                       dict(disk_number=disk_number,
                            err_code=err_code,
                            read_only=bool(read_only)))
            raise exceptions.DiskUpdateError(message=err_msg)
