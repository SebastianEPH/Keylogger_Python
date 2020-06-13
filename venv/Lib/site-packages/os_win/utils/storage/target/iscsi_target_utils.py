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

from oslo_log import log as logging
import six

from os_win._i18n import _
from os_win import _utils
from os_win import constants
from os_win import exceptions
from os_win.utils import baseutils
from os_win.utils import hostutils
from os_win.utils import pathutils
from os_win.utils import win32utils

LOG = logging.getLogger(__name__)


@six.add_metaclass(baseutils.SynchronizedMeta)
class ISCSITargetUtils(baseutils.BaseUtils):
    ID_METHOD_DNS_NAME = 1
    ID_METHOD_IPV4_ADDR = 2
    ID_METHOD_MAC_ADDR = 3
    ID_METHOD_IQN = 4
    ID_METHOD_IPV6_ADDR = 5

    _ERR_FILE_EXISTS = 80

    def __init__(self):
        self._conn_wmi = self._get_wmi_conn('//./root/wmi')
        self._ensure_wt_provider_available()

        self._pathutils = pathutils.PathUtils()
        self._hostutils = hostutils.HostUtils()
        self._win32utils = win32utils.Win32Utils()

        self._win_gteq_6_3 = self._hostutils.check_min_windows_version(6, 3)

    def _ensure_wt_provider_available(self):
        try:
            self._conn_wmi.WT_Portal
        except AttributeError:
            err_msg = _("The Windows iSCSI target provider is not available.")
            raise exceptions.ISCSITargetException(err_msg)

    def get_supported_disk_format(self):
        return (constants.DISK_FORMAT_VHDX
                if self._win_gteq_6_3 else constants.DISK_FORMAT_VHD)

    def get_supported_vhd_type(self):
        return (constants.VHD_TYPE_DYNAMIC
                if self._win_gteq_6_3 else constants.VHD_TYPE_FIXED)

    def get_portal_locations(self, available_only=True,
                             fail_if_none_found=True):
        wt_portals = self._conn_wmi.WT_Portal()

        if available_only:
            wt_portals = list(filter(lambda portal: portal.Listen, wt_portals))

        if not wt_portals and fail_if_none_found:
            err_msg = _("No valid iSCSI portal was found.")
            raise exceptions.ISCSITargetException(err_msg)

        portal_locations = [self._get_portal_location(portal)
                            for portal in wt_portals]
        return portal_locations

    def _get_portal_location(self, wt_portal):
        return '%s:%s' % (wt_portal.Address, wt_portal.Port)

    def _get_wt_host(self, target_name, fail_if_not_found=True):
        hosts = self._conn_wmi.WT_Host(HostName=target_name)

        if hosts:
            return hosts[0]
        elif fail_if_not_found:
            err_msg = _('Could not find iSCSI target %s')
            raise exceptions.ISCSITargetException(err_msg % target_name)

    def _get_wt_disk(self, description, fail_if_not_found=True):
        # We can retrieve WT Disks only by description.
        wt_disks = self._conn_wmi.WT_Disk(Description=description)
        if wt_disks:
            return wt_disks[0]
        elif fail_if_not_found:
            err_msg = _('Could not find WT Disk: %s')
            raise exceptions.ISCSITargetException(err_msg % description)

    def _get_wt_snapshot(self, description, fail_if_not_found=True):
        wt_snapshots = self._conn_wmi.WT_Snapshot(Description=description)
        if wt_snapshots:
            return wt_snapshots[0]
        elif fail_if_not_found:
            err_msg = _('Could not find WT Snapshot: %s')
            raise exceptions.ISCSITargetException(err_msg % description)

    def _get_wt_idmethod(self, initiator, target_name):
        wt_idmethod = self._conn_wmi.WT_IDMethod(HostName=target_name,
                                                 Value=initiator)
        if wt_idmethod:
            return wt_idmethod[0]

    def create_iscsi_target(self, target_name, fail_if_exists=False):
        """Creates ISCSI target."""
        try:
            self._conn_wmi.WT_Host.NewHost(HostName=target_name)
        except exceptions.x_wmi as wmi_exc:
            err_code = _utils.get_com_error_code(wmi_exc.com_error)
            target_exists = err_code == self._ERR_FILE_EXISTS

            if not target_exists or fail_if_exists:
                err_msg = _('Failed to create iSCSI target: %s.')
                raise exceptions.ISCSITargetWMIException(err_msg % target_name,
                                                         wmi_exc=wmi_exc)
            else:
                LOG.info('The iSCSI target %s already exists.',
                         target_name)

    def delete_iscsi_target(self, target_name):
        """Removes ISCSI target."""
        try:
            wt_host = self._get_wt_host(target_name, fail_if_not_found=False)
            if not wt_host:
                LOG.debug('Skipping deleting target %s as it does not '
                          'exist.', target_name)
                return
            wt_host.RemoveAllWTDisks()
            wt_host.Delete_()
        except exceptions.x_wmi as wmi_exc:
            err_msg = _("Failed to delete ISCSI target %s")
            raise exceptions.ISCSITargetWMIException(err_msg % target_name,
                                                     wmi_exc=wmi_exc)

    def iscsi_target_exists(self, target_name):
        wt_host = self._get_wt_host(target_name, fail_if_not_found=False)
        return wt_host is not None

    def get_target_information(self, target_name):
        wt_host = self._get_wt_host(target_name)

        info = {}
        info['target_iqn'] = wt_host.TargetIQN
        info['enabled'] = wt_host.Enabled
        info['connected'] = bool(wt_host.Status)

        # Note(lpetrut): Cinder uses only one-way CHAP authentication.
        if wt_host.EnableCHAP:
            info['auth_method'] = 'CHAP'
            info['auth_username'] = wt_host.CHAPUserName
            info['auth_password'] = wt_host.CHAPSecret

        return info

    def set_chap_credentials(self, target_name, chap_username, chap_password):
        try:
            wt_host = self._get_wt_host(target_name)
            wt_host.EnableCHAP = True
            wt_host.CHAPUserName = chap_username
            wt_host.CHAPSecret = chap_password
            wt_host.put()
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Failed to set CHAP credentials on target %s.')
            raise exceptions.ISCSITargetWMIException(err_msg % target_name,
                                                     wmi_exc=wmi_exc)

    def associate_initiator_with_iscsi_target(self, initiator,
                                              target_name,
                                              id_method=ID_METHOD_IQN):
        wt_idmethod = self._get_wt_idmethod(initiator, target_name)
        if wt_idmethod:
            return

        try:
            wt_idmethod = self._conn_wmi.WT_IDMethod.new()
            wt_idmethod.HostName = target_name
            wt_idmethod.Method = id_method
            wt_idmethod.Value = initiator
            wt_idmethod.put()
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Could not associate initiator %(initiator)s to '
                        'iSCSI target: %(target_name)s.')
            raise exceptions.ISCSITargetWMIException(
                err_msg % dict(initiator=initiator,
                               target_name=target_name),
                wmi_exc=wmi_exc)

    def deassociate_initiator(self, initiator, target_name):
        try:
            wt_idmethod = self._get_wt_idmethod(initiator, target_name)
            if wt_idmethod:
                wt_idmethod.Delete_()
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Could not deassociate initiator %(initiator)s from '
                        'iSCSI target: %(target_name)s.')
            raise exceptions.ISCSITargetWMIException(
                err_msg % dict(initiator=initiator,
                               target_name=target_name),
                wmi_exc=wmi_exc)

    def create_wt_disk(self, vhd_path, wtd_name, size_mb=None):
        try:
            self._conn_wmi.WT_Disk.NewWTDisk(DevicePath=vhd_path,
                                             Description=wtd_name,
                                             SizeInMB=size_mb)
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Failed to create WT Disk. '
                        'VHD path: %(vhd_path)s '
                        'WT disk name: %(wtd_name)s')
            raise exceptions.ISCSITargetWMIException(
                err_msg % dict(vhd_path=vhd_path,
                               wtd_name=wtd_name),
                wmi_exc=wmi_exc)

    def import_wt_disk(self, vhd_path, wtd_name):
        """Import a vhd/x image to be used by Windows iSCSI targets."""
        try:
            self._conn_wmi.WT_Disk.ImportWTDisk(DevicePath=vhd_path,
                                                Description=wtd_name)
        except exceptions.x_wmi as wmi_exc:
            err_msg = _("Failed to import WT disk: %s.")
            raise exceptions.ISCSITargetWMIException(err_msg % vhd_path,
                                                     wmi_exc=wmi_exc)

    def change_wt_disk_status(self, wtd_name, enabled):
        try:
            wt_disk = self._get_wt_disk(wtd_name)
            wt_disk.Enabled = enabled
            wt_disk.put()
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Could not change disk status. WT Disk name: %s')
            raise exceptions.ISCSITargetWMIException(err_msg % wtd_name,
                                                     wmi_exc=wmi_exc)

    def remove_wt_disk(self, wtd_name):
        try:
            wt_disk = self._get_wt_disk(wtd_name, fail_if_not_found=False)
            if wt_disk:
                wt_disk.Delete_()
        except exceptions.x_wmi as wmi_exc:
            err_msg = _("Failed to remove WT disk: %s.")
            raise exceptions.ISCSITargetWMIException(err_msg % wtd_name,
                                                     wmi_exc=wmi_exc)

    def extend_wt_disk(self, wtd_name, additional_mb):
        try:
            wt_disk = self._get_wt_disk(wtd_name)
            wt_disk.Extend(additional_mb)
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Could not extend WT Disk %(wtd_name)s '
                        'with additional %(additional_mb)s MB.')
            raise exceptions.ISCSITargetWMIException(
                err_msg % dict(wtd_name=wtd_name,
                               additional_mb=additional_mb),
                wmi_exc=wmi_exc)

    def add_disk_to_target(self, wtd_name, target_name):
        """Adds the disk to the target."""
        try:
            wt_disk = self._get_wt_disk(wtd_name)
            wt_host = self._get_wt_host(target_name)
            wt_host.AddWTDisk(wt_disk.WTD)
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Could not add WTD Disk %(wtd_name)s to '
                        'iSCSI target %(target_name)s.')
            raise exceptions.ISCSITargetWMIException(
                err_msg % dict(wtd_name=wtd_name,
                               target_name=target_name),
                wmi_exc=wmi_exc)

    def create_snapshot(self, wtd_name, snapshot_name):
        """Driver entry point for creating a snapshot."""
        try:
            wt_disk = self._get_wt_disk(wtd_name)
            snap_id = self._conn_wmi.WT_Snapshot.Create(WTD=wt_disk.WTD)[0]

            wt_snap = self._conn_wmi.WT_Snapshot(Id=snap_id)[0]
            wt_snap.Description = snapshot_name
            wt_snap.put()
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Failed to create snapshot. '
                        'WT Disk name: %(wtd_name)s '
                        'Snapshot name: %(snapshot_name)s')
            raise exceptions.ISCSITargetWMIException(
                err_msg % dict(wtd_name=wtd_name,
                               snapshot_name=snapshot_name),
                wmi_exc=wmi_exc)

    def export_snapshot(self, snapshot_name, dest_path):
        """Driver entry point for exporting snapshots as volumes."""
        try:
            wt_snap = self._get_wt_snapshot(snapshot_name)
            wt_disk_id = wt_snap.Export()[0]
            # This export is a read-only shadow copy, needing to be copied
            # to another disk.
            wt_disk = self._conn_wmi.WT_Disk(WTD=wt_disk_id)[0]
            wt_disk.Description = '%s-%s-temp' % (snapshot_name, wt_disk_id)
            wt_disk.put()
            src_path = wt_disk.DevicePath

            self._pathutils.copy(src_path, dest_path)

            wt_disk.Delete_()
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Failed to export snapshot %(snapshot_name)s '
                        'to %(dest_path)s.')
            raise exceptions.ISCSITargetWMIException(
                err_msg % dict(snapshot_name=snapshot_name,
                               dest_path=dest_path),
                wmi_exc=wmi_exc)

    def delete_snapshot(self, snapshot_name):
        """Driver entry point for deleting a snapshot."""
        try:
            wt_snapshot = self._get_wt_snapshot(snapshot_name,
                                                fail_if_not_found=False)
            if wt_snapshot:
                wt_snapshot.Delete_()
        except exceptions.x_wmi as wmi_exc:
            err_msg = _('Failed delete snapshot %s.')
            raise exceptions.ISCSITargetWMIException(err_msg % snapshot_name,
                                                     wmi_exc=wmi_exc)
