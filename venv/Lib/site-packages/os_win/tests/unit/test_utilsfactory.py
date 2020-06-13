# Copyright 2014 Cloudbase Solutions SRL
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
Unit tests for the Hyper-V utils factory.
"""

import inspect

import mock
from oslo_config import cfg
from oslo_utils import importutils

from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils.compute import clusterutils
from os_win.utils.compute import livemigrationutils
from os_win.utils.compute import migrationutils
from os_win.utils.compute import rdpconsoleutils
from os_win.utils.compute import vmutils
from os_win.utils.dns import dnsutils
from os_win.utils import hostutils
from os_win.utils.io import ioutils
from os_win.utils.network import networkutils
from os_win.utils import pathutils
from os_win.utils import processutils
from os_win.utils.storage import diskutils
from os_win.utils.storage.initiator import iscsi_utils
from os_win.utils.storage import smbutils
from os_win.utils.storage.virtdisk import vhdutils
from os_win import utilsfactory

CONF = cfg.CONF


class TestHyperVUtilsFactory(test_base.OsWinBaseTestCase):

    @mock.patch.object(utilsfactory.utils, 'get_windows_version')
    def test_get_class_unsupported_win_version(self, mock_get_windows_version):
        mock_get_windows_version.return_value = '5.2'
        self.assertRaises(exceptions.HyperVException, utilsfactory._get_class,
                          'hostutils')

    def test_get_class_unsupported_class_type(self):
        self.assertRaises(exceptions.HyperVException,
                          utilsfactory._get_class,
                          'invalid_class_type')

    @mock.patch.object(utilsfactory.utils, 'get_windows_version')
    def _check_get_class(self, mock_get_windows_version, expected_class,
                         class_type, windows_version='6.2', **kwargs):
        mock_get_windows_version.return_value = windows_version

        method = getattr(utilsfactory, 'get_%s' % class_type)
        instance = method(**kwargs)
        self.assertEqual(expected_class, type(instance))

        return instance

    def test_get_vmutils(self):
        instance = self._check_get_class(expected_class=vmutils.VMUtils,
                                         class_type='vmutils',
                                         host=mock.sentinel.host)
        self.assertEqual(mock.sentinel.host, instance._host)

    def test_get_vhdutils(self):
        self._check_get_class(expected_class=vhdutils.VHDUtils,
                              class_type='vhdutils')

    def test_get_networkutils(self):
        self._check_get_class(expected_class=networkutils.NetworkUtils,
                              class_type='networkutils')

    def test_get_networkutilsr2(self):
        self._check_get_class(expected_class=networkutils.NetworkUtilsR2,
                              class_type='networkutils',
                              windows_version='6.3')

    def test_get_hostutils(self):
        self._check_get_class(expected_class=hostutils.HostUtils,
                              class_type='hostutils')

    def test_get_pathutils(self):
        self._check_get_class(expected_class=pathutils.PathUtils,
                              class_type='pathutils')

    def test_get_livemigrationutils(self):
        self._check_get_class(
            expected_class=livemigrationutils.LiveMigrationUtils,
            class_type='livemigrationutils')

    @mock.patch.object(smbutils.SMBUtils, '__init__',
                       lambda *args, **kwargs: None)
    def test_get_smbutils(self):
        self._check_get_class(expected_class=smbutils.SMBUtils,
                              class_type='smbutils')

    def test_get_rdpconsoleutils(self):
        self._check_get_class(expected_class=rdpconsoleutils.RDPConsoleUtils,
                              class_type='rdpconsoleutils')

    def test_get_iscsi_initiator_utils(self):
        self._check_get_class(expected_class=iscsi_utils.ISCSIInitiatorUtils,
                              class_type='iscsi_initiator_utils')

    @mock.patch('os_win.utils.storage.initiator.fc_utils.FCUtils')
    def test_get_fc_utils(self, mock_cls_fcutils):
        self._check_get_class(
            expected_class=type(mock_cls_fcutils.return_value),
            class_type='fc_utils')

    def test_get_diskutils(self):
        self._check_get_class(
            expected_class=diskutils.DiskUtils,
            class_type='diskutils')

    @mock.patch.object(clusterutils.ClusterUtils, '_init_hyperv_conn')
    def test_get_clusterutils(self, mock_init_conn):
        self._check_get_class(
            expected_class=clusterutils.ClusterUtils,
            class_type='clusterutils')

    def test_get_dnsutils(self):
        self._check_get_class(
            expected_class=dnsutils.DNSUtils,
            class_type='dnsutils')

    def test_get_migrationutils(self):
        self._check_get_class(
            expected_class=migrationutils.MigrationUtils,
            class_type='migrationutils')

    def test_get_processutils(self):
        self._check_get_class(
            expected_class=processutils.ProcessUtils,
            class_type='processutils')

    def test_get_ioutils(self):
        self._check_get_class(
            expected_class=ioutils.IOUtils,
            class_type='ioutils')

    def test_utils_public_signatures(self):
        for module_name in utilsfactory.utils_map.keys():
            classes = utilsfactory.utils_map[module_name]
            if len(classes) < 2:
                continue

            base_class_dict = classes[0]
            base_class = importutils.import_object(base_class_dict['path'])
            for i in range(1, len(classes)):
                tested_class_dict = classes[i]
                tested_class = importutils.import_object(
                    tested_class_dict['path'])
                self.assertPublicAPISignatures(base_class, tested_class)
                self.assertPublicAPISignatures(tested_class, base_class)

    def assertPublicAPISignatures(self, baseinst, inst):
        def get_public_apis(inst):
            methods = {}
            for (name, value) in inspect.getmembers(inst, inspect.ismethod):
                if name.startswith("_"):
                    continue
                methods[name] = value
            return methods

        baseclass = baseinst.__class__.__name__
        basemethods = get_public_apis(baseinst)
        implmethods = get_public_apis(inst)

        extranames = [name for name in sorted(implmethods.keys()) if
                      name not in basemethods]
        self.assertEqual([], extranames,
                         "public methods not listed in class %s" % baseclass)

        for name in sorted(implmethods.keys()):
            baseargs = inspect.getargspec(basemethods[name])
            implargs = inspect.getargspec(implmethods[name])

            self.assertEqual(baseargs, implargs,
                             "%s args don't match class %s" %
                             (name, baseclass))
