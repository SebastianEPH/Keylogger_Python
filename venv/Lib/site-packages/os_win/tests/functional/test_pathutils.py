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
import re
import tempfile

from os_win import _utils
from os_win import constants
from os_win.tests.functional import test_base
from os_win import utilsfactory


class PathUtilsTestCase(test_base.OsWinBaseFunctionalTestCase):
    def setUp(self):
        super(PathUtilsTestCase, self).setUp()
        self._pathutils = utilsfactory.get_pathutils()

    def _get_raw_icacls_info(self, path):
        return _utils.execute("icacls.exe", path)[0]

    def _assert_contains_ace(self, path, access_to, access_flags):
        raw_out = self._get_raw_icacls_info(path)

        # The flags will be matched regardless of
        # other flags and their order.
        escaped_access_flags = access_flags.replace(
            "(", "(?=.*\(").replace(")", r"\))")
        pattern = "%s:%s.*" % (access_to, escaped_access_flags)

        match = re.findall(pattern, raw_out,
                           flags=re.IGNORECASE | re.MULTILINE)
        if not match:
            fail_msg = ("The file does not contain the expected ACL rules. "
                        "Raw icacls output: %s. Expected access rule: %s")
            expected_rule = ":".join([access_to, access_flags])
            self.fail(fail_msg % (raw_out, expected_rule))

    def test_acls(self):
        tmp_suffix = 'oswin-func-test'
        tmp_dir = tempfile.mkdtemp(suffix=tmp_suffix)
        self.addCleanup(self._pathutils.rmtree, tmp_dir)

        tmp_file_paths = []
        for idx in range(2):
            tmp_file_path = os.path.join(tmp_dir,
                                         'tmp_file_%s' % idx)
            with open(tmp_file_path, 'w') as f:
                f.write('test')
            tmp_file_paths.append(tmp_file_path)

        trustee = "NULL SID"
        self._pathutils.add_acl_rule(
            path=tmp_dir,
            trustee_name=trustee,
            access_rights=constants.ACE_GENERIC_READ,
            access_mode=constants.ACE_GRANT_ACCESS,
            inheritance_flags=(constants.ACE_OBJECT_INHERIT |
                               constants.ACE_CONTAINER_INHERIT))
        self._pathutils.add_acl_rule(
            path=tmp_file_paths[0],
            trustee_name=trustee,
            access_rights=constants.ACE_GENERIC_WRITE,
            access_mode=constants.ACE_GRANT_ACCESS)
        self._pathutils.copy_acls(tmp_file_paths[0], tmp_file_paths[1])

        self._assert_contains_ace(tmp_dir, trustee, "(OI)(CI).*(GR)")
        for path in tmp_file_paths:
            self._assert_contains_ace(path, trustee, ("(W,Rc)"))
