#  Copyright 2015 Cloudbase Solutions Srl
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

import ddt
import mock

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import jobutils


@ddt.ddt
class JobUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V JobUtils class."""

    _FAKE_RET_VAL = 0

    _FAKE_JOB_STATUS_BAD = -1
    _FAKE_JOB_DESCRIPTION = "fake_job_description"
    _FAKE_JOB_PATH = 'fake_job_path'
    _FAKE_ERROR = "fake_error"
    _FAKE_ELAPSED_TIME = 0

    def setUp(self):
        super(JobUtilsTestCase, self).setUp()
        self.jobutils = jobutils.JobUtils()
        self.jobutils._conn_attr = mock.MagicMock()

    @mock.patch.object(jobutils.JobUtils, '_wait_for_job')
    def test_check_ret_val_started(self, mock_wait_for_job):
        self.jobutils.check_ret_val(constants.WMI_JOB_STATUS_STARTED,
                                    mock.sentinel.job_path)
        mock_wait_for_job.assert_called_once_with(mock.sentinel.job_path)

    @mock.patch.object(jobutils.JobUtils, '_wait_for_job')
    def test_check_ret_val_ok(self, mock_wait_for_job):
        self.jobutils.check_ret_val(self._FAKE_RET_VAL,
                                    mock.sentinel.job_path)
        self.assertFalse(mock_wait_for_job.called)

    def test_check_ret_val_exception(self):
        self.assertRaises(exceptions.WMIJobFailed,
                          self.jobutils.check_ret_val,
                          mock.sentinel.ret_val_bad,
                          mock.sentinel.job_path)

    def test_wait_for_job_ok(self):
        mock_job = self._prepare_wait_for_job(
            constants.JOB_STATE_COMPLETED_WITH_WARNINGS)
        job = self.jobutils._wait_for_job(self._FAKE_JOB_PATH)
        self.assertEqual(mock_job, job)

    def test_wait_for_job_error_state(self):
        self._prepare_wait_for_job(
            constants.JOB_STATE_TERMINATED)
        self.assertRaises(exceptions.WMIJobFailed,
                          self.jobutils._wait_for_job,
                          self._FAKE_JOB_PATH)

    def test_wait_for_job_error_code(self):
        self._prepare_wait_for_job(
            constants.JOB_STATE_COMPLETED_WITH_WARNINGS,
            error_code=1)
        self.assertRaises(exceptions.WMIJobFailed,
                          self.jobutils._wait_for_job,
                          self._FAKE_JOB_PATH)

    @ddt.data({"extended": False,
               "expected_fields": ["InstanceID"]},
              {"extended": True,
               "expected_fields": ["InstanceID", "DetailedStatus"]})
    @ddt.unpack
    @mock.patch.object(jobutils.JobUtils, '_get_job_error_details')
    def test_get_job_details(self, mock_get_job_err, expected_fields,
                             extended):
        mock_job = mock.Mock()
        details = self.jobutils._get_job_details(mock_job, extended=extended)

        if extended:
            mock_get_job_err.assert_called_once_with(mock_job)
            self.assertEqual(details['RawErrors'],
                             mock_get_job_err.return_value)

        for field in expected_fields:
            self.assertEqual(getattr(mock_job, field),
                             details[field])

    def test_get_job_error_details(self):
        mock_job = mock.Mock()
        error_details = self.jobutils._get_job_error_details(mock_job)
        mock_job.GetErrorEx.assert_called_once_with()
        self.assertEqual(mock_job.GetErrorEx.return_value, error_details)

    def test_get_job_error_details_exception(self):
        mock_job = mock.Mock()
        mock_job.GetErrorEx.side_effect = Exception
        self.assertIsNone(self.jobutils._get_job_error_details(mock_job))

    def test_get_pending_jobs(self):
        mock_killed_job = mock.Mock(JobState=constants.JOB_STATE_KILLED)
        mock_running_job = mock.Mock(JobState=constants.WMI_JOB_STATE_RUNNING)
        mock_error_st_job = mock.Mock(JobState=constants.JOB_STATE_EXCEPTION)
        mappings = [mock.Mock(AffectingElement=None),
                    mock.Mock(AffectingElement=mock_killed_job),
                    mock.Mock(AffectingElement=mock_running_job),
                    mock.Mock(AffectingElement=mock_error_st_job)]
        self.jobutils._conn.Msvm_AffectedJobElement.return_value = mappings

        mock_affected_element = mock.Mock()

        expected_pending_jobs = [mock_running_job]
        pending_jobs = self.jobutils._get_pending_jobs_affecting_element(
            mock_affected_element)
        self.assertEqual(expected_pending_jobs, pending_jobs)

        self.jobutils._conn.Msvm_AffectedJobElement.assert_called_once_with(
            AffectedElement=mock_affected_element.path_.return_value)

    @mock.patch.object(jobutils._utils, '_is_not_found_exc')
    def test_get_pending_jobs_ignored(self, mock_is_not_found_exc):
        mock_not_found_mapping = mock.MagicMock()
        type(mock_not_found_mapping).AffectingElement = mock.PropertyMock(
            side_effect=exceptions.x_wmi)
        self.jobutils._conn.Msvm_AffectedJobElement.return_value = [
            mock_not_found_mapping]

        pending_jobs = self.jobutils._get_pending_jobs_affecting_element(
            mock.MagicMock())
        self.assertEqual([], pending_jobs)

    @mock.patch.object(jobutils._utils, '_is_not_found_exc')
    def test_get_pending_jobs_reraised(self, mock_is_not_found_exc):
        mock_is_not_found_exc.return_value = False
        mock_not_found_mapping = mock.MagicMock()
        type(mock_not_found_mapping).AffectingElement = mock.PropertyMock(
            side_effect=exceptions.x_wmi)
        self.jobutils._conn.Msvm_AffectedJobElement.return_value = [
            mock_not_found_mapping]

        self.assertRaises(exceptions.x_wmi,
                          self.jobutils._get_pending_jobs_affecting_element,
                          mock.MagicMock())

    @ddt.data(True, False)
    @mock.patch.object(jobutils.JobUtils,
                       '_get_pending_jobs_affecting_element')
    def test_stop_jobs_helper(self, jobs_ended, mock_get_pending_jobs):
        mock_job1 = mock.Mock(Cancellable=True)
        mock_job2 = mock.Mock(Cancellable=True)
        mock_job3 = mock.Mock(Cancellable=False)

        pending_jobs = [mock_job1, mock_job2, mock_job3]
        mock_get_pending_jobs.side_effect = (
            pending_jobs,
            pending_jobs if not jobs_ended else [])

        mock_job1.RequestStateChange.side_effect = (
            test_base.FakeWMIExc(hresult=jobutils._utils._WBEM_E_NOT_FOUND))
        mock_job2.RequestStateChange.side_effect = (
            test_base.FakeWMIExc(hresult=mock.sentinel.hresult))

        if jobs_ended:
            self.jobutils._stop_jobs(mock.sentinel.vm)
        else:
            self.assertRaises(exceptions.JobTerminateFailed,
                              self.jobutils._stop_jobs,
                              mock.sentinel.vm)

        mock_get_pending_jobs.assert_has_calls(
            [mock.call(mock.sentinel.vm)] * 2)

        mock_job1.RequestStateChange.assert_called_once_with(
            self.jobutils._KILL_JOB_STATE_CHANGE_REQUEST)
        mock_job2.RequestStateChange.assert_called_once_with(
            self.jobutils._KILL_JOB_STATE_CHANGE_REQUEST)
        self.assertFalse(mock_job3.RequestStateqqChange.called)

    @mock.patch.object(jobutils.JobUtils, '_stop_jobs')
    def test_stop_jobs(self, mock_stop_jobs_helper):
        fake_timeout = 1
        self.jobutils.stop_jobs(mock.sentinel.element, fake_timeout)
        mock_stop_jobs_helper.assert_called_once_with(mock.sentinel.element)

    def test_is_job_completed_true(self):
        job = mock.MagicMock(JobState=constants.WMI_JOB_STATE_COMPLETED)

        self.assertTrue(self.jobutils._is_job_completed(job))

    def test_is_job_completed_false(self):
        job = mock.MagicMock(JobState=constants.WMI_JOB_STATE_RUNNING)

        self.assertFalse(self.jobutils._is_job_completed(job))

    def _prepare_wait_for_job(self, state=_FAKE_JOB_STATUS_BAD,
                              error_code=0):
        mock_job = mock.MagicMock()
        mock_job.JobState = state
        mock_job.ErrorCode = error_code
        mock_job.Description = self._FAKE_JOB_DESCRIPTION
        mock_job.ElapsedTime = self._FAKE_ELAPSED_TIME

        wmi_patcher = mock.patch.object(jobutils.JobUtils, '_get_wmi_obj')
        mock_wmi = wmi_patcher.start()
        self.addCleanup(wmi_patcher.stop)
        mock_wmi.return_value = mock_job
        return mock_job

    def test_modify_virt_resource(self):
        side_effect = [
            (self._FAKE_JOB_PATH, mock.MagicMock(), self._FAKE_RET_VAL)]
        self._check_modify_virt_resource_max_retries(side_effect=side_effect)

    def test_modify_virt_resource_max_retries_exception(self):
        side_effect = exceptions.HyperVException('expected failure.')
        self._check_modify_virt_resource_max_retries(
            side_effect=side_effect, num_calls=6, expected_fail=True)

    def test_modify_virt_resource_max_retries(self):
        side_effect = [exceptions.HyperVException('expected failure.')] * 5 + [
            (self._FAKE_JOB_PATH, mock.MagicMock(), self._FAKE_RET_VAL)]
        self._check_modify_virt_resource_max_retries(side_effect=side_effect,
                                                     num_calls=5)

    @mock.patch('time.sleep')
    def _check_modify_virt_resource_max_retries(
            self, mock_sleep, side_effect, num_calls=1, expected_fail=False):
        mock_svc = mock.MagicMock()
        self.jobutils._vs_man_svc_attr = mock_svc
        mock_svc.ModifyResourceSettings.side_effect = side_effect
        mock_res_setting_data = mock.MagicMock()
        mock_res_setting_data.GetText_.return_value = mock.sentinel.res_data

        if expected_fail:
            self.assertRaises(exceptions.HyperVException,
                              self.jobutils.modify_virt_resource,
                              mock_res_setting_data)
        else:
            self.jobutils.modify_virt_resource(mock_res_setting_data)

        mock_calls = [
            mock.call(ResourceSettings=[mock.sentinel.res_data])] * num_calls
        mock_svc.ModifyResourceSettings.has_calls(mock_calls)
        mock_sleep.has_calls(mock.call(1) * num_calls)

    def test_add_virt_resource(self):
        self._test_virt_method('AddResourceSettings', 3, 'add_virt_resource',
                               True, mock.sentinel.vm_path,
                               [mock.sentinel.res_data])

    def test_remove_virt_resource(self):
        self._test_virt_method('RemoveResourceSettings', 2,
                               'remove_virt_resource', False,
                               ResourceSettings=[mock.sentinel.res_path])

    def test_add_virt_feature(self):
        self._test_virt_method('AddFeatureSettings', 3, 'add_virt_feature',
                               True, mock.sentinel.vm_path,
                               [mock.sentinel.res_data])

    def test_modify_virt_feature(self):
        self._test_virt_method('ModifyFeatureSettings', 3,
                               'modify_virt_feature', False,
                               FeatureSettings=[mock.sentinel.res_data])

    def test_remove_virt_feature(self):
        self._test_virt_method('RemoveFeatureSettings', 2,
                               'remove_virt_feature', False,
                               FeatureSettings=[mock.sentinel.res_path])

    def _test_virt_method(self, vsms_method_name, return_count,
                          utils_method_name, with_mock_vm, *args, **kwargs):
        mock_svc = mock.MagicMock()
        self.jobutils._vs_man_svc_attr = mock_svc
        vsms_method = getattr(mock_svc, vsms_method_name)
        mock_rsd = self._mock_vsms_method(vsms_method, return_count)
        if with_mock_vm:
            mock_vm = mock.MagicMock()
            mock_vm.path_.return_value = mock.sentinel.vm_path
            getattr(self.jobutils, utils_method_name)(mock_rsd, mock_vm)
        else:
            getattr(self.jobutils, utils_method_name)(mock_rsd)

        if args:
            vsms_method.assert_called_once_with(*args)
        else:
            vsms_method.assert_called_once_with(**kwargs)

    def _mock_vsms_method(self, vsms_method, return_count):
        args = None
        if return_count == 3:
            args = (
                mock.sentinel.job_path, mock.MagicMock(), self._FAKE_RET_VAL)
        else:
            args = (mock.sentinel.job_path, self._FAKE_RET_VAL)

        vsms_method.return_value = args
        mock_res_setting_data = mock.MagicMock()
        mock_res_setting_data.GetText_.return_value = mock.sentinel.res_data
        mock_res_setting_data.path_.return_value = mock.sentinel.res_path

        self.jobutils.check_ret_val = mock.MagicMock()

        return mock_res_setting_data

    @mock.patch.object(jobutils.JobUtils, 'check_ret_val')
    def test_remove_multiple_virt_resources_not_found(self, mock_check_ret):
        excepinfo = [None] * 5 + [jobutils._utils._WBEM_E_NOT_FOUND]
        mock_check_ret.side_effect = exceptions.x_wmi(
            'expected error', com_error=mock.Mock(excepinfo=excepinfo))
        vsms_method = self.jobutils._vs_man_svc.RemoveResourceSettings
        vsms_method.return_value = (mock.sentinel.job, mock.sentinel.ret_val)
        mock_virt_res = mock.Mock()

        self.assertRaises(exceptions.NotFound,
                          self.jobutils.remove_virt_resource, mock_virt_res)

        vsms_method.assert_called_once_with(
            ResourceSettings=[mock_virt_res.path_.return_value])
        mock_check_ret.assert_called_once_with(mock.sentinel.ret_val,
                                               mock.sentinel.job)
