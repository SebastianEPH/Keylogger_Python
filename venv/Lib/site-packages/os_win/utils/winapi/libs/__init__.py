# Copyright 2017 Cloudbase Solutions Srl
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

import importlib

from os_win._i18n import _
from os_win import exceptions


ADVAPI32 = 'advapi32'
CLUSAPI = 'clusapi'
HBAAPI = 'hbaapi'
ISCSIDSC = 'iscsidsc'
KERNEL32 = 'kernel32'
VIRTDISK = 'virtdisk'

libs = [ADVAPI32, CLUSAPI, HBAAPI, ISCSIDSC, KERNEL32, VIRTDISK]


def _get_shared_lib_module(lib_name):
    if lib_name not in libs:
        err_msg = _("Unsupported library: %s.")
        raise exceptions.OSWinException(err_msg % lib_name)

    module = importlib.import_module('os_win.utils.winapi.libs.%s' % lib_name)
    return module


def register():
    for lib_name in libs:
        module = _get_shared_lib_module(lib_name)
        module.register()


def get_shared_lib_handle(lib_name):
    module = _get_shared_lib_module(lib_name)
    return module.lib_handle
