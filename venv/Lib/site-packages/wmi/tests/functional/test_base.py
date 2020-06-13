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
import functools
import tempfile

import testtools

import wmi


class BaseFunctionalTestCase(testtools.TestCase):
    _storage_namespace = 'root/microsoft/windows/storage'

    def setUp(self):
        super(BaseFunctionalTestCase, self).setUp()
        self._conn_cimv2 = wmi.WMI()
        self._conn_storage = wmi.WMI(moniker=self._storage_namespace)

    @staticmethod
    def pass_temp_file(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                (fd, tmp_path) = tempfile.mkstemp(suffix='pymi-test')
                os.close(fd)
                # This will behave similar to the mock.patch decorator.
                args += (tmp_path, )
                return f(*args, **kwargs)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        return wrapper
