#  Copyright 2016 Cloudbase Solutions Srl
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

import mock
import six

import imp

from os_win.tests.unit import test_base
from os_win.utils import baseutils


class BaseUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the os-win BaseUtils class."""

    def setUp(self):
        super(BaseUtilsTestCase, self).setUp()
        self.utils = baseutils.BaseUtils()
        self.utils._conn = mock.MagicMock()
        mock.patch.object(imp, 'load_source').start()

    @mock.patch.object(baseutils, 'wmi', create=True)
    def test_get_wmi_obj(self, mock_wmi):
        result = self.utils._get_wmi_obj(mock.sentinel.moniker)

        self.assertEqual(mock_wmi.WMI.return_value, result)
        mock_wmi.WMI.assert_called_once_with(moniker=mock.sentinel.moniker)

    @mock.patch.object(baseutils.BaseUtils, '_get_wmi_obj')
    @mock.patch.object(baseutils, 'sys')
    def _check_get_wmi_conn(self, mock_sys, mock_get_wmi_obj, **kwargs):
        mock_sys.platform = 'win32'
        result = self.utils._get_wmi_conn(mock.sentinel.moniker, **kwargs)

        self.assertEqual(mock_get_wmi_obj.return_value, result)
        mock_get_wmi_obj.assert_called_once_with(mock.sentinel.moniker,
                                                 **kwargs)

    def test_get_wmi_conn_kwargs(self):
        self.utils._WMI_CONS.clear()
        self._check_get_wmi_conn(privileges=mock.sentinel.privileges)
        self.assertNotIn(mock.sentinel.moniker, baseutils.BaseUtils._WMI_CONS)

    def test_get_wmi_conn(self):
        self._check_get_wmi_conn()
        self.assertIn(mock.sentinel.moniker, baseutils.BaseUtils._WMI_CONS)

    @mock.patch.object(baseutils.BaseUtils, '_get_wmi_obj')
    @mock.patch.object(baseutils, 'sys')
    def test_get_wmi_conn_cached(self, mock_sys, mock_get_wmi_obj):
        mock_sys.platform = 'win32'
        baseutils.BaseUtils._WMI_CONS[mock.sentinel.moniker] = (
            mock.sentinel.conn)
        result = self.utils._get_wmi_conn(mock.sentinel.moniker)

        self.assertEqual(mock.sentinel.conn, result)
        self.assertFalse(mock_get_wmi_obj.called)

    @mock.patch.object(baseutils, 'sys')
    def test_get_wmi_conn_linux(self, mock_sys):
        mock_sys.platform = 'linux'
        result = self.utils._get_wmi_conn(mock.sentinel.moniker)

        self.assertIsNone(result)


class BaseUtilsVirtTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the os-win BaseUtilsVirt class."""

    def setUp(self):
        super(BaseUtilsVirtTestCase, self).setUp()
        self.utils = baseutils.BaseUtilsVirt()
        self.utils._conn_attr = mock.MagicMock()
        baseutils.BaseUtilsVirt._os_version = None
        mock.patch.object(imp, 'load_source').start()

    @mock.patch.object(baseutils.BaseUtilsVirt, '_get_wmi_conn')
    def test_conn(self, mock_get_wmi_conn):
        self.utils._conn_attr = None

        self.assertEqual(mock_get_wmi_conn.return_value, self.utils._conn)
        mock_get_wmi_conn.assert_called_once_with(
            self.utils._wmi_namespace % '.')

    def test_vs_man_svc(self):
        mock_os = mock.MagicMock(Version='6.3.0')
        self._mock_wmi.WMI.return_value.Win32_OperatingSystem.return_value = [
            mock_os]
        expected = self.utils._conn.Msvm_VirtualSystemManagementService()[0]
        self.assertEqual(expected, self.utils._vs_man_svc)
        self.assertEqual(expected, self.utils._vs_man_svc_attr)

    @mock.patch.object(baseutils, 'wmi', create=True)
    def test_vs_man_svc_2012(self, mock_wmi):
        baseutils.BaseUtilsVirt._old_wmi = None
        mock_os = mock.MagicMock(Version='6.2.0')
        mock_wmi.WMI.return_value.Win32_OperatingSystem.return_value = [
            mock_os]
        fake_module_path = '/fake/path/to/module'
        mock_wmi.__path__ = [fake_module_path]
        old_conn = imp.load_source.return_value.WMI.return_value

        expected = old_conn.Msvm_VirtualSystemManagementService()[0]
        self.assertEqual(expected, self.utils._vs_man_svc)
        self.assertIsNone(self.utils._vs_man_svc_attr)
        imp.load_source.assert_called_once_with(
            'old_wmi', '%s.py' % fake_module_path)

    @mock.patch.object(baseutils.BaseUtilsVirt, '_get_wmi_compat_conn')
    def test_get_wmi_obj_compatibility_6_3(self, mock_get_wmi_compat):
        mock_os = mock.MagicMock(Version='6.3.0')
        self._mock_wmi.WMI.return_value.Win32_OperatingSystem.return_value = [
            mock_os]

        result = self.utils._get_wmi_obj(mock.sentinel.moniker, True)
        self.assertEqual(self._mock_wmi.WMI.return_value, result)

    @mock.patch.object(baseutils.BaseUtilsVirt, '_get_wmi_compat_conn')
    def test_get_wmi_obj_no_compatibility_6_2(self, mock_get_wmi_compat):
        baseutils.BaseUtilsVirt._os_version = [6, 2]
        result = self.utils._get_wmi_obj(mock.sentinel.moniker, False)
        self.assertEqual(self._mock_wmi.WMI.return_value, result)

    @mock.patch.object(baseutils.BaseUtilsVirt, '_get_wmi_compat_conn')
    def test_get_wmi_obj_compatibility_6_2(self, mock_get_wmi_compat):
        baseutils.BaseUtilsVirt._os_version = [6, 2]
        result = self.utils._get_wmi_obj(mock.sentinel.moniker, True)
        self.assertEqual(mock_get_wmi_compat.return_value, result)


class SynchronizedMetaTestCase(test_base.OsWinBaseTestCase):
    @mock.patch.object(baseutils.threading, 'RLock')
    def test_synchronized_meta(self, mock_rlock_cls):
        fake_cls = type('fake_cls', (object, ),
                        dict(method1=lambda x: None, method2=lambda y: None))
        fake_cls = six.add_metaclass(baseutils.SynchronizedMeta)(fake_cls)

        fake_cls().method1()
        fake_cls().method2()

        mock_rlock_cls.assert_called_once_with()
        self.assertEqual(2, mock_rlock_cls.return_value.__exit__.call_count)
