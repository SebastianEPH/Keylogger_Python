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

# This module contains some common types extracted from ctypes.wintypes
# plus some extra ones that we are using throughout os-win.
#
# In order to avoid portability issues more easily, we avoid using
# ctypes.wintypes directly.

import ctypes
import sys

BYTE = ctypes.c_byte
WORD = ctypes.c_ushort
DWORD = ctypes.c_ulong

CHAR = ctypes.c_char
WCHAR = ctypes.c_wchar
UINT = ctypes.c_uint
INT = ctypes.c_int

DOUBLE = ctypes.c_double
FLOAT = ctypes.c_float

BOOLEAN = BYTE
BOOL = ctypes.c_long

ULONG = ctypes.c_ulong
LONG = ctypes.c_long

USHORT = ctypes.c_ushort
SHORT = ctypes.c_short

LONGLONG = _LARGE_INTEGER = LARGE_INTEGER = ctypes.c_longlong
ULONGLONG = _ULARGE_INTEGER = ULARGE_INTEGER = ctypes.c_ulonglong

LPCOLESTR = LPOLESTR = OLESTR = ctypes.c_wchar_p
LPCWSTR = LPWSTR = PWSTR = ctypes.c_wchar_p
LPCSTR = LPSTR = PSTR = ctypes.c_char_p
LPCVOID = LPVOID = PVOID = ctypes.c_void_p

HANDLE = ctypes.c_void_p

LPBOOL = PBOOL = ctypes.POINTER(BOOL)
PBOOLEAN = ctypes.POINTER(BOOLEAN)
LPBYTE = PBYTE = ctypes.POINTER(BYTE)
PCHAR = ctypes.POINTER(CHAR)
LPDWORD = PDWORD = ctypes.POINTER(DWORD)
PFLOAT = ctypes.POINTER(FLOAT)
LPHANDLE = PHANDLE = ctypes.POINTER(HANDLE)
LPINT = PINT = ctypes.POINTER(INT)
PLARGE_INTEGER = ctypes.POINTER(LARGE_INTEGER)
LPLONG = PLONG = ctypes.POINTER(LONG)
PLONGLONG = ctypes.POINTER(LONGLONG)
PSHORT = ctypes.POINTER(SHORT)
LPUINT = PUINT = ctypes.POINTER(UINT)
PULARGE_INTEGER = ctypes.POINTER(ULARGE_INTEGER)
PULONG = ctypes.POINTER(ULONG)
PUSHORT = ctypes.POINTER(USHORT)
# Warning: PWCHAR behaves differently than c_wchar_p. Accessing
# a PWCHAR structure attribute won't give us back a Python string.
PWCHAR = ctypes.POINTER(WCHAR)
LPWORD = PWORD = ctypes.POINTER(WORD)


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ULONG),
        ("Data2", USHORT),
        ("Data3", USHORT),
        ("Data4", BYTE * 8)
    ]


class OVERLAPPED(ctypes.Structure):
    _fields_ = [
        ('Internal', ULONG),
        ('InternalHigh', ULONG),
        ('Offset', DWORD),
        ('OffsetHigh', DWORD),
        ('hEvent', HANDLE)
    ]


LPOVERLAPPED = ctypes.POINTER(OVERLAPPED)

if sys.platform == 'win32':
    LPOVERLAPPED_COMPLETION_ROUTINE = ctypes.WINFUNCTYPE(
        None, DWORD, DWORD, LPOVERLAPPED)
else:
    LPOVERLAPPED_COMPLETION_ROUTINE = PVOID


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ('nLength', DWORD),
        ('lpSecurityDescriptor', LPVOID),
        ('bInheritHandle', BOOL)
    ]
