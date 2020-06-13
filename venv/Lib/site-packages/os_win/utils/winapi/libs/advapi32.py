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


class TRUSTEE(ctypes.Structure):
    _fields_ = [
        ('pMultipleTrustee', wintypes.PVOID),
        ('MultipleTrusteeOperation', wintypes.INT),
        ('TrusteeForm', wintypes.INT),
        ('TrusteeType', wintypes.INT),
        ('pstrName', wintypes.LPWSTR)
    ]


class EXPLICIT_ACCESS(ctypes.Structure):
    _fields_ = [
        ('grfAccessPermissions', wintypes.DWORD),
        ('grfAccessMode', wintypes.INT),
        ('grfInheritance', wintypes.DWORD),
        ('Trustee', TRUSTEE)
    ]


PEXPLICIT_ACCESS = ctypes.POINTER(EXPLICIT_ACCESS)


def register():
    global lib_handle
    lib_handle = ctypes.windll.advapi32

    lib_handle.GetNamedSecurityInfoW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.INT,
        wintypes.DWORD,
        wintypes.PVOID,
        wintypes.PVOID,
        wintypes.PVOID,
        wintypes.PVOID,
        wintypes.PVOID
    ]
    lib_handle.GetNamedSecurityInfoW.restype = wintypes.DWORD

    lib_handle.SetEntriesInAclW.argtypes = [
        wintypes.ULONG,
        PEXPLICIT_ACCESS,
        wintypes.PVOID,
        wintypes.PVOID
    ]
    lib_handle.SetEntriesInAclW.restype = wintypes.DWORD

    lib_handle.SetNamedSecurityInfoW.argtypes = [
        wintypes.LPWSTR,
        wintypes.INT,
        wintypes.DWORD,
        wintypes.PVOID,
        wintypes.PVOID,
        wintypes.PVOID,
        wintypes.PVOID
    ]
    lib_handle.SetNamedSecurityInfoW.restype = wintypes.DWORD
