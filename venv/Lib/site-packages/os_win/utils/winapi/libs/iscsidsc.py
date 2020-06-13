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

from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi import wintypes

lib_handle = None

ISCSI_SECURITY_FLAGS = ctypes.c_uint64
ISCSI_LOGIN_FLAGS = ctypes.c_uint32
ISCSI_LOGIN_OPTIONS_INFO_SPECIFIED = ctypes.c_uint32
ISCSI_AUTH_TYPES = wintypes.UINT
ISCSI_DIGEST_TYPES = wintypes.UINT
DEVICE_TYPE = wintypes.ULONG


class ISCSI_TARGET_PORTAL(ctypes.Structure):
    _fields_ = [
        ('SymbolicName', wintypes.WCHAR * w_const.MAX_ISCSI_PORTAL_NAME_LEN),
        ('Address', wintypes.WCHAR * w_const.MAX_ISCSI_PORTAL_ADDRESS_LEN),
        ('Socket', wintypes.USHORT)
    ]


PISCSI_TARGET_PORTAL = ctypes.POINTER(ISCSI_TARGET_PORTAL)


class ISCSI_LOGIN_OPTIONS(ctypes.Structure):
    _fields_ = [
        ('Version', wintypes.ULONG),
        ('InformationSpecified', ISCSI_LOGIN_OPTIONS_INFO_SPECIFIED),
        ('LoginFlags', ISCSI_LOGIN_FLAGS),
        ('AuthType', ISCSI_AUTH_TYPES),
        ('HeaderDigest', ISCSI_DIGEST_TYPES),
        ('DataDigest', ISCSI_DIGEST_TYPES),
        ('MaximumConnections', wintypes.ULONG),
        ('DefaultTime2Wait', wintypes.ULONG),
        ('DefaultTime2Retain', wintypes.ULONG),
        ('UsernameLength', wintypes.ULONG),
        ('PasswordLength', wintypes.ULONG),
        ('Username', wintypes.PSTR),
        ('Password', wintypes.PSTR)
    ]


PISCSI_LOGIN_OPTIONS = ctypes.POINTER(ISCSI_LOGIN_OPTIONS)


class SCSI_LUN_LIST(ctypes.Structure):
    _fields_ = [
        ('OSLUN', wintypes.ULONG),
        ('TargetLUN', wintypes.ULONGLONG)
    ]


PSCSI_LUN_LIST = ctypes.POINTER(SCSI_LUN_LIST)


class ISCSI_UNIQUE_SESSION_ID(ctypes.Structure):
    _fields_ = [
        ('AdapterUnique', wintypes.ULONGLONG),
        ('AdapterSpecific', wintypes.ULONGLONG)
    ]


PISCSI_UNIQUE_SESSION_ID = ctypes.POINTER(ISCSI_UNIQUE_SESSION_ID)


class ISCSI_UNIQUE_CONNECTION_ID(ISCSI_UNIQUE_SESSION_ID):
    pass


PISCSI_UNIQUE_CONNECTION_ID = ctypes.POINTER(ISCSI_UNIQUE_CONNECTION_ID)


class ISCSI_TARGET_MAPPING(ctypes.Structure):
    _fields_ = [
        ('InitiatorName', wintypes.WCHAR * w_const.MAX_ISCSI_HBANAME_LEN),
        ('TargetName', wintypes.WCHAR * (w_const.MAX_ISCSI_NAME_LEN + 1)),
        ('OSDeviceName', wintypes.WCHAR * w_const.MAX_PATH),
        ('SessionId', ISCSI_UNIQUE_SESSION_ID),
        ('OSBusNumber', wintypes.ULONG),
        ('OSTargetNumber', wintypes.ULONG),
        ('LUNCount', wintypes.ULONG),
        ('LUNList', PSCSI_LUN_LIST)
    ]


PISCSI_TARGET_MAPPING = ctypes.POINTER(ISCSI_TARGET_MAPPING)


class PERSISTENT_ISCSI_LOGIN_INFO(ctypes.Structure):
    _fields_ = [
        ('TargetName', wintypes.WCHAR * (w_const.MAX_ISCSI_NAME_LEN + 1)),
        ('IsInformationalSession', wintypes.BOOLEAN),
        ('InitiatorInstance', wintypes.WCHAR * w_const.MAX_ISCSI_HBANAME_LEN),
        ('InitiatorPortNumber', wintypes.ULONG),
        ('TargetPortal', ISCSI_TARGET_PORTAL),
        ('SecurityFlags', ISCSI_SECURITY_FLAGS),
        ('Mappings', PISCSI_TARGET_MAPPING),
        ('LoginOptions', ISCSI_LOGIN_OPTIONS)
    ]


PPERSISTENT_ISCSI_LOGIN_INFO = ctypes.POINTER(PERSISTENT_ISCSI_LOGIN_INFO)


class ISCSI_CONNECTION_INFO(ctypes.Structure):
    _fields_ = [
        ('ConnectionId', ISCSI_UNIQUE_CONNECTION_ID),
        ('InitiatorAddress', wintypes.PWSTR),
        ('TargetAddress', wintypes.PWSTR),
        ('InitiatorSocket', wintypes.USHORT),
        ('TargetSocket', wintypes.USHORT),
        ('CID', ctypes.c_ubyte * 2)
    ]


PISCSI_CONNECTION_INFO = ctypes.POINTER(ISCSI_CONNECTION_INFO)


