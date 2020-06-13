# Copyright 2017 Cloudbase Solutions Srl
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

import ddt
import mock

from os_win.tests.unit import test_base
from os_win.utils import processutils
from os_win.utils.winapi import constants as w_const


@ddt.ddt
class ProcessUtilsTestCase(test_base.OsWinBaseTestCase):

    _autospec_classes = [
        processutils.win32utils.Win32Utils,
    ]

    def setUp(self):
        super(ProcessUtilsTestCase, self).setUp()
        self._setup_lib_mocks()

        self._procutils = processutils.ProcessUtils()
        self._win32_utils = self._procutils._win32_utils
        self._mock_run = self._win32_utils.run_and_check_output

        self.addCleanup(mock.patch.stopall)

    def _setup_lib_mocks(self):
        self._ctypes = mock.Mock()
        # This is used in order to easily make assertions on the variables
        # passed by reference.
        self._ctypes.byref = lambda x: (x, "byref")
        self._ctypes.c_wchar_p = lambda x: (x, 'c_wchar_p')
        self._ctypes.sizeof = lambda x: (x, 'sizeof')

        self._ctypes_patcher = mock.patch.multiple(
            processutils, ctypes=self._ctypes)
        self._ctypes_patcher.start()

        self._mock_kernel32 = mock.Mock()

        mock.patch.multiple(processutils,
                            kernel32=self._mock_kernel32).start()

    def test_create_job_object(self):
        job_handle = self._procutils.create_job_object(mock.sentinel.name)

        self._mock_run.assert_called_once_with(
            self._mock_kernel32.CreateJobObjectW,
            None,
            self._ctypes.c_wchar_p(mock.sentinel.name),
            error_ret_vals=[None],
            kernel32_lib_func=True)
        self.assertEqual(self._mock_run.return_value, job_handle)

    def test_set_information_job_object(self):
        self._procutils.set_information_job_object(
            mock.sentinel.job_handle,
            mock.sentinel.job_info_class,
            mock.sentinel.job_info)

        self._mock_run.assert_called_once_with(
            self._mock_kernel32.SetInformationJobObject,
            mock.sentinel.job_handle,
            mock.sentinel.job_info_class,
            self._ctypes.byref(mock.sentinel.job_info),
            self._ctypes.sizeof(mock.sentinel.job_info),
            kernel32_lib_func=True)

    def test_assign_process_to_job_object(self):
        self._procutils.assign_process_to_job_object(
            mock.sentinel.job_handle,
            mock.sentinel.process_handle)

        self._mock_run.assert_called_once_with(
            self._mock_kernel32.AssignProcessToJobObject,
            mock.sentinel.job_handle,
            mock.sentinel.process_handle,
            kernel32_lib_func=True)

    def test_open_process(self):
        process_handle = self._procutils.open_process(
            mock.sentinel.pid,
            mock.sentinel.desired_access,
            mock.sentinel.inherit_handle)

        self._mock_run.assert_called_once_with(
            self._mock_kernel32.OpenProcess,
            mock.sentinel.desired_access,
            mock.sentinel.inherit_handle,
            mock.sentinel.pid,
            error_ret_vals=[None],
            kernel32_lib_func=True)
        self.assertEqual(self._mock_run.return_value, process_handle)

    @ddt.data({},
              {'assign_job_exc': Exception})
    @ddt.unpack
    @mock.patch.object(processutils.ProcessUtils, 'open_process')
    @mock.patch.object(processutils.ProcessUtils, 'create_job_object')
    @mock.patch.object(processutils.ProcessUtils,
                       'set_information_job_object')
    @mock.patch.object(processutils.ProcessUtils,
                       'assign_process_to_job_object')
    @mock.patch.object(processutils.kernel32_struct,
                       'JOBOBJECT_EXTENDED_LIMIT_INFORMATION')
    def test_kill_process_on_job_close(self, mock_job_limit_struct,
                                       mock_assign_job,
                                       mock_set_job_info,
                                       mock_create_job,
                                       mock_open_process,
                                       assign_job_exc=None):
        mock_assign_job.side_effect = assign_job_exc
        mock_open_process.return_value = mock.sentinel.process_handle
        mock_create_job.return_value = mock.sentinel.job_handle

        if assign_job_exc:
            self.assertRaises(assign_job_exc,
                              self._procutils.kill_process_on_job_close,
                              mock.sentinel.pid)
        else:
            self._procutils.kill_process_on_job_close(mock.sentinel.pid)

        mock_open_process.assert_called_once_with(
            mock.sentinel.pid,
            w_const.PROCESS_SET_QUOTA | w_const.PROCESS_TERMINATE)
        mock_create_job.assert_called_once_with()

        mock_job_limit_struct.assert_called_once_with()
        mock_job_limit = mock_job_limit_struct.return_value
        self.assertEqual(w_const.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
                         mock_job_limit.BasicLimitInformation.LimitFlags)

        mock_set_job_info.assert_called_once_with(
            mock.sentinel.job_handle,
            w_const.JobObjectExtendedLimitInformation,
            mock_job_limit)
        mock_assign_job.assert_called_once_with(
            mock.sentinel.job_handle,
            mock.sentinel.process_handle)

        exp_closed_handles = [mock.sentinel.process_handle]
        if assign_job_exc:
            exp_closed_handles.append(mock.sentinel.job_handle)

        self._win32_utils.close_handle.assert_has_calls(
            [mock.call(handle) for handle in exp_closed_handles])

    @ddt.data({},
              {'wait_exc': Exception})
    @ddt.unpack
    @mock.patch.object(processutils.ProcessUtils, 'open_process')
    def test_wait_for_multiple_processes(self, mock_open_process,
                                         wait_exc=None):
        pids = [mock.sentinel.pid0, mock.sentinel.pid1]
        phandles = [mock.sentinel.process_handle_0,
                    mock.sentinel.process_handle_1]

        mock_wait = self._win32_utils.wait_for_multiple_objects
        mock_wait.side_effect = wait_exc
        mock_open_process.side_effect = phandles

        if wait_exc:
            self.assertRaises(wait_exc,
                              self._procutils.wait_for_multiple_processes,
                              pids,
                              mock.sentinel.wait_all,
                              mock.sentinel.milliseconds)
        else:
            self._procutils.wait_for_multiple_processes(
                pids,
                mock.sentinel.wait_all,
                mock.sentinel.milliseconds)

        mock_open_process.assert_has_calls(
            [mock.call(pid,
                       desired_access=w_const.SYNCHRONIZE)
             for pid in pids])
        self._win32_utils.close_handle.assert_has_calls(
            [mock.call(handle) for handle in phandles])

        mock_wait.assert_called_once_with(phandles,
                                          mock.sentinel.wait_all,
                                          mock.sentinel.milliseconds)

    def test_create_mutex(self):
        handle = self._procutils.create_mutex(
            mock.sentinel.name, mock.sentinel.owner,
            mock.sentinel.sec_attr)

        self.assertEqual(self._mock_run.return_value, handle)
        self._mock_run.assert_called_once_with(
            self._mock_kernel32.CreateMutexW,
            self._ctypes.byref(mock.sentinel.sec_attr),
            mock.sentinel.owner,
            mock.sentinel.name,
            kernel32_lib_func=True)

    def test_release_mutex(self):
        self._procutils.release_mutex(mock.sentinel.handle)

        self._mock_run.assert_called_once_with(
            self._mock_kernel32.ReleaseMutex,
            mock.sentinel.handle,
            kernel32_lib_func=True)
