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

import mock

from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import _wqlutils


class WqlUtilsTestCase(test_base.OsWinBaseTestCase):
    def _test_get_element_associated_class(self, fields=None):
        mock_conn = mock.MagicMock()
        _wqlutils.get_element_associated_class(
            mock_conn, mock.sentinel.class_name,
            element_instance_id=mock.sentinel.instance_id,
            fields=fields)

        expected_fields = ", ".join(fields) if fields else '*'
        expected_query = (
            "SELECT %(expected_fields)s FROM %(class_name)s "
            "WHERE InstanceID LIKE '%(instance_id)s%%'" %
            {'expected_fields': expected_fields,
             'class_name': mock.sentinel.class_name,
             'instance_id': mock.sentinel.instance_id})
        mock_conn.query.assert_called_once_with(expected_query)

    def test_get_element_associated_class(self):
        self._test_get_element_associated_class()

    def test_get_element_associated_class_specific_fields(self):
        self._test_get_element_associated_class(
            fields=['field', 'another_field'])

    def test_get_element_associated_class_invalid_element(self):
        self.assertRaises(
            exceptions.WqlException,
            _wqlutils.get_element_associated_class,
            mock.sentinel.conn,
            mock.sentinel.class_name)
