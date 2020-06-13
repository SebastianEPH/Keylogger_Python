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

import mock

from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import _wqlutils
from os_win.utils.compute import vmutils
from os_win.utils.metrics import metricsutils
from os_win import utilsfactory


class MetricsUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V MetricsUtils class."""

    _FAKE_RET_VAL = 0
    _FAKE_PORT = "fake's port name"

    _autospec_classes = [
        vmutils.VMUtils,
    ]

    def setUp(self):
        super(MetricsUtilsTestCase, self).setUp()

        mock.patch.object(utilsfactory, 'get_vmutils',
                          mock.Mock(return_value=vmutils.VMUtils)).start()

        self.utils = metricsutils.MetricsUtils()
        self.utils._conn_attr = mock.MagicMock()

    def test_cache_metrics_defs(self):
        mock_metric_def = mock.Mock(ElementName=mock.sentinel.elementname)
        self.utils._conn.CIM_BaseMetricDefinition.return_value = [
            mock_metric_def]
        self.utils._cache_metrics_defs()
        expected_cache_metrics = {mock.sentinel.elementname: mock_metric_def}
        self.assertEqual(expected_cache_metrics, self.utils._metrics_defs_obj)

    @mock.patch.object(metricsutils.MetricsUtils, '_enable_metrics')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm_resources')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm')
    def test_enable_vm_metrics_collection(
            self, mock_get_vm, mock_get_vm_resources, mock_enable_metrics):
        mock_vm = mock_get_vm.return_value
        mock_disk = mock.MagicMock()
        mock_dvd = mock.MagicMock(
            ResourceSubType=self.utils._DVD_DISK_RES_SUB_TYPE)
        mock_get_vm_resources.return_value = [mock_disk, mock_dvd]

        self.utils.enable_vm_metrics_collection(mock.sentinel.vm_name)

        metrics_names = [self.utils._CPU_METRICS,
                         self.utils._MEMORY_METRICS]
        mock_enable_metrics.assert_has_calls(
            [mock.call(mock_disk), mock.call(mock_vm, metrics_names)])

    @mock.patch.object(metricsutils.MetricsUtils, '_enable_metrics')
    def test_enable_disk_metrics_collection(self, mock_enable_metrics):
        mock_get_disk = (
            self.utils._vmutils._get_mounted_disk_resource_from_path)

        self.utils.enable_disk_metrics_collection(
            mock.sentinel.disk_path,
            mock.sentinel.is_physical,
            mock.sentinel.serial)

        mock_get_disk.assert_called_once_with(
            mock.sentinel.disk_path,
            is_physical=mock.sentinel.is_physical,
            serial=mock.sentinel.serial)
        mock_enable_metrics.assert_called_once_with(mock_get_disk.return_value)

    @mock.patch.object(metricsutils.MetricsUtils, '_enable_metrics')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_switch_port')
    def test_enable_switch_port_metrics_collection(self, mock_get_port,
                                                   mock_enable_metrics):
        self.utils.enable_port_metrics_collection(mock.sentinel.port_name)

        mock_get_port.assert_called_once_with(mock.sentinel.port_name)
        metrics = [self.utils._NET_IN_METRICS,
                   self.utils._NET_OUT_METRICS]
        mock_enable_metrics.assert_called_once_with(
            mock_get_port.return_value, metrics)

    def _check_enable_metrics(self, metrics=None, definition=None):
        mock_element = mock.MagicMock()
        self.utils._metrics_svc.ControlMetrics.return_value = [0]

        self.utils._enable_metrics(mock_element, metrics)

        self.utils._metrics_svc.ControlMetrics.assert_called_once_with(
            Subject=mock_element.path_.return_value,
            Definition=definition,
            MetricCollectionEnabled=self.utils._METRICS_ENABLED)

    def test_enable_metrics_no_metrics(self):
        self._check_enable_metrics()

    def test_enable_metrics(self):
        metrics_name = self.utils._CPU_METRICS
        metrics_def = mock.MagicMock()
        self.utils._metrics_defs_obj = {metrics_name: metrics_def}
        self._check_enable_metrics([metrics_name, mock.sentinel.metrics_name],
                                   metrics_def.path_.return_value)

    def test_enable_metrics_exception(self):
        metric_name = self.utils._CPU_METRICS
        metric_def = mock.MagicMock()
        self.utils._metrics_defs_obj = {metric_name: metric_def}

        self.utils._metrics_svc.ControlMetrics.return_value = [1]
        self.assertRaises(exceptions.OSWinException,
                          self.utils._enable_metrics,
                          mock.MagicMock(),
                          [metric_name])

    @mock.patch.object(metricsutils.MetricsUtils, '_get_metrics')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm_resources')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm')
    def test_get_cpu_metrics(self, mock_get_vm, mock_get_vm_resources,
                             mock_get_metrics):
        fake_cpu_count = 2
        fake_uptime = 1000
        fake_cpu_metrics_val = 2000

        self.utils._metrics_defs_obj = {
            self.utils._CPU_METRICS: mock.sentinel.metrics}

        mock_vm = mock_get_vm.return_value
        mock_vm.OnTimeInMilliseconds = fake_uptime
        mock_cpu = mock.MagicMock(VirtualQuantity=fake_cpu_count)
        mock_get_vm_resources.return_value = [mock_cpu]

        mock_metric = mock.MagicMock(MetricValue=fake_cpu_metrics_val)
        mock_get_metrics.return_value = [mock_metric]

        cpu_metrics = self.utils.get_cpu_metrics(mock.sentinel.vm_name)

        self.assertEqual(3, len(cpu_metrics))
        self.assertEqual(fake_cpu_metrics_val, cpu_metrics[0])
        self.assertEqual(fake_cpu_count, cpu_metrics[1])
        self.assertEqual(fake_uptime, cpu_metrics[2])

        mock_get_vm.assert_called_once_with(mock.sentinel.vm_name)
        mock_get_vm_resources.assert_called_once_with(
            mock.sentinel.vm_name, self.utils._PROCESSOR_SETTING_DATA_CLASS)
        mock_get_metrics.assert_called_once_with(mock_vm,
                                                 mock.sentinel.metrics)

    @mock.patch.object(metricsutils.MetricsUtils, '_get_metrics')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm')
    def test_get_memory_metrics(self, mock_get_vm, mock_get_metrics):
        mock_vm = mock_get_vm.return_value
        self.utils._metrics_defs_obj = {
            self.utils._MEMORY_METRICS: mock.sentinel.metrics}

        metrics_memory = mock.MagicMock()
        metrics_memory.MetricValue = 3
        mock_get_metrics.return_value = [metrics_memory]

        response = self.utils.get_memory_metrics(mock.sentinel.vm_name)

        self.assertEqual(3, response)
        mock_get_vm.assert_called_once_with(mock.sentinel.vm_name)
        mock_get_metrics.assert_called_once_with(mock_vm,
                                                 mock.sentinel.metrics)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(metricsutils.MetricsUtils,
                       '_sum_metrics_values_by_defs')
    @mock.patch.object(metricsutils.MetricsUtils,
                       '_get_metrics_value_instances')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm_resources')
    def test_get_vnic_metrics(self, mock_get_vm_resources,
                              mock_get_value_instances, mock_sum_by_defs,
                              mock_get_element_associated_class):
        fake_rx_mb = 1000
        fake_tx_mb = 2000

        self.utils._metrics_defs_obj = {
            self.utils._NET_IN_METRICS: mock.sentinel.net_in_metrics,
            self.utils._NET_OUT_METRICS: mock.sentinel.net_out_metrics}

        mock_port = mock.MagicMock(Parent=mock.sentinel.vnic_path)
        mock_vnic = mock.MagicMock(ElementName=mock.sentinel.element_name,
                                   Address=mock.sentinel.address)
        mock_vnic.path_.return_value = mock.sentinel.vnic_path
        mock_get_vm_resources.side_effect = [[mock_port], [mock_vnic]]
        mock_sum_by_defs.return_value = [fake_rx_mb, fake_tx_mb]

        vnic_metrics = list(
            self.utils.get_vnic_metrics(mock.sentinel.vm_name))

        self.assertEqual(1, len(vnic_metrics))
        self.assertEqual(fake_rx_mb, vnic_metrics[0]['rx_mb'])
        self.assertEqual(fake_tx_mb, vnic_metrics[0]['tx_mb'])
        self.assertEqual(mock.sentinel.element_name,
                         vnic_metrics[0]['element_name'])
        self.assertEqual(mock.sentinel.address, vnic_metrics[0]['address'])

        mock_get_vm_resources.assert_has_calls([
            mock.call(mock.sentinel.vm_name, self.utils._PORT_ALLOC_SET_DATA),
            mock.call(mock.sentinel.vm_name,
                      self.utils._SYNTH_ETH_PORT_SET_DATA)])
        mock_get_value_instances.assert_called_once_with(
            mock_get_element_associated_class.return_value,
            self.utils._BASE_METRICS_VALUE)
        mock_sum_by_defs.assert_called_once_with(
            mock_get_value_instances.return_value,
            [mock.sentinel.net_in_metrics, mock.sentinel.net_out_metrics])

    @mock.patch.object(metricsutils.MetricsUtils, '_get_metrics_values')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm_resources')
    def test_get_disk_metrics(self, mock_get_vm_resources,
                              mock_get_metrics_values):
        fake_read_mb = 1000
        fake_write_mb = 2000

        self.utils._metrics_defs_obj = {
            self.utils._DISK_RD_METRICS: mock.sentinel.disk_rd_metrics,
            self.utils._DISK_WR_METRICS: mock.sentinel.disk_wr_metrics}

        mock_disk = mock.MagicMock(HostResource=[mock.sentinel.host_resource],
                                   InstanceID=mock.sentinel.instance_id)
        mock_get_vm_resources.return_value = [mock_disk]
        mock_get_metrics_values.return_value = [fake_read_mb, fake_write_mb]

        disk_metrics = list(
            self.utils.get_disk_metrics(mock.sentinel.vm_name))

        self.assertEqual(1, len(disk_metrics))
        self.assertEqual(fake_read_mb, disk_metrics[0]['read_mb'])
        self.assertEqual(fake_write_mb, disk_metrics[0]['write_mb'])
        self.assertEqual(mock.sentinel.instance_id,
                         disk_metrics[0]['instance_id'])
        self.assertEqual(mock.sentinel.host_resource,
                         disk_metrics[0]['host_resource'])

        mock_get_vm_resources.assert_called_once_with(
            mock.sentinel.vm_name,
            self.utils._STORAGE_ALLOC_SETTING_DATA_CLASS)
        metrics = [mock.sentinel.disk_rd_metrics,
                   mock.sentinel.disk_wr_metrics]
        mock_get_metrics_values.assert_called_once_with(mock_disk, metrics)

    @mock.patch.object(metricsutils.MetricsUtils, '_get_metrics_values')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm_resources')
    def test_get_disk_latency_metrics(self, mock_get_vm_resources,
                                      mock_get_metrics_values):
        self.utils._metrics_defs_obj = {
            self.utils._DISK_LATENCY_METRICS: mock.sentinel.metrics}

        mock_disk = mock.MagicMock(HostResource=[mock.sentinel.host_resource],
                                   InstanceID=mock.sentinel.instance_id)
        mock_get_vm_resources.return_value = [mock_disk]
        mock_get_metrics_values.return_value = [mock.sentinel.latency]

        disk_metrics = list(
            self.utils.get_disk_latency_metrics(mock.sentinel.vm_name))

        self.assertEqual(1, len(disk_metrics))
        self.assertEqual(mock.sentinel.latency,
                         disk_metrics[0]['disk_latency'])
        self.assertEqual(mock.sentinel.instance_id,
                         disk_metrics[0]['instance_id'])
        mock_get_vm_resources.assert_called_once_with(
            mock.sentinel.vm_name,
            self.utils._STORAGE_ALLOC_SETTING_DATA_CLASS)
        mock_get_metrics_values.assert_called_once_with(
            mock_disk, [mock.sentinel.metrics])

    @mock.patch.object(metricsutils.MetricsUtils, '_get_metrics_values')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm_resources')
    def test_get_disk_iops_metrics(self, mock_get_vm_resources,
                                   mock_get_metrics_values):
        self.utils._metrics_defs_obj = {
            self.utils._DISK_IOPS_METRICS: mock.sentinel.metrics}
        mock_disk = mock.MagicMock(HostResource=[mock.sentinel.host_resource],
                                   InstanceID=mock.sentinel.instance_id)
        mock_get_vm_resources.return_value = [mock_disk]
        mock_get_metrics_values.return_value = [mock.sentinel.iops]

        disk_metrics = list(
            self.utils.get_disk_iops_count(mock.sentinel.vm_name))

        self.assertEqual(1, len(disk_metrics))
        self.assertEqual(mock.sentinel.iops,
                         disk_metrics[0]['iops_count'])
        self.assertEqual(mock.sentinel.instance_id,
                         disk_metrics[0]['instance_id'])
        mock_get_vm_resources.assert_called_once_with(
            mock.sentinel.vm_name,
            self.utils._STORAGE_ALLOC_SETTING_DATA_CLASS)
        mock_get_metrics_values.assert_called_once_with(
            mock_disk, [mock.sentinel.metrics])

    def test_sum_metrics_values(self):
        mock_metric = mock.MagicMock(MetricValue='100')
        result = self.utils._sum_metrics_values([mock_metric] * 2)
        self.assertEqual(200, result)

    def test_sum_metrics_values_by_defs(self):
        mock_metric = mock.MagicMock(MetricDefinitionId=mock.sentinel.def_id,
                                     MetricValue='100')
        mock_metric_useless = mock.MagicMock(MetricValue='200')
        mock_metric_def = mock.MagicMock(Id=mock.sentinel.def_id)

        result = self.utils._sum_metrics_values_by_defs(
            [mock_metric, mock_metric_useless], [None, mock_metric_def])

        self.assertEqual([0, 100], result)

    def test_get_metrics_value_instances(self):
        FAKE_CLASS_NAME = "FAKE_CLASS"
        mock_el_metric = mock.MagicMock()
        mock_el_metric_2 = mock.MagicMock()
        mock_el_metric_2.path.return_value = mock.Mock(Class=FAKE_CLASS_NAME)

        self.utils._conn.Msvm_MetricForME.side_effect = [
            [], [mock.Mock(Dependent=mock_el_metric_2)]]

        returned = self.utils._get_metrics_value_instances(
            [mock_el_metric, mock_el_metric_2], FAKE_CLASS_NAME)

        expected_return = [mock_el_metric_2]
        self.assertEqual(expected_return, returned)

    @mock.patch.object(metricsutils.MetricsUtils,
                       '_sum_metrics_values_by_defs')
    def test_get_metrics_values(self, mock_sum_by_defs):
        mock_element = mock.MagicMock()
        self.utils._conn.Msvm_MetricForME.return_value = [
            mock.Mock(Dependent=mock.sentinel.metric),
            mock.Mock(Dependent=mock.sentinel.another_metric)]

        resulted_metrics_sum = self.utils._get_metrics_values(
            mock_element, mock.sentinel.metrics_defs)

        self.utils._conn.Msvm_MetricForME.assert_called_once_with(
            Antecedent=mock_element.path_.return_value)
        mock_sum_by_defs.assert_called_once_with(
            [mock.sentinel.metric, mock.sentinel.another_metric],
            mock.sentinel.metrics_defs)
        expected_metrics_sum = mock_sum_by_defs.return_value
        self.assertEqual(expected_metrics_sum, resulted_metrics_sum)

    @mock.patch.object(metricsutils.MetricsUtils, '_filter_metrics')
    def test_get_metrics(self, mock_filter_metrics):
        mock_metric = mock.MagicMock()
        mock_element = mock.MagicMock()
        self.utils._conn.Msvm_MetricForME.return_value = [mock_metric]

        result = self.utils._get_metrics(mock_element,
                                         mock.sentinel.metrics_def)

        self.assertEqual(mock_filter_metrics.return_value, result)
        self.utils._conn.Msvm_MetricForME.assert_called_once_with(
            Antecedent=mock_element.path_.return_value)
        mock_filter_metrics.assert_called_once_with(
            [mock_metric.Dependent],
            mock.sentinel.metrics_def)

    def test_filter_metrics(self):
        mock_metric = mock.MagicMock(MetricDefinitionId=mock.sentinel.def_id)
        mock_bad_metric = mock.MagicMock()
        mock_metric_def = mock.MagicMock(Id=mock.sentinel.def_id)

        result = self.utils._filter_metrics([mock_bad_metric, mock_metric],
                                            mock_metric_def)

        self.assertEqual([mock_metric], result)

    @mock.patch.object(_wqlutils, 'get_element_associated_class')
    @mock.patch.object(metricsutils.MetricsUtils, '_get_vm_setting_data')
    def test_get_vm_resources(self, mock_get_vm_setting_data,
                              mock_get_element_associated_class):
        result = self.utils._get_vm_resources(mock.sentinel.vm_name,
                                              mock.sentinel.resource_class)

        mock_get_vm_setting_data.assert_called_once_with(mock.sentinel.vm_name)
        vm_setting_data = mock_get_vm_setting_data.return_value
        mock_get_element_associated_class.assert_called_once_with(
            self.utils._conn, mock.sentinel.resource_class,
            element_instance_id=vm_setting_data.InstanceID)
        self.assertEqual(mock_get_element_associated_class.return_value,
                         result)

    @mock.patch.object(metricsutils.MetricsUtils, '_unique_result')
    def test_get_vm(self, mock_unique_result):
        result = self.utils._get_vm(mock.sentinel.vm_name)

        self.assertEqual(mock_unique_result.return_value, result)
        conn_class = self.utils._conn.Msvm_ComputerSystem
        conn_class.assert_called_once_with(ElementName=mock.sentinel.vm_name)
        mock_unique_result.assert_called_once_with(conn_class.return_value,
                                                   mock.sentinel.vm_name)

    @mock.patch.object(metricsutils.MetricsUtils, '_unique_result')
    def test_get_switch_port(self, mock_unique_result):
        result = self.utils._get_switch_port(mock.sentinel.port_name)

        self.assertEqual(mock_unique_result.return_value, result)
        conn_class = self.utils._conn.Msvm_EthernetPortAllocationSettingData
        conn_class.assert_called_once_with(ElementName=mock.sentinel.port_name)
        mock_unique_result.assert_called_once_with(conn_class.return_value,
                                                   mock.sentinel.port_name)

    @mock.patch.object(metricsutils.MetricsUtils, '_unique_result')
    def test_get_vm_setting_data(self, mock_unique_result):
        result = self.utils._get_vm_setting_data(mock.sentinel.vm_name)

        self.assertEqual(mock_unique_result.return_value, result)
        conn_class = self.utils._conn.Msvm_VirtualSystemSettingData
        conn_class.assert_called_once_with(ElementName=mock.sentinel.vm_name)
        mock_unique_result.assert_called_once_with(conn_class.return_value,
                                                   mock.sentinel.vm_name)

    def test_unique_result_not_found(self):
        self.assertRaises(exceptions.NotFound,
                          self.utils._unique_result,
                          [], mock.sentinel.resource_name)

    def test_unique_result_duplicate(self):
        self.assertRaises(exceptions.OSWinException,
                          self.utils._unique_result,
                          [mock.ANY, mock.ANY], mock.sentinel.resource_name)

    def test_unique_result(self):
        result = self.utils._unique_result([mock.sentinel.obj],
                                           mock.sentinel.resource_name)
        self.assertEqual(mock.sentinel.obj, result)
