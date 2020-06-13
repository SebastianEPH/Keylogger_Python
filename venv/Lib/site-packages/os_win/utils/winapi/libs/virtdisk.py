# Copyright 2017 Cloudbase Solutions Srl
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

import ctypes

from os_win.utils.winapi import wintypes

lib_handle = None


class VIRTUAL_STORAGE_TYPE(ctypes.Structure):
    _fields_ = [
        ('DeviceId', wintypes.DWORD),
        ('VendorId', wintypes.GUID)
    ]


PVIRTUAL_STORAGE_TYPE = ctypes.POINTER(VIRTUAL_STORAGE_TYPE)


class _RESIZE_VIRTUAL_DISK_PARAMETERS_V1(ctypes.Structure):
    _fields_ = [
        ('NewSize', wintypes.ULONGLONG)
    ]


# Only V1 is used, we avoid defining a union.
class RESIZE_VIRTUAL_DISK_PARAMETERS(ctypes.Structure):
    _fields_ = [
        ('Version', wintypes.DWORD),
        ('Version1', _RESIZE_VIRTUAL_DISK_PARAMETERS_V1)
    ]


PRESIZE_VIRTUAL_DISK_PARAMETERS = ctypes.POINTER(
    RESIZE_VIRTUAL_DISK_PARAMETERS)


class _OPEN_VIRTUAL_DISK_PARAMETERS_V1(ctypes.Structure):
    _fields_ = [
        ('RWDepth', wintypes.ULONG),
    ]


class _OPEN_VIRTUAL_DISK_PARAMETERS_V2(ctypes.Structure):
    _fields_ = [
        ('GetInfoOnly', wintypes.BOOL),
        ('ReadOnly', wintypes.BOOL),
        ('ResiliencyGuid', wintypes.GUID)
    ]


class _OPEN_VIRTUAL_DISK_PARAMETERS_U(ctypes.Union):
    _fields_ = [
        ('Version1', _OPEN_VIRTUAL_DISK_PARAMETERS_V1),
        ('Version2', _OPEN_VIRTUAL_DISK_PARAMETERS_V2)
    ]


class OPEN_VIRTUAL_DISK_PARAMETERS(ctypes.Structure):
    _anonymous_ = ['_parameters']
    _fields_ = [
        ('Version', wintypes.DWORD),
        ('_parameters', _OPEN_VIRTUAL_DISK_PARAMETERS_U)
    ]


POPEN_VIRTUAL_DISK_PARAMETERS = ctypes.POINTER(
    OPEN_VIRTUAL_DISK_PARAMETERS)


class _MERGE_VIRTUAL_DISK_PARAMETERS_V1(ctypes.Structure):
    _fields_ = [
        ('MergeDepth', wintypes.ULONG)
    ]


# Only V1 is used, we avoid defining a union.
class MERGE_VIRTUAL_DISK_PARAMETERS(ctypes.Structure):
    _fields_ = [
        ('Version', wintypes.DWORD),
        ('Version1', _MERGE_VIRTUAL_DISK_PARAMETERS_V1)
    ]


PMERGE_VIRTUAL_DISK_PARAMETERS = ctypes.POINTER(
    MERGE_VIRTUAL_DISK_PARAMETERS)


class _CREATE_VIRTUAL_DISK_PARAMETERS_V2(ctypes.Structure):
    _fields_ = [
        ('UniqueId', wintypes.GUID),
        ('MaximumSize', wintypes.ULONGLONG),
        ('BlockSizeInBytes', wintypes.ULONG),
        ('SectorSizeInBytes', wintypes.ULONG),
        ('PhysicalSectorSizeInBytes', wintypes.ULONG),
        ('ParentPath', wintypes.LPCWSTR),
        ('SourcePath', wintypes.LPCWSTR),
        ('OpenFlags', wintypes.DWORD),
        ('ParentVirtualStorageType', VIRTUAL_STORAGE_TYPE),
        ('SourceVirtualStorageType', VIRTUAL_STORAGE_TYPE),
        ('ResiliencyGuid', wintypes.GUID)
    ]


# Only V2 is used, we avoid defining a union.
class CREATE_VIRTUAL_DISK_PARAMETERS(ctypes.Structure):
    _fields_ = [
        ('Version', wintypes.DWORD),
        ('Version2', _CREATE_VIRTUAL_DISK_PARAMETERS_V2)
    ]


PCREATE_VIRTUAL_DISK_PARAMETERS = ctypes.POINTER(
    CREATE_VIRTUAL_DISK_PARAMETERS)


class _VHD_INFO_SIZE(ctypes.Structure):
    _fields_ = [
        ("VirtualSize", wintypes.ULARGE_INTEGER),
        ("PhysicalSize", wintypes.ULARGE_INTEGER),
        ("BlockSize", wintypes.ULONG),
        ("SectorSize", wintypes.ULONG)
    ]


class _VHD_INFO_PARENT_LOCATION(ctypes.Structure):
    _fields_ = [
        ('ParentResolved', wintypes.BOOL),
        ('ParentPath', wintypes.WCHAR * 512)
    ]


