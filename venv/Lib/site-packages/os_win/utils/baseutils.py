# Copyright 2016 Cloudbase Solutions Srl
#
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
Base WMI utility class.
"""

import imp
import sys
import threading
import time

from oslo_log import log as logging
from oslo_utils import reflection

if sys.platform == 'win32':
    import wmi

LOG = logging.getLogger(__name__)


class BaseUtils(object):

    _WMI_CONS = {}

    def _get_wmi_obj(self, moniker, **kwargs):
        return wmi.WMI(moniker=moniker, **kwargs)

    def _get_wmi_conn(self, moniker, **kwargs):
        if sys.platform != 'win32':
            return None
        if kwargs:
            return self._get_wmi_obj(moniker, **kwargs)
        if moniker in self._WMI_CONS:
            return self._WMI_CONS[moniker]

        wmi_conn = self._get_wmi_obj(moniker)
        self._WMI_CONS[moniker] = wmi_conn
        return wmi_conn


class BaseUtilsVirt(BaseUtils):

    _wmi_namespace = '//%s/root/virtualization/v2'
    _os_version = None
    _old_wmi = None

    def __init__(self, host='.'):
        self._vs_man_svc_attr = None
        self._host = host
        self._conn_attr = None
        self._compat_conn_attr = None

    @property
    def _conn(self):
        if not self._conn_attr:
            self._conn_attr = self._get_wmi_conn(
                self._wmi_namespace % self._host)
        return self._conn_attr

    @property
    def _compat_conn(self):
        if not self._compat_conn_attr:
            if not BaseUtilsVirt._os_version:
                # hostutils cannot be used for this, it would end up in
                # a circular import.
                os_version = wmi.WMI().Win32_OperatingSystem()[0].Version
                BaseUtilsVirt._os_version = list(
                    map(int, os_version.split('.')))

            if BaseUtilsVirt._os_version >= [6, 3]:
                self._compat_conn_attr = self._conn
            else:
                self._compat_conn_attr = self._get_wmi_compat_conn(
                    moniker=self._wmi_namespace % self._host)

        return self._compat_conn_attr

    @property
    def _vs_man_svc(self):
        if self._vs_man_svc_attr:
            return self._vs_man_svc_attr

        vs_man_svc = self._compat_conn.Msvm_VirtualSystemManagementService()[0]
        if BaseUtilsVirt._os_version >= [6, 3]:
            # NOTE(claudiub): caching this property on Windows / Hyper-V Server
            # 2012 (using the old WMI) can lead to memory leaks. PyMI doesn't
            # have those issues, so we can safely cache it.
            self._vs_man_svc_attr = vs_man_svc
        return vs_man_svc

    def _get_wmi_compat_conn(self, moniker, **kwargs):
        # old WMI should be used on Windows / Hyper-V Server 2012 whenever
        # .GetText_ is used (e.g.: AddResourceSettings). PyMI's and WMI's
        # .GetText_ have different results.
        if not BaseUtilsVirt._old_wmi:
            old_wmi_path = "%s.py" % wmi.__path__[0]
            BaseUtilsVirt._old_wmi = imp.load_source('old_wmi', old_wmi_path)
        return BaseUtilsVirt._old_wmi.WMI(moniker=moniker, **kwargs)

    def _get_wmi_obj(self, moniker, compatibility_mode=False, **kwargs):
        if not BaseUtilsVirt._os_version:
            # hostutils cannot be used for this, it would end up in
            # a circular import.
            os_version = wmi.WMI().Win32_OperatingSystem()[0].Version
            BaseUtilsVirt._os_version = list(map(int, os_version.split('.')))

        if not compatibility_mode or BaseUtilsVirt._os_version >= [6, 3]:
            return wmi.WMI(moniker=moniker, **kwargs)
        return self._get_wmi_compat_conn(moniker=moniker, **kwargs)


class SynchronizedMeta(type):
    """Use an rlock to synchronize all class methods."""

    def __init__(cls, cls_name, bases, attrs):
        super(SynchronizedMeta, cls).__init__(cls_name, bases, attrs)
        rlock = threading.RLock()

        for attr_name in attrs:
            attr = getattr(cls, attr_name)
            if callable(attr):
                decorated = SynchronizedMeta._synchronize(
                    attr, cls_name, rlock)
                setattr(cls, attr_name, decorated)

    @staticmethod
    def _synchronize(func, cls_name, rlock):
        def wrapper(*args, **kwargs):
            f_qual_name = reflection.get_callable_name(func)

            t_request = time.time()
            try:
                with rlock:
                    t_acquire = time.time()
                    LOG.debug("Method %(method_name)s acquired rlock. "
                              "Waited %(time_wait)0.3fs",
                              dict(method_name=f_qual_name,
                                   time_wait=t_acquire - t_request))
                    return func(*args, **kwargs)
            finally:
                t_release = time.time()
                LOG.debug("Method %(method_name)s released rlock. "
                          "Held %(time_held)0.3fs",
                          dict(method_name=f_qual_name,
                               time_held=t_release - t_acquire))
        return wrapper
