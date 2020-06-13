# Copyright 2015 Cloudbase Solutions Srl
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys

from eventlet import patcher
import pbr.version

from os_win.utils.winapi import libs as w_libs


__version__ = pbr.version.VersionInfo(
    'os_win').version_string()

if sys.platform == 'win32':
    import wmi
    # We need to make sure that WMI uses the unpatched threading module.
    wmi.threading = patcher.original('threading')

    # The following will set the argument and return value types for the
    # foreign functions used throughout os_win using ctypes.
    w_libs.register()
