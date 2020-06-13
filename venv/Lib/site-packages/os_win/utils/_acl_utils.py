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

import ctypes

from os_win.utils import win32utils
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi import libs as w_lib

advapi32 = w_lib.get_shared_lib_handle(w_lib.ADVAPI32)


class ACLUtils(object):
    def __init__(self):
        self._win32_utils = win32utils.Win32Utils()

    @staticmethod
    def _get_void_pp():
        return ctypes.pointer(ctypes.c_void_p())

    def get_named_security_info(self, obj_name, obj_type, security_info_flags):
        """Retrieve object security information.

        :param security_info_flags: specifies which information will
                                   be retrieved.
        :param ret_val: dict, containing pointers to the requested structures.
                        Note that the returned security descriptor will have
                        to be freed using LocalFree.
                        Some requested information may not be present, in
                        which case the according pointers will be NULL.
        """
        sec_info = {}

        if security_info_flags & w_const.OWNER_SECURITY_INFORMATION:
            sec_info['pp_sid_owner'] = self._get_void_pp()
        if security_info_flags & w_const.GROUP_SECURITY_INFORMATION:
            sec_info['pp_sid_group'] = self._get_void_pp()
        if security_info_flags & w_const.DACL_SECURITY_INFORMATION:
            sec_info['pp_dacl'] = self._get_void_pp()
        if security_info_flags & w_const.SACL_SECURITY_INFORMATION:
            sec_info['pp_sacl'] = self._get_void_pp()
        sec_info['pp_sec_desc'] = self._get_void_pp()

        self._win32_utils.run_and_check_output(
            advapi32.GetNamedSecurityInfoW,
            ctypes.c_wchar_p(obj_name),
            obj_type,
            security_info_flags,
            sec_info.get('pp_sid_owner'),
            sec_info.get('pp_sid_group'),
            sec_info.get('pp_dacl'),
            sec_info.get('pp_sacl'),
            sec_info['pp_sec_desc'])

        return sec_info

    def set_entries_in_acl(self, entry_count, p_explicit_entry_list,
                           p_old_acl):
        """Merge new ACEs into an existing ACL, returning a new ACL."""
        pp_new_acl = self._get_void_pp()

        self._win32_utils.run_and_check_output(
            advapi32.SetEntriesInAclW,
            entry_count,
            p_explicit_entry_list,
            p_old_acl,
            pp_new_acl)

        return pp_new_acl

    def set_named_security_info(self, obj_name, obj_type, security_info_flags,
                                p_sid_owner=None, p_sid_group=None,
                                p_dacl=None, p_sacl=None):
        self._win32_utils.run_and_check_output(
            advapi32.SetNamedSecurityInfoW,
            ctypes.c_wchar_p(obj_name),
            obj_type,
            security_info_flags,
            p_sid_owner,
            p_sid_group,
            p_dacl,
            p_sacl)
