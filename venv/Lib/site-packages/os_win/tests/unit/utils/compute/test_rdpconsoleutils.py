#  Copyright 2013 Cloudbase Solutions Srl
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

from os_win.tests.unit import test_base
from os_win.utils.compute import rdpconsoleutils


class RDPConsoleUtilsTestCase(test_base.OsWinBaseTestCase):
    _FAKE_RDP_PORT = 1000

    def setUp(self):
        self._rdpconsoleutils = rdpconsoleutils.RDPConsoleUtils()
        self._rdpconsoleutils._conn_attr = mock.MagicMock()

        super(RDPConsoleUtilsTestCase, self).setUp()

    def test_get_rdp_console_port(self):
        conn = self._rdpconsoleutils._conn
        mock_rdp_setting_data = conn.Msvm_TerminalServiceSettingData()[0]
        mock_rdp_setting_data.ListenerPort = self._FAKE_RDP_PORT

        listener_port = self._rdpconsoleutils.get_rdp_console_port()

        self.assertEqual(self._FAKE_RDP_PORT, listener_port)
