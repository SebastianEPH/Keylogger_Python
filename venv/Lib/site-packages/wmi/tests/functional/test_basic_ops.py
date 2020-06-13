# Copyright 2016 Cloudbase Solutions Srl
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

import os
import time

import wmi
from wmi.tests.functional import test_base


class BasicOpsTestCase(test_base.BaseFunctionalTestCase):
    def test_query(self):
        win_version_str = self._conn_cimv2.Win32_OperatingSystem()[0].Version
        win_version = list(map(int, win_version_str.split('.')))

        self.assertTrue(win_version >= [6, 0])

    @test_base.BaseFunctionalTestCase.pass_temp_file
    def test_invoke_method(self, temp_file_path):
        content = str(time.time())
        cmd = "cmd /c echo %s > %s" % (content, temp_file_path)
        startup_info = self._conn_cimv2.Win32_ProcessStartup.new()
        startup_info.ShowWindow = 0

        pid, ret_val = self._conn_cimv2.Win32_Process.Create(
            CommandLine=cmd,
            CurrentDirectory=None,
            ProcessStartupInformation=startup_info)

        time.sleep(0.5)

        with open(temp_file_path, 'r') as f:
            actual_content = f.read().strip('\n ')

        self.assertEqual(content, actual_content)

    def test_associators(self):
        logical_disk = self._conn_cimv2.Win32_LogicalDisk()[0]
        root_dir = logical_disk.associators(
            wmi_association_class="Win32_LogicalDiskRootDirectory")[0]

        self.assertEqual(logical_disk.Name.lower(),
                         root_dir.Name.lower().strip('\\'))

    def test_new_conn_invalid_creds(self):
        err_code = None
        try:
            wmi.WMI(user='invalidcredstest')
        except wmi.x_wmi as exc:
            err_code = exc.com_error.hresult & 0xFFFF

        error_logon_failure = 0x52e
        self.assertEqual(error_logon_failure, err_code)
