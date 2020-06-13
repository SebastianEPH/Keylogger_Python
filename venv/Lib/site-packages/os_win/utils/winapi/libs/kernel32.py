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


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('ReadOperationCount', wintypes.ULONGLONG),
        ('WriteOperationCount', wintypes.ULONGLONG),
        ('OtherOperationCount', wintypes.ULONGLONG),
        ('ReadTransferCount', wintypes.ULONGLONG),
        ('WriteTransferCount', wintypes.ULONGLONG),
        ('OtherTransferCount', wintypes.ULONGLONG)
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('PerProcessUserTimeLimit', wintypes.LARGE_INTEGER),
        ('PerJobUserTimeLimit', wintypes.LARGE_INTEGER),
        ('LimitFlags', wintypes.DWORD),
        ('MinimumWorkingSetSize', ctypes.c_size_t),
        ('MaximumWorkingSetSize', ctypes.c_size_t),
        ('ActiveProcessLimit', wintypes.DWORD),
        ('Affinity', wintypes.PULONG),
        ('PriorityClass', wintypes.DWORD),
        ('SchedulingClass', wintypes.DWORD)
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ('IoInfo', IO_COUNTERS),
        ('ProcessMemoryLimit', ctypes.c_size_t),
        ('JobMemoryLimit', ctypes.c_size_t),
        ('PeakProcessMemoryUsed', ctypes.c_size_t),
        ('PeakJobMemoryUsed', ctypes.c_size_t)
    ]


class FILE_ID_128(ctypes.Structure):
    _fields_ = [
        ('Identifier', wintypes.BYTE * 16)
    ]


class FILE_ID_INFO(ctypes.Structure):
    _fields_ = [
        ('VolumeSerialNumber', wintypes.ULONGLONG),
        ('FileId', FILE_ID_128)
    ]


def register():
    global lib_handle
    lib_handle = ctypes.windll.kernel32

    lib_handle.CancelIoEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPOVERLAPPED
    ]
    lib_handle.CancelIoEx.restype = wintypes.BOOL

    lib_handle.CloseHandle.argtypes = [wintypes.HANDLE]
    lib_handle.CloseHandle.restype = wintypes.BOOL

    lib_handle.CopyFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.BOOL
    ]
    lib_handle.CopyFileW.restype = wintypes.BOOL

    lib_handle.CreateEventW.argtypes = [
        wintypes.PVOID,  # unused
        wintypes.BOOL,
        wintypes.BOOL,
        wintypes.LPCWSTR
    ]
    lib_handle.CreateEventW.restype = wintypes.HANDLE

    lib_handle.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.PVOID,  # unused
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE
    ]
    lib_handle.CreateFileW.restype = wintypes.HANDLE

    lib_handle.CreateMutexW.argtypes = [
        wintypes.LPCVOID,
        wintypes.BOOL,
        wintypes.LPCWSTR]
    lib_handle.CreateMutexW.restype = wintypes.HANDLE

    lib_handle.CreatePipe.argtypes = [
        wintypes.PHANDLE,
        wintypes.PHANDLE,
        wintypes.PVOID,
        wintypes.DWORD
    ]
    lib_handle.CreatePipe.restype = wintypes.BOOL

    lib_handle.CreateSymbolicLinkW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD
    ]
    lib_handle.CreateSymbolicLinkW.restype = wintypes.BOOL

    lib_handle.FormatMessageA.argtypes = [
        wintypes.DWORD,
        wintypes.LPCVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.PVOID,
        wintypes.DWORD,
        wintypes.PVOID
    ]
    lib_handle.FormatMessageA.restype = wintypes.DWORD

    lib_handle.GetFileInformationByHandleEx.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD

    ]
    lib_handle.GetFileInformationByHandleEx.restype = wintypes.BOOL

    lib_handle.GetDiskFreeSpaceExW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.PULARGE_INTEGER,
        wintypes.PULARGE_INTEGER,
        wintypes.PULARGE_INTEGER
    ]
    lib_handle.GetDiskFreeSpaceExW.restype = wintypes.BOOL

    lib_handle.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
    lib_handle.GetFileAttributesW.restype = wintypes.DWORD

    lib_handle.GetLastError.argtypes = []
    lib_handle.GetLastError.restype = wintypes.DWORD

    lib_handle.GetTickCount64.argtypes = []
    lib_handle.GetTickCount64.restype = wintypes.ULONGLONG

    lib_handle.IsProcessorFeaturePresent.argtypes = [wintypes.DWORD]
    lib_handle.IsProcessorFeaturePresent.restype = wintypes.BOOL

    lib_handle.LocalFree.argtypes = [wintypes.HANDLE]
    lib_handle.LocalFree.restype = wintypes.HANDLE

    lib_handle.ReadFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPDWORD,
        wintypes.LPOVERLAPPED
    ]
    lib_handle.ReadFile.restype = wintypes.BOOL

    lib_handle.ReadFileEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPOVERLAPPED,
        wintypes.LPOVERLAPPED_COMPLETION_ROUTINE
    ]
    lib_handle.ReadFileEx.restype = wintypes.BOOL

    lib_handle.ReleaseMutex.argtypes = [wintypes.HANDLE]
    lib_handle.ReleaseMutex.restype = wintypes.BOOL

    lib_handle.ResetEvent.argtypes = [wintypes.HANDLE]
    lib_handle.ResetEvent.restype = wintypes.BOOL

    lib_handle.SetEvent.argtypes = [wintypes.HANDLE]
    lib_handle.SetEvent.restype = wintypes.BOOL

    lib_handle.SetLastError.argtypes = [wintypes.DWORD]
    lib_handle.SetLastError.restype = None

    lib_handle.WaitForSingleObject.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD
    ]
    lib_handle.WaitForSingleObject.restype = wintypes.DWORD

    lib_handle.WaitForSingleObjectEx.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.BOOL
    ]
    lib_handle.WaitForSingleObjectEx.restype = wintypes.DWORD

    lib_handle.WaitNamedPipeW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD
    ]
    lib_handle.WaitNamedPipeW.restype = wintypes.BOOL

    lib_handle.WriteFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        wintypes.LPDWORD,
        wintypes.LPOVERLAPPED,
    ]
    lib_handle.WriteFile.restype = wintypes.BOOL

    lib_handle.WriteFileEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        wintypes.LPOVERLAPPED,
        wintypes.LPOVERLAPPED_COMPLETION_ROUTINE
    ]
    lib_handle.WriteFileEx.restype = wintypes.BOOL

    lib_handle.CreateJobObjectW.argtypes = [
        wintypes.LPCVOID,
        wintypes.LPCWSTR
    ]
    lib_handle.CreateJobObjectW.restype = wintypes.HANDLE

    lib_handle.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        wintypes.INT,
        wintypes.LPVOID,
        wintypes.DWORD
    ]
    lib_handle.SetInformationJobObject.restype = wintypes.BOOL

    lib_handle.AssignProcessToJobObject.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE
    ]
    lib_handle.AssignProcessToJobObject.restype = wintypes.BOOL

    lib_handle.OpenProcess.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD
    ]
    lib_handle.OpenProcess.restype = wintypes.HANDLE

    lib_handle.WaitForMultipleObjects.argtypes = [
        wintypes.DWORD,
        wintypes.LPHANDLE,
        wintypes.BOOL,
        wintypes.DWORD
    ]
    lib_handle.WaitForMultipleObjects.restype = wintypes.DWORD
