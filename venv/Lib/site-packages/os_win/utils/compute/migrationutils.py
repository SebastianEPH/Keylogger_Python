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

from oslo_log import log as logging

from os_win._i18n import _
from os_win import constants
from os_win import exceptions
from os_win.utils import baseutils
from os_win.utils.compute import vmutils
from os_win.utils import jobutils

LOG = logging.getLogger(__name__)


class MigrationUtils(baseutils.BaseUtilsVirt):

    def __init__(self):
        super(MigrationUtils, self).__init__()
        self._vmutils = vmutils.VMUtils()
        self._jobutils = jobutils.JobUtils()

    def _get_export_setting_data(self, vm_name):
        vm = self._vmutils._lookup_vm(vm_name)
        export_sd = self._compat_conn.Msvm_VirtualSystemExportSettingData(
            InstanceID=vm.InstanceID)
        return export_sd[0]

    def export_vm(self, vm_name, export_path,
                  copy_snapshots_config=constants.EXPORT_CONFIG_SNAPSHOTS_ALL,
                  copy_vm_storage=False, create_export_subdir=False):
        vm = self._vmutils._lookup_vm(vm_name)
        export_setting_data = self._get_export_setting_data(vm_name)

        export_setting_data.CopySnapshotConfiguration = copy_snapshots_config
        export_setting_data.CopyVmStorage = copy_vm_storage
        export_setting_data.CreateVmExportSubdirectory = create_export_subdir

        (job_path, ret_val) = self._vs_man_svc.ExportSystemDefinition(
            ComputerSystem=vm.path_(),
            ExportDirectory=export_path,
            ExportSettingData=export_setting_data.GetText_(1))
        self._jobutils.check_ret_val(ret_val, job_path)

    def import_vm_definition(self, export_config_file_path,
                             snapshot_folder_path,
                             new_uuid=False):
        (ref, job_path, ret_val) = self._vs_man_svc.ImportSystemDefinition(
            new_uuid, snapshot_folder_path, export_config_file_path)
        self._jobutils.check_ret_val(ret_val, job_path)

    def realize_vm(self, vm_name):
        planned_vm = self._get_planned_vm(vm_name, fail_if_not_found=True)

        if planned_vm:
            (job_path, ret_val) = (
                self._vs_man_svc.ValidatePlannedSystem(planned_vm.path_()))
            self._jobutils.check_ret_val(ret_val, job_path)
            (job_path, ref, ret_val) = (
                self._vs_man_svc.RealizePlannedSystem(planned_vm.path_()))
            self._jobutils.check_ret_val(ret_val, job_path)

    def _get_planned_vm(self, vm_name, conn_v2=None, fail_if_not_found=False):
        if not conn_v2:
            conn_v2 = self._conn
        planned_vm = conn_v2.Msvm_PlannedComputerSystem(ElementName=vm_name)
        if planned_vm:
            return planned_vm[0]
        elif fail_if_not_found:
            raise exceptions.HyperVException(
                _('Cannot find planned VM with name: %s') % vm_name)
        return None

    def planned_vm_exists(self, vm_name):
        """Checks if the Planned VM with the given name exists on the host."""
        return self._get_planned_vm(vm_name) is not None

    def _destroy_planned_vm(self, planned_vm):
        LOG.debug("Destroying existing planned VM: %s",
                  planned_vm.ElementName)
        (job_path,
         ret_val) = self._vs_man_svc.DestroySystem(planned_vm.path_())
        self._jobutils.check_ret_val(ret_val, job_path)

    def destroy_existing_planned_vm(self, vm_name):
        planned_vm = self._get_planned_vm(vm_name, self._compat_conn)
        if planned_vm:
            self._destroy_planned_vm(planned_vm)
