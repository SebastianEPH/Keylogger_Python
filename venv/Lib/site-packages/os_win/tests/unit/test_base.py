# Copyright 2015 Cloudbase Solutions Srl
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

import mock
from oslotest import base
from oslotest import mock_fixture
from six.moves import builtins

import os

from os_win import exceptions
from os_win.utils import baseutils

mock_fixture.patch_mock_module()


class TestingException(Exception):
    pass


class FakeWMIExc(exceptions.x_wmi):
    def __init__(self, hresult=None):
        super(FakeWMIExc, self).__init__()
        excepinfo = [None] * 5 + [hresult]
        self.com_error = mock.Mock(excepinfo=excepinfo)
        self.com_error.hresult = hresult


class BaseTestCase(base.BaseTestCase):
    _autospec_classes = []

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.useFixture(mock_fixture.MockAutospecFixture())
        self._patch_autospec_classes()
        self.addCleanup(mock.patch.stopall)

    def _patch_autospec_classes(self):
        for class_type in self._autospec_classes:
            mocked_class = mock.MagicMock(autospec=class_type)
            patcher = mock.patch(
                '.'.join([class_type.__module__, class_type.__name__]),
                mocked_class)
            patcher.start()


class OsWinBaseTestCase(BaseTestCase):

    def setUp(self):
        super(OsWinBaseTestCase, self).setUp()

        self._mock_wmi = mock.MagicMock()
        baseutils.BaseUtilsVirt._old_wmi = self._mock_wmi

        mock_os = mock.MagicMock(Version='6.3.0')
        self._mock_wmi.WMI.return_value.Win32_OperatingSystem.return_value = (
            [mock_os])

        if os.name == 'nt':
            # The wmi module is expected to exist and by the time this runs,
            # the tested module will have imported it already.
            wmi_patcher = mock.patch('wmi.WMI', new=self._mock_wmi.WMI)
        else:
            # The wmi module doesn't exist, we'll have to "create" it.
            wmi_patcher = mock.patch.object(builtins, 'wmi', create=True,
                                            new=self._mock_wmi)
        wmi_patcher.start()