class ISCSI_SESSION_INFO(ctypes.Structure):
    _fields_ = [
        ('SessionId', ISCSI_UNIQUE_SESSION_ID),
        ('InitiatorName', wintypes.PWSTR),
        ('TargetName', wintypes.PWSTR),
        ('TargetNodeName', wintypes.PWSTR),
        ('ISID', ctypes.c_ubyte * 6),
        ('TSID', ctypes.c_ubyte * 2),
        ('ConnectionCount', wintypes.ULONG),
        ('Connections', PISCSI_CONNECTION_INFO)
    ]


PISCSI_SESSION_INFO = ctypes.POINTER(ISCSI_SESSION_INFO)


class SCSI_ADDRESS(ctypes.Structure):
    _fields_ = [
        ('Length', wintypes.ULONG),
        ('PortNumber', ctypes.c_ubyte),
        ('PathId', ctypes.c_ubyte),
        ('TargetId', ctypes.c_ubyte),
        ('Lun', ctypes.c_ubyte)
    ]


class STORAGE_DEVICE_NUMBER(ctypes.Structure):
    _fields_ = [
        ('DeviceType', DEVICE_TYPE),
        ('DeviceNumber', wintypes.DWORD),
        ('PartitionNumber', wintypes.DWORD)
    ]


class ISCSI_DEVICE_ON_SESSION(ctypes.Structure):
    _fields_ = [
        ('InitiatorName', wintypes.WCHAR * w_const.MAX_ISCSI_HBANAME_LEN),
        ('TargetName', wintypes.WCHAR * (w_const.MAX_ISCSI_NAME_LEN + 1)),
        ('ScsiAddress', SCSI_ADDRESS),
        ('DeviceInterfaceType', wintypes.GUID),
        ('DeviceInterfaceName', wintypes.WCHAR * w_const.MAX_PATH),
        ('LegacyName', wintypes.WCHAR * w_const.MAX_PATH),
        ('StorageDeviceNumber', STORAGE_DEVICE_NUMBER),
        ('DeviceInstance', wintypes.ULONG)
    ]


PISCSI_DEVICE_ON_SESSION = ctypes.POINTER(ISCSI_DEVICE_ON_SESSION)


def register():
    global lib_handle
    lib_handle = ctypes.windll.iscsidsc

    lib_handle.AddIScsiStaticTargetW.argtypes = [
        wintypes.PWSTR,
        wintypes.PWSTR,
        wintypes.ULONG,
        wintypes.BOOLEAN,
        PISCSI_TARGET_MAPPING,
        PISCSI_LOGIN_OPTIONS,
        wintypes.LPVOID  # unused
    ]
    lib_handle.AddIScsiStaticTargetW.restype = wintypes.ULONG

    lib_handle.GetDevicesForIScsiSessionW.argtypes = [
        PISCSI_UNIQUE_SESSION_ID,
        wintypes.PULONG,
        PISCSI_DEVICE_ON_SESSION
    ]
    lib_handle.GetDevicesForIScsiSessionW.restype = wintypes.ULONG

    lib_handle.GetIScsiInitiatorNodeNameW.argtypes = [wintypes.PWCHAR]
    lib_handle.GetIScsiInitiatorNodeNameW.restype = wintypes.ULONG

    lib_handle.GetIScsiSessionListW.argtypes = [
        wintypes.PULONG,
        wintypes.PULONG,
        PISCSI_SESSION_INFO
    ]
    lib_handle.GetIScsiSessionListW.restype = wintypes.ULONG

    lib_handle.LoginIScsiTargetW.argtypes = [
        wintypes.PWSTR,
        wintypes.BOOLEAN,
        wintypes.PWSTR,
        wintypes.ULONG,
        PISCSI_TARGET_PORTAL,
        ISCSI_SECURITY_FLAGS,
        PISCSI_TARGET_MAPPING,
        PISCSI_LOGIN_OPTIONS,
        wintypes.ULONG,
        wintypes.PCHAR,
        wintypes.BOOLEAN,
        PISCSI_UNIQUE_SESSION_ID,
        PISCSI_UNIQUE_CONNECTION_ID
    ]
    lib_handle.LoginIScsiTargetW.restype = wintypes.ULONG

    lib_handle.LogoutIScsiTarget.argtypes = [PISCSI_UNIQUE_SESSION_ID]
    lib_handle.LogoutIScsiTarget.restype = wintypes.ULONG

    lib_handle.RemoveIScsiPersistentTargetW.argtypes = [
        wintypes.PWSTR,
        wintypes.ULONG,
        wintypes.PWSTR,
        PISCSI_TARGET_PORTAL
    ]
    lib_handle.RemoveIScsiPersistentTargetW.restype = wintypes.ULONG

    lib_handle.RemoveIScsiStaticTargetW.argtypes = [wintypes.PWSTR]
    lib_handle.RemoveIScsiStaticTargetW.restype = wintypes.ULONG

    lib_handle.ReportIScsiInitiatorListW.argtypes = [
        wintypes.PULONG,
        wintypes.PWCHAR
    ]
    lib_handle.ReportIScsiInitiatorListW.restype = wintypes.ULONG

    lib_handle.ReportIScsiPersistentLoginsW.argtypes = [
        wintypes.PULONG,
        PPERSISTENT_ISCSI_LOGIN_INFO,
        wintypes.PULONG
    ]
    lib_handle.ReportIScsiPersistentLoginsW.restype = wintypes.ULONG

    lib_handle.ReportIScsiTargetsW.argtypes = [
        wintypes.BOOLEAN,
        wintypes.PULONG,
        wintypes.PWCHAR
    ]
    lib_handle.ReportIScsiTargetsW.restype = wintypes.ULONG
