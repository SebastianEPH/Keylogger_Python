# Copyright 2015 Cloudbase Solutions Srl
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
import socket

from oslo_log import log as logging

from os_win._i18n import _
from os_win import _utils
from os_win import exceptions
from os_win.utils import baseutils
from os_win.utils import win32utils

LOG = logging.getLogger(__name__)


class SMBUtils(baseutils.BaseUtils):
    _loopback_share_map = {}

    def __init__(self):
        self._win32_utils = win32utils.Win32Utils()
        self._smb_conn = self._get_wmi_conn(r"root\Microsoft\Windows\SMB")

    def check_smb_mapping(self, share_path, remove_unavailable_mapping=False):
        mappings = self._smb_conn.Msft_SmbMapping(RemotePath=share_path)

        if not mappings:
            return False

        if os.path.exists(share_path):
            LOG.debug('Share already mounted: %s', share_path)
            return True
        else:
            LOG.debug('Share exists but is unavailable: %s ', share_path)
            if remove_unavailable_mapping:
                self.unmount_smb_share(share_path, force=True)
            return False

    def mount_smb_share(self, share_path, username=None, password=None):
        try:
            LOG.debug('Mounting share: %s', share_path)
            self._smb_conn.Msft_SmbMapping.Create(RemotePath=share_path,
                                                  UserName=username,
                                                  Password=password)
        except exceptions.x_wmi as exc:
            err_msg = (_(
                'Unable to mount SMBFS share: %(share_path)s '
                'WMI exception: %(wmi_exc)s') % {'share_path': share_path,
                                                 'wmi_exc': exc})
            raise exceptions.SMBException(err_msg)

    def unmount_smb_share(self, share_path, force=False):
        mappings = self._smb_conn.Msft_SmbMapping(RemotePath=share_path)
        if not mappings:
            LOG.debug('Share %s is not mounted. Skipping unmount.',
                      share_path)

        for mapping in mappings:
            # Due to a bug in the WMI module, getting the output of
            # methods returning None will raise an AttributeError
            try:
                mapping.Remove(Force=force)
            except AttributeError:
                pass
            except exceptions.x_wmi:
                # If this fails, a 'Generic Failure' exception is raised.
                # This happens even if we unforcefully unmount an in-use
                # share, for which reason we'll simply ignore it in this
                # case.
                if force:
                    raise exceptions.SMBException(
                        _("Could not unmount share: %s") % share_path)

    def get_smb_share_path(self, share_name):
        shares = self._smb_conn.Msft_SmbShare(Name=share_name)
        share_path = shares[0].Path if shares else None
        if not shares:
            LOG.debug("Could not find any local share named %s.", share_name)
        return share_path

    def is_local_share(self, share_path):
        # In case of Scale-Out File Servers, we'll get the Distributed Node
        # Name of the share. We have to check whether this resolves to a
        # local ip, which would happen in a hyper converged scenario.
        #
        # In this case, mounting the share is not supported and we have to
        # use the local share path.
        if share_path in self._loopback_share_map:
            return self._loopback_share_map[share_path]

        addr = share_path.lstrip('\\').split('\\', 1)[0]

        local_ips = _utils.get_ips(socket.gethostname())
        local_ips += _utils.get_ips('localhost')

        dest_ips = _utils.get_ips(addr)
        is_local = bool(set(local_ips).intersection(set(dest_ips)))

        self._loopback_share_map[share_path] = is_local
        return is_local
