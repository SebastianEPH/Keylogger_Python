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
Utility class for VHD related operations.

Official VHD format specs can be retrieved at:
http://technet.microsoft.com/en-us/library/bb676673.aspx
See "Download the Specifications Without Registering"

Official VHDX format specs can be retrieved at:
http://www.microsoft.com/en-us/download/details.aspx?id=34750
"""
import ctypes
import os
import struct

from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import units

from os_win._i18n import _
from os_win import constants
from os_win import exceptions
from os_win.utils.storage import diskutils
from os_win.utils import win32utils
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi import libs as w_lib
from os_win.utils.winapi.libs import virtdisk as vdisk_struct
from os_win.utils.winapi import wintypes

kernel32 = w_lib.get_shared_lib_handle(w_lib.KERNEL32)
virtdisk = w_lib.get_shared_lib_handle(w_lib.VIRTDISK)

LOG = logging.getLogger(__name__)


VHD_SIGNATURE = b'conectix'
VHDX_SIGNATURE = b'vhdxfile'

DEVICE_ID_MAP = {
    constants.DISK_FORMAT_VHD: w_const.VIRTUAL_STORAGE_TYPE_DEVICE_VHD,
    constants.DISK_FORMAT_VHDX: w_const.VIRTUAL_STORAGE_TYPE_DEVICE_VHDX,
}

VHD_HEADER_SIZE_FIX = 512
VHD_BAT_ENTRY_SIZE = 4
VHD_DYNAMIC_DISK_HEADER_SIZE = 1024
VHD_HEADER_SIZE_DYNAMIC = 512
VHD_FOOTER_SIZE_DYNAMIC = 512

VHDX_BAT_ENTRY_SIZE = 8
VHDX_HEADER_OFFSETS = [64 * units.Ki, 128 * units.Ki]
VHDX_HEADER_SECTION_SIZE = units.Mi
VHDX_LOG_LENGTH_OFFSET = 68
VHDX_METADATA_SIZE_OFFSET = 64
VHDX_REGION_TABLE_OFFSET = 192 * units.Ki
VHDX_BS_METADATA_ENTRY_OFFSET = 48

VIRTUAL_DISK_DEFAULT_SECTOR_SIZE = 0x200
VIRTUAL_DISK_DEFAULT_PHYS_SECTOR_SIZE = 0x200

CREATE_VIRTUAL_DISK_FLAGS = {
    constants.VHD_TYPE_FIXED:
        w_const.CREATE_VIRTUAL_DISK_FLAG_FULL_PHYSICAL_ALLOCATION,
}


class VHDUtils(object):
    def __init__(self):
        self._win32_utils = win32utils.Win32Utils()
        self._disk_utils = diskutils.DiskUtils()

        self._vhd_info_members = {
            w_const.GET_VIRTUAL_DISK_INFO_SIZE: 'Size',
            w_const.GET_VIRTUAL_DISK_INFO_PARENT_LOCATION:
                'ParentLocation',
            w_const.GET_VIRTUAL_DISK_INFO_VIRTUAL_STORAGE_TYPE:
                'VirtualStorageType',
            w_const.GET_VIRTUAL_DISK_INFO_PROVIDER_SUBTYPE:
                'ProviderSubtype',
            w_const.GET_VIRTUAL_DISK_INFO_IS_LOADED: 'IsLoaded'}

        # Describes the way error handling is performed
        # for virtdisk.dll functions.
        self._virtdisk_run_args = dict(
            failure_exc=exceptions.VHDWin32APIException,
            error_on_nonzero_ret_val=True,
            ret_val_is_err_code=True)

    def _run_and_check_output(self, *args, **kwargs):
        cleanup_handle = kwargs.pop('cleanup_handle', None)
        kwargs.update(self._virtdisk_run_args)

        try:
            return self._win32_utils.run_and_check_output(*args, **kwargs)
        finally:
            if cleanup_handle:
                self._win32_utils.close_handle(cleanup_handle)

    def _open(self, vhd_path,
              open_flag=0,
              open_access_mask=w_const.VIRTUAL_DISK_ACCESS_ALL,
              open_params=None):
        device_id = self._get_vhd_device_id(vhd_path)

        vst = vdisk_struct.VIRTUAL_STORAGE_TYPE(
            DeviceId=device_id,
            VendorId=w_const.VIRTUAL_STORAGE_TYPE_VENDOR_MICROSOFT)
        handle = wintypes.HANDLE()

        self._run_and_check_output(virtdisk.OpenVirtualDisk,
                                   ctypes.byref(vst),
                                   ctypes.c_wchar_p(vhd_path),
                                   open_access_mask,
                                   open_flag,
                                   open_params,
                                   ctypes.byref(handle))
        return handle

    def close(self, handle):
        self._win32_utils.close_handle(handle)

    def create_vhd(self, new_vhd_path, new_vhd_type, src_path=None,
                   max_internal_size=0, parent_path=None):
        new_device_id = self._get_vhd_device_id(new_vhd_path)

        vst = vdisk_struct.VIRTUAL_STORAGE_TYPE(
            DeviceId=new_device_id,
            VendorId=w_const.VIRTUAL_STORAGE_TYPE_VENDOR_MICROSOFT)

        params = vdisk_struct.CREATE_VIRTUAL_DISK_PARAMETERS()
        params.Version = w_const.CREATE_VIRTUAL_DISK_VERSION_2
        params.Version2.MaximumSize = max_internal_size
        params.Version2.ParentPath = parent_path
        params.Version2.SourcePath = src_path
        params.Version2.PhysicalSectorSizeInBytes = (
            VIRTUAL_DISK_DEFAULT_PHYS_SECTOR_SIZE)
        params.Version2.BlockSizeInBytes = (
            w_const.CREATE_VHD_PARAMS_DEFAULT_BLOCK_SIZE)
        params.Version2.SectorSizeInBytes = (
            VIRTUAL_DISK_DEFAULT_SECTOR_SIZE)

        handle = wintypes.HANDLE()
        create_virtual_disk_flag = CREATE_VIRTUAL_DISK_FLAGS.get(
            new_vhd_type, 0)

        self._run_and_check_output(virtdisk.CreateVirtualDisk,
                                   ctypes.byref(vst),
                                   ctypes.c_wchar_p(new_vhd_path),
                                   0,
                                   None,
                                   create_virtual_disk_flag,
                                   0,
                                   ctypes.byref(params),
                                   None,
                                   ctypes.byref(handle),
                                   cleanup_handle=handle)

    def create_dynamic_vhd(self, path, max_internal_size):
        self.create_vhd(path,
                        constants.VHD_TYPE_DYNAMIC,
                        max_internal_size=max_internal_size)

    def create_differencing_vhd(self, path, parent_path):
        self.create_vhd(path,
                        constants.VHD_TYPE_DIFFERENCING,
                        parent_path=parent_path)

    def convert_vhd(self, src, dest,
                    vhd_type=constants.VHD_TYPE_DYNAMIC):
        self.create_vhd(dest, vhd_type, src_path=src)

    def get_vhd_format(self, vhd_path):
        vhd_format = os.path.splitext(vhd_path)[1][1:].upper()
        device_id = DEVICE_ID_MAP.get(vhd_format)
        # If the disk format is not recognised by extension,
        # we attempt to retrieve it by seeking the signature.
        if not device_id and os.path.exists(vhd_path):
            vhd_format = self._get_vhd_format_by_signature(vhd_path)

        if not vhd_format:
            raise exceptions.VHDException(
                _("Could not retrieve VHD format: %s") % vhd_path)

        return vhd_format

    def _get_vhd_device_id(self, vhd_path):
        vhd_format = self.get_vhd_format(vhd_path)
        return DEVICE_ID_MAP.get(vhd_format)

    def _get_vhd_format_by_signature(self, vhd_path):
        with open(vhd_path, 'rb') as f:
            # print f.read()
            # Read header
            if f.read(8) == VHDX_SIGNATURE:
                return constants.DISK_FORMAT_VHDX

            # Read footer
            f.seek(0, 2)
            file_size = f.tell()
            if file_size >= 512:
                f.seek(-512, 2)
                if f.read(8) == VHD_SIGNATURE:
                    return constants.DISK_FORMAT_VHD

    def get_vhd_info(self, vhd_path, info_members=None,
                     open_parents=False):
        """Returns a dict containing VHD image information.

        :param info_members: A list of information members to be retrieved.

        Default retrieved members and according dict keys:
            GET_VIRTUAL_DISK_INFO_SIZE: 1
                - VirtualSize
                - PhysicalSize
                - BlockSize
                - SectorSize
            GET_VIRTUAL_DISK_INFO_PARENT_LOCATION: 3
                - ParentResolved
                - ParentPath (ParentLocationBuffer)
            GET_VIRTUAL_DISK_INFO_VIRTUAL_STORAGE_TYPE: 6
                - DeviceId (format)
                - VendorId
            GET_VIRTUAL_DISK_INFO_PROVIDER_SUBTYPE:
                - ProviderSubtype
        """
        vhd_info = {}
        info_members = info_members or self._vhd_info_members

        open_flag = (w_const.OPEN_VIRTUAL_DISK_FLAG_NO_PARENTS
                     if not open_parents else 0)
        open_access_mask = (w_const.VIRTUAL_DISK_ACCESS_GET_INFO |
                            w_const.VIRTUAL_DISK_ACCESS_DETACH)
        handle = self._open(
            vhd_path,
            open_flag=open_flag,
            open_access_mask=open_access_mask)

        try:
            for member in info_members:
                info = self._get_vhd_info_member(handle, member)
                vhd_info.update(info)
        finally:
            self._win32_utils.close_handle(handle)

        return vhd_info

    def _get_vhd_info_member(self, vhd_file, info_member):
        virt_disk_info = vdisk_struct.GET_VIRTUAL_DISK_INFO()
        virt_disk_info.Version = ctypes.c_uint(info_member)

        infoSize = ctypes.sizeof(virt_disk_info)

        virtdisk.GetVirtualDiskInformation.restype = wintypes.DWORD

        # Note(lpetrut): If the vhd has no parent image, this will
        # return an error. No need to raise an exception in this case.
        ignored_error_codes = []
        if info_member == w_const.GET_VIRTUAL_DISK_INFO_PARENT_LOCATION:
            ignored_error_codes.append(w_const.ERROR_VHD_INVALID_TYPE)

        self._run_and_check_output(virtdisk.GetVirtualDiskInformation,
                                   vhd_file,
                                   ctypes.byref(ctypes.c_ulong(infoSize)),
                                   ctypes.byref(virt_disk_info),
                                   None,
                                   ignored_error_codes=ignored_error_codes)

        return self._parse_vhd_info(virt_disk_info, info_member)

    def _parse_vhd_info(self, virt_disk_info, info_member):
        vhd_info = {}
        vhd_info_member = self._vhd_info_members[info_member]
        info = getattr(virt_disk_info, vhd_info_member)

        if hasattr(info, '_fields_'):
            for field in info._fields_:
                vhd_info[field[0]] = getattr(info, field[0])
        else:
            vhd_info[vhd_info_member] = info

        return vhd_info

    def get_vhd_size(self, vhd_path):
        """Return vhd size.

        Returns a dict containing the virtual size, physical size,
        block size and sector size of the vhd.
        """
        size = self.get_vhd_info(vhd_path,
                                 [w_const.GET_VIRTUAL_DISK_INFO_SIZE])
        return size

    def get_vhd_parent_path(self, vhd_path):
        vhd_info = self.get_vhd_info(
            vhd_path,
            [w_const.GET_VIRTUAL_DISK_INFO_PARENT_LOCATION])
        parent_path = vhd_info['ParentPath']

        return parent_path if parent_path else None

    def get_vhd_type(self, vhd_path):
        vhd_info = self.get_vhd_info(
            vhd_path,
            [w_const.GET_VIRTUAL_DISK_INFO_PROVIDER_SUBTYPE])
        return vhd_info['ProviderSubtype']

    def merge_vhd(self, vhd_path, delete_merged_image=True):
        """Merges a VHD/x image into the immediate next parent image."""
        open_params = vdisk_struct.OPEN_VIRTUAL_DISK_PARAMETERS()
        open_params.Version = w_const.OPEN_VIRTUAL_DISK_VERSION_1
        open_params.Version1.RWDepth = 2

        handle = self._open(vhd_path,
                            open_params=ctypes.byref(open_params))

        params = vdisk_struct.MERGE_VIRTUAL_DISK_PARAMETERS()
        params.Version = w_const.MERGE_VIRTUAL_DISK_VERSION_1
        params.Version1.MergeDepth = 1

        self._run_and_check_output(
            virtdisk.MergeVirtualDisk,
            handle,
            0,
            ctypes.byref(params),
            None,
            cleanup_handle=handle)

        if delete_merged_image:
            os.remove(vhd_path)

    def reconnect_parent_vhd(self, child_path, parent_path):
        open_params = vdisk_struct.OPEN_VIRTUAL_DISK_PARAMETERS()
        open_params.Version = w_const.OPEN_VIRTUAL_DISK_VERSION_2
        open_params.Version2.GetInfoOnly = False

        handle = self._open(
            child_path,
            open_flag=w_const.OPEN_VIRTUAL_DISK_FLAG_NO_PARENTS,
            open_access_mask=0,
            open_params=ctypes.byref(open_params))

        params = vdisk_struct.SET_VIRTUAL_DISK_INFO()
        params.Version = w_const.SET_VIRTUAL_DISK_INFO_PARENT_PATH
        params.ParentFilePath = parent_path

        self._run_and_check_output(virtdisk.SetVirtualDiskInformation,
                                   handle,
                                   ctypes.byref(params),
                                   cleanup_handle=handle)

    def resize_vhd(self, vhd_path, new_max_size, is_file_max_size=True,
                   validate_new_size=True):
        if is_file_max_size:
            new_internal_max_size = self.get_internal_vhd_size_by_file_size(
                vhd_path, new_max_size)
        else:
            new_internal_max_size = new_max_size

        if validate_new_size:
            if not self._check_resize_needed(vhd_path, new_internal_max_size):
                return

        self._resize_vhd(vhd_path, new_internal_max_size)

    def _check_resize_needed(self, vhd_path, new_size):
        curr_size = self.get_vhd_size(vhd_path)['VirtualSize']
        if curr_size > new_size:
            err_msg = _("Cannot resize image %(vhd_path)s "
                        "to a smaller size. "
                        "Image virtual size: %(curr_size)s, "
                        "Requested virtual size: %(new_size)s")
            raise exceptions.VHDException(
                err_msg % dict(vhd_path=vhd_path,
                               curr_size=curr_size,
                               new_size=new_size))
        elif curr_size == new_size:
            LOG.debug("Skipping resizing %(vhd_path)s to %(new_size)s"
                      "as it already has the requested size.",
                      dict(vhd_path=vhd_path,
                           new_size=new_size))
            return False
        return True

    def _resize_vhd(self, vhd_path, new_max_size):
        handle = self._open(vhd_path)

        params = vdisk_struct.RESIZE_VIRTUAL_DISK_PARAMETERS()
        params.Version = w_const.RESIZE_VIRTUAL_DISK_VERSION_1
        params.Version1.NewSize = new_max_size

        self._run_and_check_output(
            virtdisk.ResizeVirtualDisk,
            handle,
            0,
            ctypes.byref(params),
            None,
            cleanup_handle=handle)

    def get_internal_vhd_size_by_file_size(self, vhd_path,
                                           new_vhd_file_size):
        """Get internal size of a VHD according to new VHD file size."""
        vhd_info = self.get_vhd_info(vhd_path)
        vhd_type = vhd_info['ProviderSubtype']
        vhd_dev_id = vhd_info['DeviceId']

        if vhd_type == constants.VHD_TYPE_DIFFERENCING:
            vhd_parent = vhd_info['ParentPath']
            return self.get_internal_vhd_size_by_file_size(
                vhd_parent, new_vhd_file_size)

        if vhd_dev_id == w_const.VIRTUAL_STORAGE_TYPE_DEVICE_VHD:
            func = self._get_internal_vhd_size_by_file_size
        else:
            func = self._get_internal_vhdx_size_by_file_size
        return func(vhd_path, new_vhd_file_size, vhd_info)

    def _get_internal_vhd_size_by_file_size(self, vhd_path,
                                            new_vhd_file_size,
                                            vhd_info):
        """Fixed VHD size = Data Block size + 512 bytes

           | Dynamic_VHD_size = Dynamic Disk Header
           |                  + Copy of hard disk footer
           |                  + Hard Disk Footer
           |                  + Data Block
           |                  + BAT
           | Dynamic Disk header fields
           |     Copy of hard disk footer (512 bytes)
           |     Dynamic Disk Header (1024 bytes)
           |     BAT (Block Allocation table)
           |     Data Block 1
           |     Data Block 2
           |     Data Block n
           |     Hard Disk Footer (512 bytes)
           | Default block size is 2M
           | BAT entry size is 4byte
        """

        vhd_type = vhd_info['ProviderSubtype']
        if vhd_type == constants.VHD_TYPE_FIXED:
            vhd_header_size = VHD_HEADER_SIZE_FIX
            return new_vhd_file_size - vhd_header_size
        else:
            bs = vhd_info['BlockSize']
            bes = VHD_BAT_ENTRY_SIZE
            ddhs = VHD_DYNAMIC_DISK_HEADER_SIZE
            hs = VHD_HEADER_SIZE_DYNAMIC
            fs = VHD_FOOTER_SIZE_DYNAMIC

            max_internal_size = (new_vhd_file_size -
                                 (hs + ddhs + fs)) * bs // (bes + bs)
            return max_internal_size

    def _get_internal_vhdx_size_by_file_size(self, vhd_path,
                                             new_vhd_file_size,
                                             vhd_info):
        """VHDX Size:

        Header (1MB) + Log + Metadata Region + BAT + Payload Blocks

        The chunk size is the maximum number of bytes described by a SB
        block.

        Chunk size = 2^{23} * SectorSize

        :param str vhd_path: VHD file path
        :param new_vhd_file_size: Size of the new VHD file.
        :return: Internal VHD size according to new VHD file size.
        """

        try:
            with open(vhd_path, 'rb') as f:
                hs = VHDX_HEADER_SECTION_SIZE
                bes = VHDX_BAT_ENTRY_SIZE

                lss = vhd_info['SectorSize']
                bs = self._get_vhdx_block_size(f)
                ls = self._get_vhdx_log_size(f)
                ms = self._get_vhdx_metadata_size_and_offset(f)[0]

                chunk_ratio = (1 << 23) * lss // bs
                size = new_vhd_file_size

                max_internal_size = (bs * chunk_ratio * (size - hs -
                                     ls - ms - bes - bes // chunk_ratio) //
                                     (bs *
                                     chunk_ratio + bes * chunk_ratio + bes))

                return max_internal_size - (max_internal_size % bs)
        except IOError as ex:
            raise exceptions.VHDException(
                _("Unable to obtain internal size from VHDX: "
                  "%(vhd_path)s. Exception: %(ex)s") %
                {"vhd_path": vhd_path, "ex": ex})

    def _get_vhdx_current_header_offset(self, vhdx_file):
        sequence_numbers = []
        for offset in VHDX_HEADER_OFFSETS:
            vhdx_file.seek(offset + 8)
            sequence_numbers.append(struct.unpack('<Q',
                                    vhdx_file.read(8))[0])
        current_header = sequence_numbers.index(max(sequence_numbers))
        return VHDX_HEADER_OFFSETS[current_header]

    def _get_vhdx_log_size(self, vhdx_file):
        current_header_offset = self._get_vhdx_current_header_offset(vhdx_file)
        offset = current_header_offset + VHDX_LOG_LENGTH_OFFSET
        vhdx_file.seek(offset)
        log_size = struct.unpack('<I', vhdx_file.read(4))[0]
        return log_size

    def _get_vhdx_metadata_size_and_offset(self, vhdx_file):
        offset = VHDX_METADATA_SIZE_OFFSET + VHDX_REGION_TABLE_OFFSET
        vhdx_file.seek(offset)
        metadata_offset = struct.unpack('<Q', vhdx_file.read(8))[0]
        metadata_size = struct.unpack('<I', vhdx_file.read(4))[0]
        return metadata_size, metadata_offset

    def _get_vhdx_block_size(self, vhdx_file):
        metadata_offset = self._get_vhdx_metadata_size_and_offset(vhdx_file)[1]
        offset = metadata_offset + VHDX_BS_METADATA_ENTRY_OFFSET
        vhdx_file.seek(offset)
        file_parameter_offset = struct.unpack('<I', vhdx_file.read(4))[0]

        vhdx_file.seek(file_parameter_offset + metadata_offset)
        block_size = struct.unpack('<I', vhdx_file.read(4))[0]
        return block_size

    def get_best_supported_vhd_format(self):
        return constants.DISK_FORMAT_VHDX

    def flatten_vhd(self, vhd_path):
        base_path, ext = os.path.splitext(vhd_path)
        tmp_path = base_path + '.tmp' + ext
        self.convert_vhd(vhd_path, tmp_path)

        os.unlink(vhd_path)
        os.rename(tmp_path, vhd_path)

    def attach_virtual_disk(self, vhd_path, read_only=True,
                            detach_on_handle_close=False):
        """Attach a virtual disk image.

        :param vhd_path: the path of the image to attach
        :param read_only: (bool) attach the image in read only mode
        :parma detach_on_handle_close: if set, the image will automatically be
                                       detached when the last image handle is
                                       closed.
        :returns: if 'detach_on_handle_close' is set, it returns a virtual
                  disk image handle that may be closed using the
                  'close' method of this class.
        """
        open_access_mask = (w_const.VIRTUAL_DISK_ACCESS_ATTACH_RO
                            if read_only
                            else w_const.VIRTUAL_DISK_ACCESS_ATTACH_RW)
        attach_virtual_disk_flag = 0
        if not detach_on_handle_close:
            attach_virtual_disk_flag |= (
                w_const.ATTACH_VIRTUAL_DISK_FLAG_PERMANENT_LIFETIME)
        if read_only:
            attach_virtual_disk_flag |= (
                w_const.ATTACH_VIRTUAL_DISK_FLAG_READ_ONLY)

        handle = self._open(
            vhd_path,
            open_access_mask=open_access_mask)

        self._run_and_check_output(
            virtdisk.AttachVirtualDisk,
            handle,
            None,  # security descriptor
            attach_virtual_disk_flag,
            0,  # provider specific flags
            None,  # attach parameters
            None,  # overlapped structure
            cleanup_handle=handle if not detach_on_handle_close else None)

        if detach_on_handle_close:
            return handle

    def detach_virtual_disk(self, vhd_path):
        if not os.path.exists(vhd_path):
            LOG.debug("Image %s could not be found. Skipping detach.",
                      vhd_path)
            return

        open_access_mask = w_const.VIRTUAL_DISK_ACCESS_DETACH

        try:
            handle = self._open(vhd_path, open_access_mask=open_access_mask)
        except Exception as exc:
            # File locks from different hosts may prevent us from opening this
            # image, which may not even be used by the local host.
            #
            # Note that listing disks can be a time consuming operation, for
            # which reason we'll try to avoid it by default.
            with excutils.save_and_reraise_exception() as ctxt:
                if not self.is_virtual_disk_file_attached(vhd_path):
                    LOG.info("The following image is not currently attached "
                             "to the local host: '%(vhd_path)s'. Ignoring "
                             "exception encountered while attempting to "
                             "open and disconnect it: %(exc)s",
                             dict(vhd_path=vhd_path, exc=exc))
                    ctxt.reraise = False
                    return

        ret_val = self._run_and_check_output(
            virtdisk.DetachVirtualDisk,
            handle,
            0,  # detach flags
            0,  # provider specific flags
            ignored_error_codes=[w_const.ERROR_NOT_READY],
            cleanup_handle=handle)

        if ret_val == w_const.ERROR_NOT_READY:
            LOG.debug("Image %s was not attached.", vhd_path)

    def get_virtual_disk_physical_path(self, vhd_path):
        """Returns the physical disk path for an attached disk image.

        :param vhd_path: an attached disk image path.
        :returns: the mount path of the specified image, in the form of
                  \\.\PhysicalDriveX.
        """

        open_flag = w_const.OPEN_VIRTUAL_DISK_FLAG_NO_PARENTS
        open_access_mask = (w_const.VIRTUAL_DISK_ACCESS_GET_INFO |
                            w_const.VIRTUAL_DISK_ACCESS_DETACH)
        handle = self._open(
            vhd_path,
            open_flag=open_flag,
            open_access_mask=open_access_mask)

        disk_path = (ctypes.c_wchar * w_const.MAX_PATH)()
        disk_path_sz = wintypes.ULONG(w_const.MAX_PATH)
        self._run_and_check_output(
            virtdisk.GetVirtualDiskPhysicalPath,
            handle,
            ctypes.byref(disk_path_sz),
            disk_path,
            cleanup_handle=handle)

        return disk_path.value

    def is_virtual_disk_file_attached(self, vhd_path):
        if not os.path.exists(vhd_path):
            LOG.debug("Image %s could not be found.", vhd_path)
            return False

        try:
            vhd_info = self.get_vhd_info(
                vhd_path,
                [w_const.GET_VIRTUAL_DISK_INFO_IS_LOADED])
            return bool(vhd_info['IsLoaded'])
        except Exception as exc:
            # We may fail to open the image due to file locks. We'll try
            # an alternative, much slower approach.
            LOG.info("Could not get virtual disk information: %(vhd_path)s. "
                     "Trying an alternative approach. Error: %(exc)s",
                     dict(vhd_path=vhd_path,
                          exc=exc))
            return self._disk_utils.is_virtual_disk_file_attached(vhd_path)
