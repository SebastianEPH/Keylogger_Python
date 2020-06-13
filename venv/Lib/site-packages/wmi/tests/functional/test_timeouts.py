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


# The following tests perform various operations,
# setting timeouts that are expected to be hit.
class OperationTimeoutTestCase(test_base.BaseFunctionalTestCase):
    def _check_op_timeout(self, f, *args, **kwargs):
        # 'f' is expected to be a method that accepts
        # operation options.
        self.assertRaises(wmi.x_wmi_timed_out,
                          f, *args,
                          operation_options={'operation_timeout': 0.001},
                          **kwargs)

    def test_query(self):
        self._check_op_timeout(self._conn_cimv2.Win32_Process)

    @test_base.BaseFunctionalTestCase.pass_temp_file
    @test_base.BaseFunctionalTestCase.pass_temp_file
    def test_invoke_method(self, temp_src, temp_dest):
        with open(temp_src, 'w') as f:
            f.write('random data' * (10 << 20))
        os.unlink(temp_dest)

        datafile = self._conn_cimv2.Cim_DataFile(Name=temp_src)[0]
        self._check_op_timeout(datafile.Copy, temp_dest)

        time.sleep(0.5)

    def test_associators(self):
        disk = self._conn_cimv2.Win32_DiskDrive()[0]
        self._check_op_timeout(disk.associators)

    @test_base.BaseFunctionalTestCase.pass_temp_file
    def test_modify_delete(self, temp_file_path):
        operation_options = {'operation_timeout': 1}

        datafile = self._conn_cimv2.Cim_DataFile(Name=temp_file_path)[0]
        datafile.Description = 'fake_description'
        datafile.put(operation_options=operation_options)
        datafile.Delete_(operation_options=operation_options)

    def test_per_session_timeouts(self):
        conn = wmi.WMI(operation_timeout=0.1)
        self.assertRaises(wmi.x_wmi_timed_out,
                          conn.Win32_Processor)

        # We expect the query to be successful after we override the
        # session based operation timeout.
        conn.Win32_Process(operation_options={'operation_timeout': 10})