class _VHD_INFO_PHYSICAL_DISK(ctypes.Structure):
    _fields_ = [
        ("LogicalSectorSize", wintypes.ULONG),
        ("PhysicalSectorSize", wintypes.ULONG),
        ("IsRemote", wintypes.BOOL)
    ]


class _VHD_INFO(ctypes.Union):
    _fields_ = [
        ("Size", _VHD_INFO_SIZE),
        ("Identifier", wintypes.GUID),
        ("ParentLocation", _VHD_INFO_PARENT_LOCATION),
        ("ParentIdentifier", wintypes.GUID),
        ("ParentTimestamp", wintypes.ULONG),
        ("VirtualStorageType", VIRTUAL_STORAGE_TYPE),
        ("ProviderSubtype", wintypes.ULONG),
        ("Is4kAligned", wintypes.BOOL),
        ("IsLoaded", wintypes.BOOL),
        ("PhysicalDisk", _VHD_INFO_PHYSICAL_DISK),
        ("VhdPhysicalSectorSize", wintypes.ULONG),
        ("SmallestSafeVirtualSize", wintypes.ULARGE_INTEGER),
        ("FragmentationPercentage", wintypes.ULONG)
    ]


class GET_VIRTUAL_DISK_INFO(ctypes.Structure):
    _anonymous_ = ['_vhdinfo']
    _fields_ = [
        ("Version", wintypes.UINT),
        ("_vhdinfo", _VHD_INFO)
    ]


PGET_VIRTUAL_DISK_INFO = ctypes.POINTER(GET_VIRTUAL_DISK_INFO)


# Only this version is used, we avoid defining a union.
class SET_VIRTUAL_DISK_INFO(ctypes.Structure):
    _fields_ = [
        ('Version', wintypes.DWORD),
        ('ParentFilePath', wintypes.LPCWSTR)
    ]


PSET_VIRTUAL_DISK_INFO = ctypes.POINTER(SET_VIRTUAL_DISK_INFO)


def register():
    global lib_handle
    lib_handle = ctypes.windll.virtdisk

    lib_handle.CreateVirtualDisk.argtypes = [
        PVIRTUAL_STORAGE_TYPE,
        wintypes.LPCWSTR,
        wintypes.INT,
        wintypes.PVOID,
        wintypes.INT,
        wintypes.ULONG,
        PCREATE_VIRTUAL_DISK_PARAMETERS,
        wintypes.LPOVERLAPPED,
        wintypes.PHANDLE
    ]
    lib_handle.CreateVirtualDisk.restype = wintypes.DWORD

    lib_handle.GetVirtualDiskInformation.argtypes = [
        wintypes.HANDLE,
        wintypes.PULONG,
        PGET_VIRTUAL_DISK_INFO,
        wintypes.PULONG
    ]
    lib_handle.GetVirtualDiskInformation.restype = wintypes.DWORD

    lib_handle.MergeVirtualDisk.argtypes = [
        wintypes.HANDLE,
        wintypes.INT,
        PMERGE_VIRTUAL_DISK_PARAMETERS,
        wintypes.LPOVERLAPPED
    ]
    lib_handle.MergeVirtualDisk.restype = wintypes.DWORD

    lib_handle.OpenVirtualDisk.argtypes = [
        PVIRTUAL_STORAGE_TYPE,
        wintypes.LPCWSTR,
        wintypes.INT,
        wintypes.INT,
        POPEN_VIRTUAL_DISK_PARAMETERS,
        wintypes.PHANDLE
    ]
    lib_handle.OpenVirtualDisk.restype = wintypes.DWORD

    lib_handle.ResizeVirtualDisk.argtypes = [
        wintypes.HANDLE,
        wintypes.INT,
        PRESIZE_VIRTUAL_DISK_PARAMETERS,
        wintypes.LPOVERLAPPED
    ]
    lib_handle.ResizeVirtualDisk.restype = wintypes.DWORD

    lib_handle.SetVirtualDiskInformation.argtypes = [
        wintypes.HANDLE,
        PSET_VIRTUAL_DISK_INFO
    ]
    lib_handle.SetVirtualDiskInformation.restype = wintypes.DWORD

    lib_handle.AttachVirtualDisk.argtypes = [
        wintypes.HANDLE,
        wintypes.PVOID,
        wintypes.INT,
        wintypes.ULONG,
        wintypes.PVOID,
        wintypes.LPOVERLAPPED
    ]
    lib_handle.AttachVirtualDisk.restype = wintypes.DWORD

    lib_handle.DetachVirtualDisk.argtypes = [
        wintypes.HANDLE,
        wintypes.INT,
        wintypes.ULONG
    ]
    lib_handle.DetachVirtualDisk.restype = wintypes.DWORD

    lib_handle.GetVirtualDiskPhysicalPath.argtypes = [
        wintypes.HANDLE,
        wintypes.PULONG,
        wintypes.PWSTR
    ]
    lib_handle.GetVirtualDiskPhysicalPath.restype = wintypes.DWORD
