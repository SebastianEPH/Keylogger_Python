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

import ctypes

import os_win.conf
from os_win.utils.winapi import wintypes

CONF = os_win.conf.CONF

lib_handle = None

HBA_STATUS = ctypes.c_uint32
HBA_HANDLE = ctypes.c_uint32
HBA_PortType = ctypes.c_uint32
HBA_PortSpeed = ctypes.c_uint32
HBA_PortState = ctypes.c_uint32
HBA_COS = ctypes.c_uint32
HBA_FC4Types = ctypes.c_uint32 * 32
HBA_FCPBindingType = wintypes.INT


class HBA_WWN(ctypes.Structure):
    _fields_ = [('wwn', ctypes.c_ubyte * 8)]


class HBA_PortAttributes(ctypes.Structure):
    _fields_ = [('NodeWWN', HBA_WWN),
                ('PortWWN', HBA_WWN),
                ('PortFcId', ctypes.c_uint32),
                ('PortType', HBA_PortType),
                ('PortState', HBA_PortState),
                ('PortSupportedClassofService', HBA_COS),
                ('PortSupportedFc4Types', HBA_FC4Types),
                ('PortSymbolicName', wintypes.CHAR * 256),
                ('OSDeviceName', wintypes.CHAR * 256),
                ('PortSupportedSpeed', HBA_PortSpeed),
                ('PortSpeed', HBA_PortSpeed),
                ('PortMaxFrameSize', ctypes.c_uint32),
                ('FabricName', HBA_WWN),
                ('NumberOfDiscoveredPorts', ctypes.c_uint32)]


class HBA_FCPId(ctypes.Structure):
    _fields_ = [('FcId', ctypes.c_uint32),
                ('NodeWWN', HBA_WWN),
                ('PortWWN', HBA_WWN),
                ('FcpLun', ctypes.c_uint64)]


class HBA_ScsiId(ctypes.Structure):
    _fields_ = [('OSDeviceName', wintypes.CHAR * 256),
                ('ScsiBusNumber', ctypes.c_uint32),
                ('ScsiTargetNumber', ctypes.c_uint32),
                ('ScsiOSLun', ctypes.c_uint32)]


class HBA_FCPScsiEntry(ctypes.Structure):
    _fields_ = [('ScsiId', HBA_ScsiId),
                ('FcpId', HBA_FCPId)]


def get_target_mapping_struct(entry_count=0):
    class HBA_FCPTargetMapping(ctypes.Structure):
        _fields_ = [('NumberOfEntries', ctypes.c_uint32),
                    ('Entries', HBA_FCPScsiEntry * entry_count)]

        def __init__(self, entry_count):
            self.NumberOfEntries = entry_count
            self.Entries = (HBA_FCPScsiEntry * entry_count)()

    return HBA_FCPTargetMapping(entry_count)


class HBA_AdapterAttributes(ctypes.Structure):
    _fields_ = [('Manufacturer', wintypes.CHAR * 64),
                ('SerialNumber', wintypes.CHAR * 64),
                ('Model', wintypes.CHAR * 256),
                ('ModelDescription', wintypes.CHAR * 256),
                ('NodeWWN', HBA_WWN),
                ('NodeSymbolicName', wintypes.CHAR * 256),
                ('HardwareVersion', wintypes.CHAR * 256),
                ('DriverVersion', wintypes.CHAR * 256),
                ('OptionROMVersion', wintypes.CHAR * 256),
                ('FirmwareVersion', wintypes.CHAR * 256),
                ('VendorSpecificID', ctypes.c_uint32),
                ('NumberOfPorts', ctypes.c_uint32),
                ('DriverName', wintypes.CHAR * 256)]


def register():
    global lib_handle
    lib_handle = ctypes.cdll.LoadLibrary(CONF.os_win.hbaapi_lib_path)

    lib_handle.HBA_CloseAdapter.argtypes = [HBA_HANDLE]
    lib_handle.HBA_CloseAdapter.restype = None

    lib_handle.HBA_GetAdapterAttributes.argtypes = [
        HBA_HANDLE,
        ctypes.POINTER(HBA_AdapterAttributes)]
    lib_handle.HBA_GetAdapterAttributes.restype = HBA_STATUS

    lib_handle.HBA_GetAdapterName.argtypes = [
        ctypes.c_uint32,
        wintypes.PCHAR
    ]
    lib_handle.HBA_GetAdapterName.restype = HBA_STATUS

    lib_handle.HBA_GetAdapterPortAttributes.argtypes = [
        HBA_HANDLE,
        ctypes.c_uint32,
        ctypes.POINTER(HBA_PortAttributes)
    ]
    lib_handle.HBA_GetAdapterPortAttributes.restype = HBA_STATUS

    lib_handle.HBA_GetFcpTargetMapping.argtypes = [
        HBA_HANDLE,
        wintypes.PVOID
    ]
    lib_handle.HBA_GetFcpTargetMapping.restype = HBA_STATUS

    lib_handle.HBA_GetNumberOfAdapters.argtypes = []
    lib_handle.HBA_GetNumberOfAdapters.restype = ctypes.c_uint32

    lib_handle.HBA_OpenAdapter.argtypes = [wintypes.PCHAR]
    lib_handle.HBA_OpenAdapter.restype = HBA_HANDLE

    lib_handle.HBA_OpenAdapterByWWN.argtypes = [
        ctypes.POINTER(HBA_HANDLE),
        HBA_WWN]
    lib_handle.HBA_OpenAdapterByWWN.restype = HBA_STATUS

    lib_handle.HBA_ScsiInquiryV2.argtypes = [
        HBA_HANDLE,
        HBA_WWN,
        HBA_WWN,
        ctypes.c_uint64,
        ctypes.c_uint8,
        ctypes.c_uint8,
        wintypes.PVOID,
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint8),
        wintypes.PVOID,
        ctypes.POINTER(ctypes.c_uint32)
    ]
    lib_handle.HBA_ScsiInquiryV2.restype = HBA_STATUS

    lib_handle.HBA_RefreshAdapterConfiguration.argtypes = []
    lib_handle.HBA_RefreshAdapterConfiguration.restype = None
