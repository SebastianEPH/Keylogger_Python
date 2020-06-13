# Copyright 2016 Cloudbase Solutions Srl
#
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
"""
Utility class for metrics related operations.
Based on the "root/virtualization/v2" namespace available starting with
Hyper-V Server / Windows Server 2012.
"""

from oslo_log import log as logging

from os_win._i18n import _
from os_win import exceptions
from os_win.utils import _wqlutils
from os_win.utils import baseutils

LOG = logging.getLogger(__name__)


class MetricsUtils(baseutils.BaseUtilsVirt):

    _VIRTUAL_SYSTEM_TYPE_REALIZED = 'Microsoft:Hyper-V:System:Realized'
    _DVD_DISK_RES_SUB_TYPE = 'Microsoft:Hyper-V:Virtual CD/DVD Disk'
    _STORAGE_ALLOC_SETTING_DATA_CLASS = 'Msvm_StorageAllocationSettingData'
    _PROCESSOR_SETTING_DATA_CLASS = 'Msvm_ProcessorSettingData'
    _SYNTH_ETH_PORT_SET_DATA = 'Msvm_SyntheticEthernetPortSettingData'
    _PORT_ALLOC_SET_DATA = 'Msvm_EthernetPortAllocationSettingData'
    _PORT_ALLOC_ACL_SET_DATA = 'Msvm_EthernetSwitchPortAclSettingData'
    _BASE_METRICS_VALUE = 'Msvm_BaseMetricValue'

    _CPU_METRICS = 'Aggregated Average CPU Utilization'
    _MEMORY_METRICS = 'Aggregated Average Memory Utilization'
    _NET_IN_METRICS = 'Filtered Incoming Network Traffic'
    _NET_OUT_METRICS = 'Filtered Outgoing Network Traffic'
    # Disk metrics are supported from Hyper-V 2012 R2
    _DISK_RD_METRICS = 'Disk Data Read'
    _DISK_WR_METRICS = 'Disk Data Written'
    _DISK_LATENCY_METRICS = 'Average Disk Latency'
    _DISK_IOPS_METRICS = 'Average Normalized Disk Throughput'

    _METRICS_ENABLED = 2

    def __init__(self, host='.'):
        super(MetricsUtils, self).__init__(host)
        self._metrics_svc_obj = None
        self._metrics_defs_obj = {}

        # We need to avoid a circular dependency.
        from os_win import utilsfactory
        self._vmutils = utilsfactory.get_vmutils(host)

    @property
    def _metrics_svc(self):
        if not self._metrics_svc_obj:
            self._metrics_svc_obj = self._compat_conn.Msvm_MetricService()[0]
        return self._metrics_svc_obj

    @property
    def _metrics_defs(self):
        if not self._metrics_defs_obj:
            self._cache_metrics_defs()
        return self._metrics_defs_obj

    def _cache_metrics_defs(self):
        for metrics_def in self._conn.CIM_BaseMetricDefinition():
            self._metrics_defs_obj[metrics_def.ElementName] = metrics_def

    def enable_vm_metrics_collection(self, vm_name):
        vm = self._get_vm(vm_name)
        disks = self._get_vm_resources(vm_name,
                                       self._STORAGE_ALLOC_SETTING_DATA_CLASS)
        filtered_disks = [d for d in disks if
                          d.ResourceSubType != self._DVD_DISK_RES_SUB_TYPE]

        # enable metrics for disk.
        for disk in filtered_disks:
            self._enable_metrics(disk)

        metrics_names = [self._CPU_METRICS, self._MEMORY_METRICS]
        self._enable_metrics(vm, metrics_names)

    def enable_disk_metrics_collection(self, attached_disk_path=None,
                                       is_physical=False,
                                       serial=None):
        disk = self._vmutils._get_mounted_disk_resource_from_path(
            attached_disk_path, is_physical=is_physical, serial=serial)
        self._enable_metrics(disk)

    def enable_port_metrics_collection(self, switch_port_name):
        port = self._get_switch_port(switch_port_name)
        metrics_names = [self._NET_IN_METRICS, self._NET_OUT_METRICS]
        self._enable_metrics(port, metrics_names)

    def _enable_metrics(self, element, metrics_names=None):
        if not metrics_names:
            definition_paths = [None]
        else:
            definition_paths = []
            for metrics_name in metrics_names:
                metrics_def = self._metrics_defs.get(metrics_name)
                if not metrics_def:
                    LOG.warning("Metric not found: %s", metrics_name)
                    continue
                definition_paths.append(metrics_def.path_())

        element_path = element.path_()
        for definition_path in definition_paths:
            ret_val = self._metrics_svc.ControlMetrics(
                Subject=element_path,
                Definition=definition_path,
                MetricCollectionEnabled=self._METRICS_ENABLED)[0]
            if ret_val:
                err_msg = _("Failed to enable metrics for resource "
                            "%(resource_name)s. "
                            "Return code: %(ret_val)s.") % dict(
                                resource_name=element.ElementName,
                                ret_val=ret_val)
                raise exceptions.OSWinException(err_msg)

    def get_cpu_metrics(self, vm_name):
        vm = self._get_vm(vm_name)
        cpu_sd = self._get_vm_resources(vm_name,
                                        self._PROCESSOR_SETTING_DATA_CLASS)[0]
        cpu_metrics_def = self._metrics_defs[self._CPU_METRICS]
        cpu_metrics_aggr = self._get_metrics(vm, cpu_metrics_def)

        cpu_used = 0
        if cpu_metrics_aggr:
            cpu_used = int(cpu_metrics_aggr[0].MetricValue)

        return (cpu_used,
                int(cpu_sd.VirtualQuantity),
                int(vm.OnTimeInMilliseconds))

    def get_memory_metrics(self, vm_name):
        vm = self._get_vm(vm_name)
        memory_def = self._metrics_defs[self._MEMORY_METRICS]
        metrics_memory = self._get_metrics(vm, memory_def)
        memory_usage = 0
        if metrics_memory:
            memory_usage = int(metrics_memory[0].MetricValue)
        return memory_usage

    def get_vnic_metrics(self, vm_name):
        ports = self._get_vm_resources(vm_name, self._PORT_ALLOC_SET_DATA)
        vnics = self._get_vm_resources(vm_name, self._SYNTH_ETH_PORT_SET_DATA)

        metrics_def_in = self._metrics_defs[self._NET_IN_METRICS]
        metrics_def_out = self._metrics_defs[self._NET_OUT_METRICS]

        for port in ports:
            vnic = [v for v in vnics if port.Parent == v.path_()][0]
            port_acls = _wqlutils.get_element_associated_class(
                self._conn, self._PORT_ALLOC_ACL_SET_DATA,
                element_instance_id=port.InstanceID)

            metrics_value_instances = self._get_metrics_value_instances(
                port_acls, self._BASE_METRICS_VALUE)
            metrics_values = self._sum_metrics_values_by_defs(
                metrics_value_instances, [metrics_def_in, metrics_def_out])

            yield {
                'rx_mb': metrics_values[0],
                'tx_mb': metrics_values[1],
                'element_name': vnic.ElementName,
                'address': vnic.Address
            }

    def get_disk_metrics(self, vm_name):
        metrics_def_r = self._metrics_defs[self._DISK_RD_METRICS]
        metrics_def_w = self._metrics_defs[self._DISK_WR_METRICS]

        disks = self._get_vm_resources(vm_name,
                                       self._STORAGE_ALLOC_SETTING_DATA_CLASS)
        for disk in disks:
            metrics_values = self._get_metrics_values(
                disk, [metrics_def_r, metrics_def_w])

            yield {
                # Values are in megabytes
                'read_mb': metrics_values[0],
                'write_mb': metrics_values[1],
                'instance_id': disk.InstanceID,
                'host_resource': disk.HostResource[0]
            }

    def get_disk_latency_metrics(self, vm_name):
        metrics_latency_def = self._metrics_defs[self._DISK_LATENCY_METRICS]

        disks = self._get_vm_resources(vm_name,
                                       self._STORAGE_ALLOC_SETTING_DATA_CLASS)
        for disk in disks:
            metrics_values = self._get_metrics_values(
                disk, [metrics_latency_def])

            yield {
                'disk_latency': metrics_values[0],
                'instance_id': disk.InstanceID,
            }

    def get_disk_iops_count(self, vm_name):
        metrics_def_iops = self._metrics_defs[self._DISK_IOPS_METRICS]

        disks = self._get_vm_resources(vm_name,
                                       self._STORAGE_ALLOC_SETTING_DATA_CLASS)
        for disk in disks:
            metrics_values = self._get_metrics_values(
                disk, [metrics_def_iops])

            yield {
                'iops_count': metrics_values[0],
                'instance_id': disk.InstanceID,
            }

    @staticmethod
    def _sum_metrics_values(metrics):
        return sum([int(metric.MetricValue) for metric in metrics])

    def _sum_metrics_values_by_defs(self, element_metrics, metrics_defs):
        metrics_values = []
        for metrics_def in metrics_defs:
            if metrics_def:
                metrics = self._filter_metrics(element_metrics, metrics_def)
                metrics_values.append(self._sum_metrics_values(metrics))
            else:
                # In case the metric is not defined on this host
                metrics_values.append(0)
        return metrics_values

    def _get_metrics_value_instances(self, elements, result_class):
        instances = []
        for el in elements:
            # NOTE(abalutoiu): Msvm_MetricForME is the association between
            # an element and all the metric values maintained for it.
            el_metric = [
                x.Dependent for x in self._conn.Msvm_MetricForME(
                    Antecedent=el.path_())]
            el_metric = [
                x for x in el_metric if x.path().Class == result_class]
            if el_metric:
                instances.append(el_metric[0])

        return instances

    def _get_metrics_values(self, element, metrics_defs):
        element_metrics = [
            x.Dependent for x in self._conn.Msvm_MetricForME(
                Antecedent=element.path_())]
        return self._sum_metrics_values_by_defs(element_metrics, metrics_defs)

    def _get_metrics(self, element, metrics_def):
        metrics = [
            x.Dependent for x in self._conn.Msvm_MetricForME(
                Antecedent=element.path_())]
        return self._filter_metrics(metrics, metrics_def)

    @staticmethod
    def _filter_metrics(all_metrics, metrics_def):
        return [v for v in all_metrics if
                v.MetricDefinitionId == metrics_def.Id]

    def _get_vm_resources(self, vm_name, resource_class):
        setting_data = self._get_vm_setting_data(vm_name)
        return _wqlutils.get_element_associated_class(
            self._conn, resource_class,
            element_instance_id=setting_data.InstanceID)

    def _get_vm(self, vm_name):
        vms = self._conn.Msvm_ComputerSystem(ElementName=vm_name)
        return self._unique_result(vms, vm_name)

    def _get_switch_port(self, port_name):
        ports = self._conn.Msvm_EthernetPortAllocationSettingData(
            ElementName=port_name)
        return self._unique_result(ports, port_name)

    def _get_vm_setting_data(self, vm_name):
        vssds = self._conn.Msvm_VirtualSystemSettingData(
            ElementName=vm_name)
        return self._unique_result(vssds, vm_name)

    @staticmethod
    def _unique_result(objects, resource_name):
        n = len(objects)
        if n == 0:
            raise exceptions.NotFound(resource=resource_name)
        elif n > 1:
            raise exceptions.OSWinException(
                _('Duplicate resource name found: %s') % resource_name)
        else:
            return objects[0]
