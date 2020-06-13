# Copyright 2015 Cloudbase Solutions Srl
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

from os_win import _utils
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import win32utils
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi import wintypes


@ddt.ddt
class Win32UtilsTestCase(test_base.BaseTestCase):
    def setUp(self):
        super(Win32UtilsTestCase, self).setUp()
        self._setup_lib_mocks()

        self._win32_utils = win32utils.Win32Utils()

        self.addCleanup(mock.patch.stopall)

    def _setup_lib_mocks(self):
        self._ctypes = mock.Mock()
        # This is used in order to easily make assertions on the variables
        # passed by reference.
        self._ctypes.byref = lambda x: (x, "byref")

        self._ctypes_patcher = mock.patch.multiple(
            win32utils, ctypes=self._ctypes)
        self._ctypes_patcher.start()

        mock.patch.multiple(win32utils,
                            kernel32=mock.DEFAULT,
                            create=True).start()

    @mock.patch.object(win32utils.Win32Utils, 'get_error_message')
    @mock.patch.object(win32utils.Win32Utils, 'get_last_error')
    def _test_run_and_check_output(self, mock_get_last_err, mock_get_err_msg,
                                   ret_val=0, expected_exc=None,
                                   **kwargs):
        self._ctypes_patcher.stop()

        mock_func = mock.Mock()
        mock_func.return_value = ret_val

        if expected_exc:
            self.assertRaises(expected_exc,
                              self._win32_utils.run_and_check_output,
                              mock_func,
                              mock.sentinel.arg,
                              kwarg=mock.sentinel.kwarg,
                              **kwargs)
        else:
            actual_ret_val = self._win32_utils.run_and_check_output(
                mock_func,
                mock.sentinel.arg,
                kwarg=mock.sentinel.kwarg,
                **kwargs)
            self.assertEqual(ret_val, actual_ret_val)

        mock_func.assert_called_once_with(mock.sentinel.arg,
                                          kwarg=mock.sentinel.kwarg)

        return mock_get_last_err, mock_get_err_msg

    def test_run_and_check_output(self):
        self._test_run_and_check_output()

    def test_run_and_check_output_fail_on_nonzero_ret_val(self):
        ret_val = 1

        (mock_get_last_err,
         mock_get_err_msg) = self._test_run_and_check_output(
            ret_val=ret_val,
            expected_exc=exceptions.VHDWin32APIException,
            failure_exc=exceptions.VHDWin32APIException)

        mock_get_err_msg.assert_called_once_with(ret_val)

    def test_run_and_check_output_explicit_error_ret_vals(self):
        ret_val = 1
        error_ret_vals = [ret_val]

        (mock_get_last_err,
         mock_get_err_msg) = self._test_run_and_check_output(
            ret_val=ret_val,
            error_ret_vals=error_ret_vals,
            ret_val_is_err_code=False,
            expected_exc=exceptions.Win32Exception)

        mock_get_err_msg.assert_called_once_with(
            win32utils.ctypes.c_ulong(mock_get_last_err).value)

    def test_run_and_check_output_ignored_error(self):
        ret_val = 1
        ignored_err_codes = [ret_val]

        self._test_run_and_check_output(ret_val=ret_val,
                                        ignored_error_codes=ignored_err_codes)

    def test_run_and_check_output_kernel32_lib_func(self):
        ret_val = 0
        self._test_run_and_check_output(ret_val=ret_val,
                                        expected_exc=exceptions.Win32Exception,
                                        kernel32_lib_func=True)

    def test_run_and_check_output_with_err_msg_dict(self):
        self._ctypes_patcher.stop()

        err_code = 1
        err_msg = 'fake_err_msg'
        err_msg_dict = {err_code: err_msg}

        mock_func = mock.Mock()
        mock_func.return_value = err_code

        try:
            self._win32_utils.run_and_check_output(mock_func,
                                                   mock.sentinel.arg,
                                                   error_msg_src=err_msg_dict)
        except Exception as ex:
            self.assertIsInstance(ex, exceptions.Win32Exception)
            self.assertIn(err_msg, ex.message)

    @mock.patch.object(win32utils.Win32Utils, '_run_and_check_output')
    def test_run_and_check_output_eventlet_nb_mode_disabled(self, mock_helper):
        self._win32_utils.run_and_check_output(
            mock.sentinel.func,
            mock.sentinel.arg,
            eventlet_nonblocking_mode=False)
        mock_helper.assert_called_once_with(mock.sentinel.func,
                                            mock.sentinel.arg)

    @mock.patch.object(_utils, 'avoid_blocking_call')
    def test_run_and_check_output_eventlet_nb_mode_enabled(self, mock_helper):
        self._win32_utils.run_and_check_output(
            mock.sentinel.func,
            mock.sentinel.arg,
            eventlet_nonblocking_mode=True)
        mock_helper.assert_called_once_with(
            self._win32_utils._run_and_check_output,
            mock.sentinel.func,
            mock.sentinel.arg)

    def test_get_error_message(self):
        err_msg = self._win32_utils.get_error_message(mock.sentinel.err_code)

        fake_msg_buff = win32utils.ctypes.c_char_p.return_value

        expected_flags = (w_const.FORMAT_MESSAGE_FROM_SYSTEM |
                          w_const.FORMAT_MESSAGE_ALLOCATE_BUFFER |
                          w_const.FORMAT_MESSAGE_IGNORE_INSERTS)

        win32utils.kernel32.FormatMessageA.assert_called_once_with(
            expected_flags, None, mock.sentinel.err_code, 0,
            win32utils.ctypes.byref(fake_msg_buff), 0, None)
        self.assertEqual(fake_msg_buff.value, err_msg)

    def test_get_last_error(self):
        last_err = self._win32_utils.get_last_error()

        self.assertEqual(win32utils.kernel32.GetLastError.return_value,
                         last_err)
        win32utils.kernel32.SetLastError.assert_called_once_with(0)

    @ddt.data(0, 1)
    @mock.patch.object(win32utils.LOG, 'exception')
    def test_local_free(self, ret_val, mock_log_exc):
        mock_localfree = win32utils.kernel32.LocalFree
        mock_localfree.return_value = ret_val

        self._win32_utils.local_free(mock.sentinel.handle)

        mock_localfree.assert_any_call(mock.sentinel.handle)
        self.assertEqual(bool(ret_val), mock_log_exc.called)

    @mock.patch.object(win32utils.Win32Utils, 'run_and_check_output')
    def test_wait_for_multiple_objects(self, mock_helper):
        fake_handles = [10, 11]

        ret_val = self._win32_utils.wait_for_multiple_objects(
            fake_handles, mock.sentinel.wait_all, mock.sentinel.milliseconds)

        mock_helper.assert_called_once_with(
            win32utils.kernel32.WaitForMultipleObjects,
            len(fake_handles),
            mock.ANY,
            mock.sentinel.wait_all,
            mock.sentinel.milliseconds,
            kernel32_lib_func=True,
            error_ret_vals=[w_const.WAIT_FAILED])
        self.assertEqual(mock_helper.return_value, ret_val)

        handles_arg = mock_helper.call_args_list[0][0][2]
        self.assertIsInstance(handles_arg,
                              wintypes.HANDLE * len(fake_handles))
        self.assertEqual(fake_handles, handles_arg[:])

    @mock.patch.object(win32utils.Win32Utils, 'run_and_check_output')
    def test_wait_for_multiple_objects_timeout(self, mock_helper):
        fake_handles = [10]
        mock_helper.return_value = w_const.ERROR_WAIT_TIMEOUT

        self.assertRaises(
            exceptions.Timeout,
            self._win32_utils.wait_for_multiple_objects,
            fake_handles, mock.sentinel.wait_all,
            mock.sentinel.milliseconds)

    @mock.patch.object(win32utils.Win32Utils, 'run_and_check_output')
    def test_wait_for_single_object(self, mock_helper):
        ret_val = self._win32_utils.wait_for_single_object(
            mock.sentinel.handle, mock.sentinel.milliseconds)

        mock_helper.assert_called_once_with(
            win32utils.kernel32.WaitForSingleObject,
            mock.sentinel.handle,
            mock.sentinel.milliseconds,
            kernel32_lib_func=True,
            error_ret_vals=[w_const.WAIT_FAILED])
        self.assertEqual(mock_helper.return_value, ret_val)

    @mock.patch.object(win32utils.Win32Utils, 'run_and_check_output')
    def test_wait_for_single_object_timeout(self, mock_helper):
        mock_helper.return_value = w_const.ERROR_WAIT_TIMEOUT

        self.assertRaises(
            exceptions.Timeout,
            self._win32_utils.wait_for_single_object,
            mock.sentinel.timeout,
            mock.sentinel.milliseconds)
