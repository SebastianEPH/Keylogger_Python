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

import ddt
import mock
from six.moves import queue

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils.compute import clusterutils
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi.libs import clusapi as clusapi_def
from os_win.utils.winapi import wintypes


@ddt.ddt
class ClusterUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V ClusterUtilsBase class."""

    _autospec_classes = [
        clusterutils._clusapi_utils.ClusApiUtils,
        clusterutils._clusapi_utils.ClusterContextManager
    ]

    _FAKE_RES_NAME = "fake_res_name"
    _FAKE_HOST = "fake_host"
    _FAKE_PREV_HOST = "fake_prev_host"
    _FAKE_VM_NAME = 'instance-00000001'
    _FAKE_RESOURCEGROUP_NAME = 'Virtual Machine %s' % _FAKE_VM_NAME

    @mock.patch.object(clusterutils.ClusterUtils, '_init_hyperv_conn')
    def setUp(self, mock_get_wmi_conn):
        super(ClusterUtilsTestCase, self).setUp()
        self._clusterutils = clusterutils.ClusterUtils()
        self._clusterutils._conn_cluster = mock.MagicMock()
        self._clusterutils._cluster = mock.MagicMock()
        self._clusapi = self._clusterutils._clusapi_utils
        self._cmgr = self._clusterutils._cmgr

    def _cmgr_val(self, cmgr):
        # Return the value that a mocked context manager would yield.
        return cmgr.return_value.__enter__.return_value

    def test_init_hyperv_conn(self):
        fake_cluster_name = "fake_cluster"
        mock_cluster = mock.MagicMock()
        mock_cluster.path_.return_value = r"\\%s\root" % fake_cluster_name

        mock_conn = mock.MagicMock()
        mock_conn.MSCluster_Cluster.return_value = [mock_cluster]

        self._clusterutils._get_wmi_conn = mock.MagicMock()
        self._clusterutils._get_wmi_conn.return_value = mock_conn

        self._clusterutils._init_hyperv_conn("fake_host", timeout=1)

    def test_init_hyperv_conn_exception(self):
        self._clusterutils._get_wmi_conn = mock.MagicMock()
        self._clusterutils._get_wmi_conn.side_effect = AttributeError
        self.assertRaises(exceptions.HyperVClusterException,
                          self._clusterutils._init_hyperv_conn, "fake_host",
                          timeout=1)

    @mock.patch.object(clusterutils.ClusterUtils,
                       '_get_cluster_nodes')
    def test_check_cluster_state_not_enough_nodes(self, mock_get_nodes):
        self.assertRaises(exceptions.HyperVClusterException,
                          self._clusterutils.check_cluster_state)

    def test_get_node_name(self):
        self._clusterutils._this_node = mock.sentinel.fake_node_name
        self.assertEqual(mock.sentinel.fake_node_name,
                         self._clusterutils.get_node_name())

    @mock.patch.object(clusterutils.ClusterUtils, 'cluster_enum')
    def test_get_cluster_nodes(self, mock_cluster_enum):
        expected = mock_cluster_enum.return_value

        self.assertEqual(expected, self._clusterutils._get_cluster_nodes())

        mock_cluster_enum.assert_called_once_with(w_const.CLUSTER_ENUM_NODE)

    @mock.patch.object(clusterutils.ClusterUtils, 'cluster_enum')
    @mock.patch.object(clusterutils.ClusterUtils, 'get_cluster_group_type')
    def test_get_vm_groups(self, mock_get_type, mock_cluster_enum):
        mock_groups = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock()]
        group_types = [w_const.ClusGroupTypeVirtualMachine,
                       w_const.ClusGroupTypeVirtualMachine,
                       mock.sentinel.some_other_group_type]

        mock_cluster_enum.return_value = mock_groups
        mock_get_type.side_effect = group_types

        exp = mock_groups[:-1]
        res = list(self._clusterutils._get_vm_groups())

        self.assertEqual(exp, res)

        mock_cluster_enum.assert_called_once_with(w_const.CLUSTER_ENUM_GROUP)
        mock_get_type.assert_has_calls(
            [mock.call(r['name']) for r in mock_groups])

    @mock.patch.object(clusterutils.ClusterUtils,
                       '_lookup_vm_group')
    def test_lookup_vm_group_check(self, mock_lookup_vm_group):
        mock_lookup_vm_group.return_value = mock.sentinel.fake_vm

        ret = self._clusterutils._lookup_vm_group_check(
            self._FAKE_VM_NAME)
        self.assertEqual(mock.sentinel.fake_vm, ret)

    @mock.patch.object(clusterutils.ClusterUtils,
                       '_lookup_vm_group')
    def test_lookup_vm_group_check_no_vm(self, mock_lookup_vm_group):
        mock_lookup_vm_group.return_value = None

        self.assertRaises(exceptions.HyperVVMNotFoundException,
                          self._clusterutils._lookup_vm_group_check,
                          self._FAKE_VM_NAME)

    @mock.patch.object(clusterutils.ClusterUtils,
                       '_lookup_res')
    def test_lookup_vm_group(self, mock_lookup_res):
        self._clusterutils._lookup_vm_group(self._FAKE_VM_NAME)
        mock_lookup_res.assert_called_once_with(
            self._clusterutils._conn_cluster.MSCluster_ResourceGroup,
            self._FAKE_VM_NAME)

    def test_lookup_res_no_res(self):
        res_list = []
        resource_source = mock.MagicMock()
        resource_source.return_value = res_list

        self.assertIsNone(
            self._clusterutils._lookup_res(resource_source,
                                           self._FAKE_RES_NAME))
        resource_source.assert_called_once_with(
            Name=self._FAKE_RES_NAME)

    def test_lookup_res_duplicate_res(self):
        res_list = [mock.sentinel.r1,
                    mock.sentinel.r1]
        resource_source = mock.MagicMock()
        resource_source.return_value = res_list

        self.assertRaises(exceptions.HyperVClusterException,
                          self._clusterutils._lookup_res,
                          resource_source,
                          self._FAKE_RES_NAME)
        resource_source.assert_called_once_with(
            Name=self._FAKE_RES_NAME)

    def test_lookup_res(self):
        res_list = [mock.sentinel.r1]
        resource_source = mock.MagicMock()
        resource_source.return_value = res_list

        self.assertEqual(
            mock.sentinel.r1,
            self._clusterutils._lookup_res(resource_source,
                                           self._FAKE_RES_NAME))
        resource_source.assert_called_once_with(
            Name=self._FAKE_RES_NAME)

    @mock.patch.object(clusterutils.ClusterUtils,
                       '_get_cluster_nodes')
    def test_get_cluster_node_names(self, mock_get_cluster_nodes):
        cluster_nodes = [dict(name='node1'),
                         dict(name='node2')]
        mock_get_cluster_nodes.return_value = cluster_nodes

        ret = self._clusterutils.get_cluster_node_names()

        self.assertItemsEqual(['node1', 'node2'], ret)

    @mock.patch.object(clusterutils.ClusterUtils, '_get_cluster_group_state')
    def test_get_vm_host(self, mock_get_state):
        # Refresh the helpers. Closures are a bit difficult to mock.
        owner_node = "fake_owner_node"
        mock_get_state.return_value = dict(owner_node=owner_node)

        self.assertEqual(
            owner_node,
            self._clusterutils.get_vm_host(mock.sentinel.vm_name))

        self._cmgr.open_cluster_group.assert_called_once_with(
            mock.sentinel.vm_name)
        mock_get_state.assert_called_once_with(
            self._cmgr_val(self._cmgr.open_cluster_group))

    @mock.patch.object(clusterutils.ClusterUtils, '_get_vm_groups')
    def test_list_instances(self, mock_get_vm_groups):
        mock_get_vm_groups.return_value = [dict(name='vm1'),
                                           dict(name='vm2')]
        ret = self._clusterutils.list_instances()
        self.assertItemsEqual(['vm1', 'vm2'], ret)

    @mock.patch.object(clusterutils.ClusterUtils, '_get_vm_groups')
    def test_list_instance_uuids(self, mock_get_vm_groups):
        mock_get_vm_groups.return_value = [dict(id='uuid1'),
                                           dict(id='uuid2')]
        ret = self._clusterutils.list_instance_uuids()
        self.assertItemsEqual(['uuid1', 'uuid2'], ret)

    @ddt.data(True, False)
    @mock.patch.object(clusterutils.ClusterUtils,
                       '_lookup_vm_group_check')
    def test_add_vm_to_cluster(self, auto_failback,
                               mock_lookup_vm_group_check):
        self._clusterutils._cluster.AddVirtualMachine = mock.MagicMock()
        vm_group = mock.Mock()
        mock_lookup_vm_group_check.return_value = vm_group

        self._clusterutils.add_vm_to_cluster(
            self._FAKE_VM_NAME, mock.sentinel.max_failover_count,
            mock.sentinel.failover_period, auto_failback)

        self.assertEqual(mock.sentinel.max_failover_count,
                         vm_group.FailoverThreshold)
        self.assertEqual(mock.sentinel.failover_period,
                         vm_group.FailoverPeriod)
        self.assertTrue(vm_group.PersistentState)
        self.assertEqual(vm_group.AutoFailbackType, int(auto_failback))
        self.assertEqual(vm_group.FailbackWindowStart,
                         self._clusterutils._FAILBACK_WINDOW_MIN)
        self.assertEqual(vm_group.FailbackWindowEnd,
                         self._clusterutils._FAILBACK_WINDOW_MAX)
        vm_group.put.assert_called_once_with()

    def test_bring_online(self):
        self._clusterutils.bring_online(mock.sentinel.vm_name)

        self._cmgr.open_cluster_group.assert_called_once_with(
            mock.sentinel.vm_name)
        self._clusapi.online_cluster_group.assert_called_once_with(
            self._cmgr_val(self._cmgr.open_cluster_group))

    def test_take_offline(self):
        self._clusterutils.take_offline(mock.sentinel.vm_name)

        self._cmgr.open_cluster_group.assert_called_once_with(
            mock.sentinel.vm_name)
        self._clusapi.offline_cluster_group.assert_called_once_with(
            self._cmgr_val(self._cmgr.open_cluster_group))

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group')
    def test_delete(self, mock_lookup_vm_group):
        vm = mock.MagicMock()
        mock_lookup_vm_group.return_value = vm

        self._clusterutils.delete(self._FAKE_VM_NAME)
        vm.DestroyGroup.assert_called_once_with(
            self._clusterutils._DESTROY_GROUP)

    def test_cluster_enum(self):
        cluster_objects = [mock.Mock(), mock.Mock()]

        self._clusapi.cluster_get_enum_count.return_value = len(
            cluster_objects)
        self._clusapi.cluster_enum.side_effect = cluster_objects

        exp_ret_val = [dict(version=item.dwVersion,
                            type=item.dwType,
                            id=item.lpszId,
                            name=item.lpszName) for item in cluster_objects]
        ret_val = list(self._clusterutils.cluster_enum(mock.sentinel.obj_type))

        self.assertEqual(exp_ret_val, ret_val)

        enum_handle = self._cmgr_val(self._cmgr.open_cluster_enum)
        self._cmgr.open_cluster_enum.assert_called_once_with(
            mock.sentinel.obj_type)
        self._clusapi.cluster_get_enum_count.assert_called_once_with(
            enum_handle)
        self._clusapi.cluster_enum.assert_has_calls(
            [mock.call(enum_handle, idx)
             for idx in range(len(cluster_objects))])

    @ddt.data(True, False)
    def test_vm_exists(self, exists):
        self._cmgr.open_cluster_resource.side_effect = (
            None if exists else exceptions.ClusterObjectNotFound('test'))

        self.assertEqual(
            exists,
            self._clusterutils.vm_exists(self._FAKE_VM_NAME))

        self._cmgr.open_cluster_resource.assert_called_once_with(
            self._FAKE_RESOURCEGROUP_NAME)

    @mock.patch.object(clusterutils.ClusterUtils, '_migrate_vm')
    def test_live_migrate_vm(self, mock_migrate_vm):
        self._clusterutils.live_migrate_vm(self._FAKE_VM_NAME,
                                           self._FAKE_HOST,
                                           mock.sentinel.timeout)

        mock_migrate_vm.assert_called_once_with(
            self._FAKE_VM_NAME, self._FAKE_HOST,
            self._clusterutils._LIVE_MIGRATION_TYPE,
            constants.CLUSTER_GROUP_ONLINE,
            mock.sentinel.timeout)

    @mock.patch.object(wintypes, 'DWORD')
    @mock.patch.object(clusterutils.ClusterUtils,
                       '_wait_for_cluster_group_migration')
    @mock.patch.object(clusterutils.ClusterUtils,
                       '_validate_migration')
    @mock.patch.object(clusterutils,
                       '_ClusterGroupStateChangeListener')
    @ddt.data(None, exceptions.ClusterException)
    def test_migrate_vm(self, wait_unexpected_exc,
                        mock_listener_cls,
                        mock_validate_migr,
                        mock_wait_group, mock_dword):
        mock_wait_group.side_effect = wait_unexpected_exc

        migrate_args = (self._FAKE_VM_NAME,
                        self._FAKE_HOST,
                        self._clusterutils._LIVE_MIGRATION_TYPE,
                        constants.CLUSTER_GROUP_ONLINE,
                        mock.sentinel.timeout)

        if wait_unexpected_exc:
            self.assertRaises(wait_unexpected_exc,
                              self._clusterutils._migrate_vm,
                              *migrate_args)
        else:
            self._clusterutils._migrate_vm(*migrate_args)

        mock_dword.assert_called_once_with(
            self._clusterutils._LIVE_MIGRATION_TYPE)

        self._clusapi.get_property_list_entry.assert_has_calls(
            [mock.call(prop_name,
                       w_const.CLUSPROP_SYNTAX_LIST_VALUE_DWORD,
                       mock_dword.return_value)
             for prop_name in (w_const.CLUS_RESTYPE_NAME_VM,
                               w_const.CLUS_RESTYPE_NAME_VM_CONFIG)])

        expected_prop_entries = [
            self._clusapi.get_property_list_entry.return_value] * 2
        self._clusapi.get_property_list.assert_called_once_with(
            expected_prop_entries)

        expected_migrate_flags = (
            w_const.CLUSAPI_GROUP_MOVE_RETURN_TO_SOURCE_NODE_ON_ERROR |
            w_const.CLUSAPI_GROUP_MOVE_QUEUE_ENABLED |
            w_const.CLUSAPI_GROUP_MOVE_HIGH_PRIORITY_START)

        exp_clus_h = self._cmgr_val(self._cmgr.open_cluster)
        exp_clus_node_h = self._cmgr_val(self._cmgr.open_cluster_node)
        exp_clus_group_h = self._cmgr_val(self._cmgr.open_cluster_group)

        self._cmgr.open_cluster.assert_called_once_with()
        self._cmgr.open_cluster_group.assert_called_once_with(
            self._FAKE_VM_NAME, cluster_handle=exp_clus_h)
        self._cmgr.open_cluster_node.assert_called_once_with(
            self._FAKE_HOST, cluster_handle=exp_clus_h)

        self._clusapi.move_cluster_group.assert_called_once_with(
            exp_clus_group_h, exp_clus_node_h, expected_migrate_flags,
            self._clusapi.get_property_list.return_value)

        mock_listener_cls.assert_called_once_with(exp_clus_h,
                                                  self._FAKE_VM_NAME)
        mock_listener = mock_listener_cls.return_value

        mock_wait_group.assert_called_once_with(
            mock_listener.__enter__.return_value,
            self._FAKE_VM_NAME, exp_clus_group_h,
            constants.CLUSTER_GROUP_ONLINE,
            mock.sentinel.timeout)

        if not wait_unexpected_exc:
            mock_validate_migr.assert_called_once_with(
                exp_clus_group_h,
                self._FAKE_VM_NAME,
                constants.CLUSTER_GROUP_ONLINE,
                self._FAKE_HOST)

    @mock.patch.object(clusterutils.ClusterUtils,
                       '_cancel_cluster_group_migration')
    @mock.patch.object(clusterutils.ClusterUtils,
                       '_wait_for_cluster_group_migration')
    @mock.patch.object(clusterutils.ClusterUtils,
                       '_validate_migration')
    @mock.patch.object(clusterutils,
                       '_ClusterGroupStateChangeListener')
    @ddt.data(True, False)
    def test_migrate_vm_timeout(self, finished_after_cancel,
                                mock_listener_cls,
                                mock_validate_migr,
                                mock_wait_group,
                                mock_cancel_migr):
        timeout_exc = exceptions.ClusterGroupMigrationTimeOut(
            group_name=self._FAKE_VM_NAME,
            time_elapsed=10)
        mock_wait_group.side_effect = timeout_exc
        mock_listener = self._cmgr_val(mock_listener_cls)
        mock_validate_migr.side_effect = (
            (None, ) if finished_after_cancel
            else exceptions.ClusterGroupMigrationFailed(
                group_name=self._FAKE_VM_NAME,
                expected_state=mock.sentinel.expected_state,
                expected_node=self._FAKE_HOST,
                group_state=mock.sentinel.expected_state,
                owner_node=mock.sentinel.other_host))

        migrate_args = (self._FAKE_VM_NAME,
                        self._FAKE_HOST,
                        self._clusterutils._LIVE_MIGRATION_TYPE,
                        mock.sentinel.exp_state,
                        mock.sentinel.timeout)

        if finished_after_cancel:
            self._clusterutils._migrate_vm(*migrate_args)
        else:
            self.assertRaises(exceptions.ClusterGroupMigrationTimeOut,
                              self._clusterutils._migrate_vm,
                              *migrate_args)

        exp_clus_group_h = self._cmgr_val(self._cmgr.open_cluster_group)
        mock_cancel_migr.assert_called_once_with(
            mock_listener, self._FAKE_VM_NAME, exp_clus_group_h,
            mock.sentinel.exp_state, mock.sentinel.timeout)
        mock_validate_migr.assert_called_once_with(exp_clus_group_h,
                                                   self._FAKE_VM_NAME,
                                                   mock.sentinel.exp_state,
                                                   self._FAKE_HOST)

    @ddt.data({},
              {'expected_state': constants.CLUSTER_GROUP_OFFLINE,
               'is_valid': False},
              {'expected_node': 'some_other_node',
               'is_valid': False})
    @ddt.unpack
    def test_validate_migration(
            self, expected_node=_FAKE_HOST,
            expected_state=constants.CLUSTER_GROUP_ONLINE,
            is_valid=True):
        group_state = dict(owner_node=self._FAKE_HOST.upper(),
                           state=constants.CLUSTER_GROUP_ONLINE)
        self._clusapi.get_cluster_group_state.return_value = group_state

        if is_valid:
            self._clusterutils._validate_migration(mock.sentinel.group_handle,
                                                   self._FAKE_VM_NAME,
                                                   expected_state,
                                                   expected_node)
        else:
            self.assertRaises(exceptions.ClusterGroupMigrationFailed,
                              self._clusterutils._validate_migration,
                              mock.sentinel.group_handle,
                              self._FAKE_VM_NAME,
                              expected_state,
                              expected_node)

        self._clusapi.get_cluster_group_state.assert_called_once_with(
            mock.sentinel.group_handle)

    @mock.patch.object(clusterutils.ClusterUtils,
                       '_cancel_cluster_group_migration')
    @mock.patch.object(clusterutils,
                       '_ClusterGroupStateChangeListener')
    def test_cancel_cluster_group_migration_public(self, mock_listener_cls,
                                                   mock_cancel_migr):

        exp_clus_h = self._cmgr_val(self._cmgr.open_cluster)
        exp_clus_group_h = self._cmgr_val(self._cmgr.open_cluster_group)

        mock_listener = mock_listener_cls.return_value
        mock_listener.__enter__.return_value = mock_listener

        self._clusterutils.cancel_cluster_group_migration(
            mock.sentinel.group_name,
            mock.sentinel.expected_state,
            mock.sentinel.timeout)

        self._cmgr.open_cluster.assert_called_once_with()
        self._cmgr.open_cluster_group.assert_called_once_with(
            mock.sentinel.group_name, cluster_handle=exp_clus_h)

        mock_listener.__enter__.assert_called_once_with()
        mock_listener_cls.assert_called_once_with(exp_clus_h,
                                                  mock.sentinel.group_name)
        mock_cancel_migr.assert_called_once_with(
            mock_listener,
            mock.sentinel.group_name,
            exp_clus_group_h,
            mock.sentinel.expected_state,
            mock.sentinel.timeout)

    @mock.patch.object(clusterutils.ClusterUtils,
                       '_get_cluster_group_state')
    @mock.patch.object(clusterutils.ClusterUtils,
                       '_is_migration_pending')
    @mock.patch.object(clusterutils.ClusterUtils,
                       '_wait_for_cluster_group_migration')
    @ddt.data({},
              {'cancel_exception': test_base.TestingException()},
              {'cancel_exception':
                  exceptions.Win32Exception(
                      error_code=w_const.INVALID_HANDLE_VALUE,
                      func_name=mock.sentinel.func_name,
                      error_message=mock.sentinel.error_message)},
              {'cancel_exception':
                  exceptions.Win32Exception(
                      error_code=w_const.ERROR_INVALID_STATE,
                      func_name=mock.sentinel.func_name,
                      error_message=mock.sentinel.error_message),
               'invalid_state_for_cancel': True},
              {'cancel_exception':
                  exceptions.Win32Exception(
                      error_code=w_const.ERROR_INVALID_STATE,
                      func_name=mock.sentinel.func_name,
                      error_message=mock.sentinel.error_message),
               'invalid_state_for_cancel': True,
               'cancel_still_pending': True},
              {'cancel_still_pending': True},
              {'cancel_still_pending': True,
               'cancel_wait_exception': test_base.TestingException()})
    @ddt.unpack
    def test_cancel_cluster_group_migration(self, mock_wait_migr,
                                            mock_is_migr_pending,
                                            mock_get_gr_state,
                                            cancel_still_pending=False,
                                            cancel_exception=None,
                                            invalid_state_for_cancel=False,
                                            cancel_wait_exception=None):
        expected_exception = None
        if cancel_wait_exception:
            expected_exception = exceptions.JobTerminateFailed()
        if (cancel_exception and (not invalid_state_for_cancel
                                  or cancel_still_pending)):
            expected_exception = cancel_exception

        mock_is_migr_pending.return_value = cancel_still_pending
        mock_get_gr_state.return_value = dict(
            state=mock.sentinel.state,
            status_info=mock.sentinel.status_info)

        self._clusapi.cancel_cluster_group_operation.side_effect = (
            cancel_exception or (not cancel_still_pending, ))
        mock_wait_migr.side_effect = cancel_wait_exception

        cancel_args = (mock.sentinel.listener,
                       mock.sentinel.group_name,
                       mock.sentinel.group_handle,
                       mock.sentinel.expected_state,
                       mock.sentinel.timeout)
        if expected_exception:
            self.assertRaises(
                expected_exception.__class__,
                self._clusterutils._cancel_cluster_group_migration,
                *cancel_args)
        else:
            self._clusterutils._cancel_cluster_group_migration(
                *cancel_args)

        self._clusapi.cancel_cluster_group_operation.assert_called_once_with(
            mock.sentinel.group_handle)

        if isinstance(cancel_exception, exceptions.Win32Exception):
            mock_get_gr_state.assert_called_once_with(
                mock.sentinel.group_handle)
            mock_is_migr_pending.assert_called_once_with(
                mock.sentinel.state,
                mock.sentinel.status_info,
                mock.sentinel.expected_state)
        if cancel_still_pending and not cancel_exception:
            mock_wait_migr.assert_called_once_with(
                mock.sentinel.listener,
                mock.sentinel.group_name,
                mock.sentinel.group_handle,
                mock.sentinel.expected_state,
                timeout=mock.sentinel.timeout)

    def test_is_migration_pending(self):
        self.assertTrue(
            self._clusterutils._is_migration_pending(
                group_state=constants.CLUSTER_GROUP_OFFLINE,
                group_status_info=0,
                expected_state=constants.CLUSTER_GROUP_ONLINE))
        self.assertTrue(
            self._clusterutils._is_migration_pending(
                group_state=constants.CLUSTER_GROUP_ONLINE,
                group_status_info=w_const.
                    CLUSGRP_STATUS_WAITING_IN_QUEUE_FOR_MOVE | 1,  # noqa
                expected_state=constants.CLUSTER_GROUP_ONLINE))
        self.assertFalse(
            self._clusterutils._is_migration_pending(
                group_state=constants.CLUSTER_GROUP_OFFLINE,
                group_status_info=0,
                expected_state=constants.CLUSTER_GROUP_OFFLINE))

    @mock.patch.object(clusterutils.ClusterUtils, '_is_migration_pending')
    @mock.patch.object(clusterutils.ClusterUtils, '_get_cluster_group_state')
    @mock.patch.object(clusterutils, 'time')
    def test_wait_for_clus_group_migr_timeout(self, mock_time,
                                              mock_get_gr_state,
                                              mock_is_migr_pending):
        exp_wait_iterations = 3
        mock_listener = mock.Mock()
        mock_time.time.side_effect = range(exp_wait_iterations + 2)
        timeout = 10

        state_info = dict(state=mock.sentinel.current_state,
                          status_info=mock.sentinel.status_info)

        events = [dict(status_info=mock.sentinel.migr_queued),
                  dict(state=mock.sentinel.pending_state),
                  queue.Empty]

        mock_get_gr_state.return_value = state_info
        mock_is_migr_pending.return_value = True
        mock_listener.get.side_effect = events

        self.assertRaises(
            exceptions.ClusterGroupMigrationTimeOut,
            self._clusterutils._wait_for_cluster_group_migration,
            mock_listener,
            mock.sentinel.group_name,
            mock.sentinel.group_handle,
            mock.sentinel.expected_state,
            timeout=timeout)

        mock_get_gr_state.assert_called_once_with(mock.sentinel.group_handle)

        exp_wait_times = [timeout - elapsed - 1
                          for elapsed in range(exp_wait_iterations)]
        mock_listener.get.assert_has_calls(
            [mock.call(wait_time) for wait_time in exp_wait_times])
        mock_is_migr_pending.assert_has_calls(
            [mock.call(mock.sentinel.current_state,
                       mock.sentinel.status_info,
                       mock.sentinel.expected_state),
             mock.call(mock.sentinel.current_state,
                       mock.sentinel.migr_queued,
                       mock.sentinel.expected_state),
             mock.call(mock.sentinel.pending_state,
                       mock.sentinel.migr_queued,
                       mock.sentinel.expected_state)])

    @mock.patch.object(clusterutils.ClusterUtils, '_is_migration_pending')
    @mock.patch.object(clusterutils.ClusterUtils, '_get_cluster_group_state')
    def test_wait_for_clus_group_migr_success(self, mock_get_gr_state,
                                              mock_is_migr_pending):
        mock_listener = mock.Mock()

        state_info = dict(state=mock.sentinel.current_state,
                          status_info=mock.sentinel.status_info)

        mock_get_gr_state.return_value = state_info
        mock_is_migr_pending.side_effect = [True, False]
        mock_listener.get.return_value = {}

        self._clusterutils._wait_for_cluster_group_migration(
            mock_listener,
            mock.sentinel.group_name,
            mock.sentinel.group_handle,
            mock.sentinel.expected_state,
            timeout=None)

        mock_listener.get.assert_called_once_with(None)

    @mock.patch.object(clusterutils.ClusterUtils, '_get_cluster_nodes')
    def get_cluster_node_name(self, mock_get_nodes):
        fake_node = dict(id=mock.sentinel.vm_id,
                         name=mock.sentinel.vm_name)
        mock_get_nodes.return_value([fake_node])

        self.assertEqual(
            mock.sentinel.vm_name,
            self._clusterutils.get_cluster_node_name(mock.sentinel.vm_id))
        self.assertRaises(
            exceptions.NotFound,
            self._clusterutils.get_cluster_node_name(mock.sentinel.missing_id))

    @mock.patch('ctypes.byref')
    def test_get_cluster_group_type(self, mock_byref):
        mock_byref.side_effect = lambda x: ('byref', x)
        self._clusapi.cluster_group_control.return_value = (
            mock.sentinel.buff, mock.sentinel.buff_sz)

        ret_val = self._clusterutils.get_cluster_group_type(
            mock.sentinel.group_name)
        self.assertEqual(
            self._clusapi.get_cluster_group_type.return_value,
            ret_val)

        self._cmgr.open_cluster_group.assert_called_once_with(
            mock.sentinel.group_name)
        self._clusapi.cluster_group_control.assert_called_once_with(
            self._cmgr_val(self._cmgr.open_cluster_group),
            w_const.CLUSCTL_GROUP_GET_RO_COMMON_PROPERTIES)
        self._clusapi.get_cluster_group_type.assert_called_once_with(
            mock_byref(mock.sentinel.buff), mock.sentinel.buff_sz)

    @mock.patch.object(clusterutils.ClusterUtils,
                       '_get_cluster_group_state')
    @mock.patch.object(clusterutils.ClusterUtils,
                       '_is_migration_queued')
    def test_get_cluster_group_state_info(self, mock_is_migr_queued,
                                          mock_get_gr_state):

        exp_clus_group_h = self._cmgr_val(self._cmgr.open_cluster_group)

        mock_get_gr_state.return_value = dict(
            state=mock.sentinel.state,
            status_info=mock.sentinel.status_info,
            owner_node=mock.sentinel.owner_node)

        sts_info = self._clusterutils.get_cluster_group_state_info(
            mock.sentinel.group_name)
        exp_sts_info = dict(state=mock.sentinel.state,
                            owner_node=mock.sentinel.owner_node,
                            migration_queued=mock_is_migr_queued.return_value)

        self.assertEqual(exp_sts_info, sts_info)

        self._cmgr.open_cluster_group.assert_called_once_with(
            mock.sentinel.group_name)

        mock_get_gr_state.assert_called_once_with(exp_clus_group_h)
        mock_is_migr_queued.assert_called_once_with(mock.sentinel.status_info)

    @mock.patch('ctypes.byref')
    def test_get_cluster_group_state(self, mock_byref):
        mock_byref.side_effect = lambda x: ('byref', x)

        state_info = dict(state=mock.sentinel.state,
                          owner_node=mock.sentinel.owner_node)
        self._clusapi.get_cluster_group_state.return_value = state_info

        self._clusapi.cluster_group_control.return_value = (
            mock.sentinel.buff, mock.sentinel.buff_sz)
        self._clusapi.get_cluster_group_status_info.return_value = (
            mock.sentinel.status_info)

        exp_state_info = state_info.copy()
        exp_state_info['status_info'] = mock.sentinel.status_info

        ret_val = self._clusterutils._get_cluster_group_state(
            mock.sentinel.group_handle)
        self.assertEqual(exp_state_info, ret_val)

        self._clusapi.get_cluster_group_state.assert_called_once_with(
            mock.sentinel.group_handle)
        self._clusapi.cluster_group_control.assert_called_once_with(
            mock.sentinel.group_handle,
            w_const.CLUSCTL_GROUP_GET_RO_COMMON_PROPERTIES)
        self._clusapi.get_cluster_group_status_info.assert_called_once_with(
            mock_byref(mock.sentinel.buff), mock.sentinel.buff_sz)

    @mock.patch.object(clusterutils, 'tpool')
    @mock.patch.object(clusterutils, 'patcher')
    def test_monitor_vm_failover_no_vm(self, mock_patcher, mock_tpool):
        mock_watcher = mock.MagicMock()
        fake_prev = mock.MagicMock(OwnerNode=self._FAKE_PREV_HOST)
        fake_wmi_object = mock.MagicMock(OwnerNode=self._FAKE_HOST,
                                         Name='Virtual Machine',
                                         previous=fake_prev)
        mock_tpool.execute.return_value = fake_wmi_object
        fake_callback = mock.MagicMock()

        self._clusterutils._monitor_vm_failover(mock_watcher,
                                                fake_callback,
                                                mock.sentinel.event_timeout_ms)

        mock_tpool.execute.assert_called_once_with(
            mock_watcher,
            mock.sentinel.event_timeout_ms)
        fake_callback.assert_not_called()

    @mock.patch.object(clusterutils, 'tpool')
    @mock.patch.object(clusterutils, 'patcher')
    def test_monitor_vm_failover(self, mock_patcher, mock_tpool):
        mock_watcher = mock.MagicMock()
        fake_prev = mock.MagicMock(OwnerNode=self._FAKE_PREV_HOST)
        fake_wmi_object = mock.MagicMock(OwnerNode=self._FAKE_HOST,
                                         Name=self._FAKE_RESOURCEGROUP_NAME,
                                         previous=fake_prev)
        mock_tpool.execute.return_value = fake_wmi_object
        fake_callback = mock.MagicMock()

        self._clusterutils._monitor_vm_failover(mock_watcher, fake_callback)

        mock_tpool.execute.assert_called_once_with(
            mock_watcher,
            self._clusterutils._WMI_EVENT_TIMEOUT_MS)
        fake_callback.assert_called_once_with(self._FAKE_VM_NAME,
                                              self._FAKE_PREV_HOST,
                                              self._FAKE_HOST)

    @mock.patch.object(clusterutils.ClusterUtils, '_get_failover_watcher')
    @mock.patch.object(clusterutils.ClusterUtils, '_monitor_vm_failover')
    @mock.patch.object(clusterutils, 'time')
    def test_get_vm_owner_change_listener(self, mock_time,
                                          mock_monitor, mock_get_watcher):
        mock_monitor.side_effect = [None, exceptions.OSWinException,
                                    KeyboardInterrupt]

        listener = self._clusterutils.get_vm_owner_change_listener()
        self.assertRaises(KeyboardInterrupt,
                          listener,
                          mock.sentinel.callback)

        mock_monitor.assert_has_calls(
            [mock.call(mock_get_watcher.return_value,
                       mock.sentinel.callback,
                       constants.DEFAULT_WMI_EVENT_TIMEOUT_MS)] * 3)
        mock_time.sleep.assert_called_once_with(
            constants.DEFAULT_WMI_EVENT_TIMEOUT_MS / 1000)

    @mock.patch.object(clusterutils, '_ClusterGroupOwnerChangeListener')
    @mock.patch.object(clusterutils.ClusterUtils, 'get_cluster_node_name')
    @mock.patch.object(clusterutils.ClusterUtils, 'get_cluster_group_type')
    @mock.patch.object(clusterutils, 'time')
    def test_get_vm_owner_change_listener_v2(self, mock_time, mock_get_type,
                                             mock_get_node_name,
                                             mock_listener):
        mock_get_type.side_effect = [
            w_const.ClusGroupTypeVirtualMachine,
            mock.sentinel.other_type]
        mock_events = [mock.MagicMock(), mock.MagicMock()]
        mock_listener.return_value.get.side_effect = (
            mock_events + [exceptions.OSWinException, KeyboardInterrupt])
        callback = mock.Mock()

        listener = self._clusterutils.get_vm_owner_change_listener_v2()
        self.assertRaises(KeyboardInterrupt,
                          listener,
                          callback)

        callback.assert_called_once_with(
            mock_events[0]['cluster_object_name'],
            mock_get_node_name.return_value)
        mock_listener.assert_called_once_with(
            self._clusapi.open_cluster.return_value)
        mock_get_node_name.assert_called_once_with(mock_events[0]['parent_id'])
        mock_get_type.assert_any_call(mock_events[0]['cluster_object_name'])
        mock_time.sleep.assert_called_once_with(
            constants.DEFAULT_WMI_EVENT_TIMEOUT_MS / 1000)


class ClusterEventListenerTestCase(test_base.OsWinBaseTestCase):
    @mock.patch.object(clusterutils._ClusterEventListener, '_setup')
    def setUp(self, mock_setup):
        super(ClusterEventListenerTestCase, self).setUp()

        self._setup_listener()

    def _setup_listener(self, stop_on_error=True):
        self._listener = clusterutils._ClusterEventListener(
            mock.sentinel.cluster_handle,
            stop_on_error=stop_on_error)

        self._listener._running = True
        self._listener._clusapi_utils = mock.Mock()
        self._clusapi = self._listener._clusapi_utils

    def test_get_notif_key_dw(self):
        fake_notif_key = 1
        notif_key_dw = self._listener._get_notif_key_dw(fake_notif_key)

        self.assertIsInstance(notif_key_dw, ctypes.c_ulong)
        self.assertEqual(fake_notif_key, notif_key_dw.value)
        self.assertEqual(notif_key_dw,
                         self._listener._get_notif_key_dw(fake_notif_key))

    @mock.patch.object(clusterutils._ClusterEventListener,
                       '_get_notif_key_dw')
    def test_add_filter(self, mock_get_notif_key):
        mock_get_notif_key.side_effect = (
            mock.sentinel.notif_key_dw,
            mock.sentinel.notif_key_dw_2)
        self._clusapi.create_cluster_notify_port_v2.return_value = (
            mock.sentinel.notif_port_h)

        self._listener._add_filter(mock.sentinel.filter,
                                   mock.sentinel.notif_key)
        self._listener._add_filter(mock.sentinel.filter_2,
                                   mock.sentinel.notif_key_2)

        self.assertEqual(mock.sentinel.notif_port_h,
                         self._listener._notif_port_h)
        mock_get_notif_key.assert_has_calls(
            [mock.call(mock.sentinel.notif_key),
             mock.call(mock.sentinel.notif_key_2)])
        self._clusapi.create_cluster_notify_port_v2.assert_has_calls(
            [mock.call(mock.sentinel.cluster_handle,
                       mock.sentinel.filter,
                       None,
                       mock.sentinel.notif_key_dw),
             mock.call(mock.sentinel.cluster_handle,
                       mock.sentinel.filter_2,
                       mock.sentinel.notif_port_h,
                       mock.sentinel.notif_key_dw_2)])

    @mock.patch.object(clusterutils._ClusterEventListener, '_add_filter')
    @mock.patch.object(clusapi_def, 'NOTIFY_FILTER_AND_TYPE')
    def test_setup_notif_port(self, mock_filter_struct_cls, mock_add_filter):
        notif_filter = dict(object_type=mock.sentinel.object_type,
                            filter_flags=mock.sentinel.filter_flags,
                            notif_key=mock.sentinel.notif_key)
        self._listener._notif_filters_list = [notif_filter]

        self._listener._setup_notif_port()

        mock_filter_struct_cls.assert_called_once_with(
            dwObjectType=mock.sentinel.object_type,
            FilterFlags=mock.sentinel.filter_flags)
        mock_add_filter.assert_called_once_with(
            mock_filter_struct_cls.return_value,
            mock.sentinel.notif_key)

    def test_signal_stopped(self):
        self._listener._signal_stopped()

        self.assertFalse(self._listener._running)
        self.assertIsNone(self._listener._event_queue.get(block=False))

    @mock.patch.object(clusterutils._ClusterEventListener,
                       '_signal_stopped')
    def test_stop(self, mock_signal_stopped):
        self._listener._notif_port_h = mock.sentinel.notif_port_h

        self._listener.stop()

        mock_signal_stopped.assert_called_once_with()
        self._clusapi.close_cluster_notify_port.assert_called_once_with(
            mock.sentinel.notif_port_h)

    @mock.patch.object(clusterutils._ClusterEventListener,
                       '_process_event')
    def test_listen(self, mock_process_event):
        events = [mock.sentinel.ignored_event, mock.sentinel.retrieved_event]
        self._clusapi.get_cluster_notify_v2.side_effect = events

        self._listener._notif_port_h = mock.sentinel.notif_port_h

        def fake_process_event(event):
            if event == mock.sentinel.ignored_event:
                return

            self._listener._running = False
            return mock.sentinel.processed_event

        mock_process_event.side_effect = fake_process_event

        self._listener._listen()

        processed_event = self._listener._event_queue.get(block=False)
        self.assertEqual(mock.sentinel.processed_event,
                         processed_event)
        self.assertTrue(self._listener._event_queue.empty())

        self._clusapi.get_cluster_notify_v2.assert_any_call(
            mock.sentinel.notif_port_h,
            timeout_ms=-1)

    def test_listen_exception(self):
        self._clusapi.get_cluster_notify_v2.side_effect = (
            test_base.TestingException)

        self._listener._listen()

        self.assertFalse(self._listener._running)

    @mock.patch.object(clusterutils._ClusterEventListener, '_setup')
    @mock.patch.object(clusterutils.time, 'sleep')
    def test_listen_ignore_exception(self, mock_sleep, mock_setup):
        self._setup_listener(stop_on_error=False)

        self._clusapi.get_cluster_notify_v2.side_effect = (
            test_base.TestingException,
            KeyboardInterrupt)

        self.assertRaises(KeyboardInterrupt, self._listener._listen)
        self.assertTrue(self._listener._running)
        mock_sleep.assert_called_once_with(
            self._listener._error_sleep_interval)

    def test_get_event(self):
        self._listener._event_queue = mock.Mock()

        event = self._listener.get(timeout=mock.sentinel.timeout)
        self.assertEqual(self._listener._event_queue.get.return_value, event)

        self._listener._event_queue.get.assert_called_once_with(
            timeout=mock.sentinel.timeout)

    def test_get_event_listener_stopped(self):
        self._listener._running = False
        self.assertRaises(exceptions.OSWinException,
                          self._listener.get,
                          timeout=1)

        def fake_get(block=True, timeout=0):
            self._listener._running = False
            return None

        self._listener._running = True
        self._listener._event_queue = mock.Mock(get=fake_get)

        self.assertRaises(exceptions.OSWinException,
                          self._listener.get,
                          timeout=1)

    @mock.patch.object(clusterutils._ClusterEventListener,
                       '_ensure_listener_running')
    @mock.patch.object(clusterutils._ClusterEventListener,
                       'stop')
    def test_context_manager(self, mock_stop, mock_ensure_running):
        with self._listener as l:
            self.assertIs(self._listener, l)
            mock_ensure_running.assert_called_once_with()

        mock_stop.assert_called_once_with()


class ClusterGroupStateChangeListenerTestCase(test_base.OsWinBaseTestCase):
    _FAKE_GROUP_NAME = 'fake_group_name'

    @mock.patch.object(clusterutils._ClusterEventListener, '_setup')
    def setUp(self, mock_setup):
        super(ClusterGroupStateChangeListenerTestCase, self).setUp()

        self._listener = clusterutils._ClusterGroupStateChangeListener(
            mock.sentinel.cluster_handle,
            self._FAKE_GROUP_NAME)

        self._listener._clusapi_utils = mock.Mock()
        self._clusapi = self._listener._clusapi_utils

    def _get_fake_event(self, **kwargs):
        event = dict(cluster_object_name=self._FAKE_GROUP_NAME.upper(),
                     object_type=mock.sentinel.object_type,
                     filter_flags=mock.sentinel.filter_flags,
                     buff=mock.sentinel.buff,
                     buff_sz=mock.sentinel.buff_sz)
        event.update(**kwargs)
        return event

    def _get_exp_processed_event(self, event, **kwargs):
        preserved_keys = ['cluster_object_name', 'object_type',
                          'filter_flags', 'notif_key']
        exp_proc_evt = {key: event[key] for key in preserved_keys}
        exp_proc_evt.update(**kwargs)
        return exp_proc_evt

    @mock.patch('ctypes.byref')
    def test_process_event_dropped(self, mock_byref):
        event = self._get_fake_event(cluster_object_name='other_group_name')
        self.assertIsNone(self._listener._process_event(event))

        event = self._get_fake_event(notif_key=2)
        self.assertIsNone(self._listener._process_event(event))

        notif_key = self._listener._NOTIF_KEY_GROUP_COMMON_PROP
        self._clusapi.get_cluster_group_status_info.side_effect = (
            exceptions.ClusterPropertyListEntryNotFound(
                property_name='fake_prop_name'))
        event = self._get_fake_event(notif_key=notif_key)
        self.assertIsNone(self._listener._process_event(event))

    def test_process_state_change_event(self):
        fake_state = constants.CLUSTER_GROUP_ONLINE
        event_buff = ctypes.c_ulong(fake_state)
        notif_key = self._listener._NOTIF_KEY_GROUP_STATE

        event = self._get_fake_event(notif_key=notif_key,
                                     buff=ctypes.byref(event_buff),
                                     buff_sz=ctypes.sizeof(event_buff))
        exp_proc_evt = self._get_exp_processed_event(
            event, state=fake_state)

        proc_evt = self._listener._process_event(event)
        self.assertEqual(exp_proc_evt, proc_evt)

    @mock.patch('ctypes.byref')
    def test_process_status_info_change_event(self, mock_byref):
        self._clusapi.get_cluster_group_status_info.return_value = (
            mock.sentinel.status_info)
        mock_byref.side_effect = lambda x: ('byref', x)
        notif_key = self._listener._NOTIF_KEY_GROUP_COMMON_PROP

        event = self._get_fake_event(notif_key=notif_key)
        exp_proc_evt = self._get_exp_processed_event(
            event, status_info=mock.sentinel.status_info)

        proc_evt = self._listener._process_event(event)
        self.assertEqual(exp_proc_evt, proc_evt)

        self._clusapi.get_cluster_group_status_info.assert_called_once_with(
            mock_byref(mock.sentinel.buff),
            mock.sentinel.buff_sz)
