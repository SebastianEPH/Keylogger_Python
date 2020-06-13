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


class NOTIFY_FILTER_AND_TYPE(ctypes.Structure):
    _fields_ = [
        ('dwObjectType', wintypes.DWORD),
        ('FilterFlags', wintypes.LONGLONG)
    ]


class CLUSTER_ENUM_ITEM(ctypes.Structure):
    _fields_ = [
        ('dwVersion', wintypes.DWORD),
        ('dwType', wintypes.DWORD),
        ('cbId', wintypes.DWORD),
        ('lpszId', wintypes.LPWSTR),
        ('cbName', wintypes.DWORD),
        ('lpszName', wintypes.LPWSTR)
    ]


PCLUSTER_ENUM_ITEM = ctypes.POINTER(CLUSTER_ENUM_ITEM)
PNOTIFY_FILTER_AND_TYPE = ctypes.POINTER(NOTIFY_FILTER_AND_TYPE)


def register():
    global lib_handle
    lib_handle = ctypes.windll.clusapi

    lib_handle.CancelClusterGroupOperation.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD
    ]
    lib_handle.CancelClusterGroupOperation.restype = wintypes.DWORD

    lib_handle.CloseCluster.argtypes = [wintypes.HANDLE]
    lib_handle.CloseCluster.restype = wintypes.BOOL

    lib_handle.CloseClusterGroup.argtypes = [wintypes.HANDLE]
    lib_handle.CloseClusterGroup.restype = wintypes.BOOL

    lib_handle.CloseClusterNode.argtypes = [wintypes.HANDLE]
    lib_handle.CloseClusterNode.restype = wintypes.BOOL

    lib_handle.CloseClusterResource.argtypes = [wintypes.HANDLE]
    lib_handle.CloseClusterResource.restype = wintypes.BOOL

    lib_handle.CloseClusterNotifyPort.argtypes = [wintypes.HANDLE]
    lib_handle.CloseClusterNotifyPort.restype = wintypes.BOOL

    lib_handle.ClusterCloseEnumEx.argtypes = [wintypes.HANDLE]
    lib_handle.ClusterCloseEnumEx.restype = wintypes.BOOL

    lib_handle.ClusterEnumEx.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.PVOID,
        wintypes.LPDWORD
    ]
    lib_handle.ClusterEnumEx.restype = wintypes.DWORD

    lib_handle.ClusterGetEnumCountEx.argtypes = [
        wintypes.HANDLE,
    ]
    lib_handle.ClusterGetEnumCountEx.restype = wintypes.DWORD

    lib_handle.ClusterGroupControl.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID
    ]
    lib_handle.ClusterGroupControl.restype = wintypes.DWORD

    lib_handle.ClusterOpenEnumEx.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.PVOID
    ]
    lib_handle.ClusterOpenEnumEx.restype = wintypes.HANDLE

    lib_handle.DestroyClusterGroup.argtypes = [
        wintypes.HANDLE
    ]
    lib_handle.DestroyClusterGroup.restype = wintypes.DWORD

    lib_handle.GetClusterGroupState.argtypes = [
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.PDWORD
    ]
    lib_handle.GetClusterGroupState.restype = wintypes.DWORD

    lib_handle.CreateClusterNotifyPortV2.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
        PNOTIFY_FILTER_AND_TYPE,
        wintypes.DWORD,
        wintypes.PDWORD
    ]
    lib_handle.CreateClusterNotifyPortV2.restype = wintypes.HANDLE

    lib_handle.GetClusterNotifyV2.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.PDWORD),
        PNOTIFY_FILTER_AND_TYPE,
        wintypes.PBYTE,
        wintypes.LPDWORD,
        wintypes.LPWSTR,
        wintypes.LPDWORD,
        wintypes.LPWSTR,
        wintypes.LPDWORD,
        wintypes.LPWSTR,
        wintypes.LPDWORD,
        wintypes.LPWSTR,
        wintypes.LPDWORD,
        wintypes.DWORD
    ]
    lib_handle.GetClusterNotifyV2.restype = wintypes.DWORD

    lib_handle.MoveClusterGroupEx.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.PVOID,
        wintypes.DWORD
    ]
    lib_handle.MoveClusterGroupEx.restype = wintypes.DWORD

    lib_handle.OfflineClusterGroup.argtypes = [
        wintypes.HANDLE
    ]
    lib_handle.OfflineClusterGroup.restype = wintypes.DWORD

    lib_handle.OnlineClusterGroup.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
    ]
    lib_handle.OnlineClusterGroup.restype = wintypes.DWORD

    lib_handle.OpenCluster.argtypes = [wintypes.LPCWSTR]
    lib_handle.OpenCluster.restype = wintypes.HANDLE

    lib_handle.OpenClusterGroup.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCWSTR
    ]
    lib_handle.OpenClusterGroup.restype = wintypes.HANDLE

    lib_handle.OpenClusterNode.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCWSTR
    ]
    lib_handle.OpenClusterNode.restype = wintypes.HANDLE

    lib_handle.OpenClusterResource.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCWSTR
    ]
    lib_handle.OpenClusterResource.restype = wintypes.HANDLE
