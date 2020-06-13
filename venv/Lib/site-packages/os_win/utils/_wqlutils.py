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

from os_win._i18n import _
from os_win import exceptions


def get_element_associated_class(conn, class_name, element_instance_id=None,
                                 element_uuid=None, fields=None):
    """Returns the objects associated to an element as a list.

    :param conn: connection to be used to execute the query
    :param class_name: object's class type name to be retrieved
    :param element_instance_id: element class InstanceID
    :param element_uuid: UUID of the element
    :param fields: specific class attributes to be retrieved
    """
    if element_instance_id:
        instance_id = element_instance_id
    elif element_uuid:
        instance_id = "Microsoft:%s" % element_uuid
    else:
        err_msg = _("Could not get element associated class. Either element "
                    "instance id or element uuid must be specified.")
        raise exceptions.WqlException(err_msg)
    fields = ", ".join(fields) if fields else "*"
    return conn.query(
        "SELECT %(fields)s FROM %(class_name)s WHERE InstanceID "
        "LIKE '%(instance_id)s%%'" % {
            'fields': fields,
            'class_name': class_name,
            'instance_id': instance_id})
