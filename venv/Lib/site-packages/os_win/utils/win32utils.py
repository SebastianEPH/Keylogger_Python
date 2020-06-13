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

import ctypes

from oslo_log import log as logging

from os_win import _utils
from os_win import exceptions
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi import libs as w_lib
from os_win.utils.winapi import wintypes

kernel32 = w_lib.get_shared_lib_handle(w_lib.KERNEL32)

LOG = logging.getLogger(__name__)


class Win32Utils(object):
    def __init__(self):
        self._kernel32_lib_func_opts = dict(error_on_nonzero_ret_val=False,
                                            ret_val_is_err_code=False)

    def run_and_check_output(self, *args, **kwargs):
        eventlet_nonblocking_mode = kwargs.pop(
            'eventlet_nonblocking_mode', True)

        if eventlet_nonblocking_mode:
            # We have to make sure that the invoked function as well as the
            # subsequent error handling are performed within the same thread.
            return _utils.avoid_blocking_call(
                self._run_and_check_output, *args, **kwargs)
        else:
            return self._run_and_check_output(*args, **kwargs)

    def _run_and_check_output(self, func, *args, **kwargs):
        """Convenience helper method for running Win32 API methods."""
        kernel32_lib_func = kwargs.pop('kernel32_lib_func', False)
        if kernel32_lib_func:
            kwargs['error_ret_vals'] = kwargs.get('error_ret_vals', [0])
            kwargs.update(self._kernel32_lib_func_opts)

        ignored_error_codes = kwargs.pop('ignored_error_codes', [])

        # A list of return values signaling that the operation failed.
        error_ret_vals = kwargs.pop('error_ret_vals', [])
        error_on_nonzero_ret_val = kwargs.pop('error_on_nonzero_ret_val', True)
        # Note(lpetrut): In the future, we may use functions that can
        # return information/warning HRESULTs that should not be
        # treated as exceptions.
        ret_val_is_err_code = kwargs.pop('ret_val_is_err_code', True)

        # The exception raised when the Win32 API function fails. The
        # exception must inherit Win32Exception.
        failure_exc = kwargs.pop('failure_exc', exceptions.Win32Exception)
        # Expects a dict containing error codes as keys and the
        # according error message codes as values. If the error code is
        # not present in this dict, this method will search the System
        # message table.
        error_msg_src = kwargs.pop('error_msg_src', {})

        ret_val = func(*args, **kwargs)

        func_failed = (error_on_nonzero_ret_val and ret_val) or (
            ret_val in error_ret_vals)

        if func_failed:
            error_code = (ret_val
                          if ret_val_is_err_code else self.get_last_error())
            error_code = ctypes.c_ulong(error_code).value
            if error_code not in ignored_error_codes:
                error_message = error_msg_src.get(error_code,
                                                  self.get_error_message(
                                                      error_code))
                func_name = getattr(func, '__name__', '')
                raise failure_exc(error_code=error_code,
                                  error_message=error_message,
                                  func_name=func_name)
        return ret_val

    @staticmethod
    def get_error_message(error_code):
        message_buffer = ctypes.c_char_p()

        kernel32.FormatMessageA(
            w_const.FORMAT_MESSAGE_FROM_SYSTEM |
            w_const.FORMAT_MESSAGE_ALLOCATE_BUFFER |
            w_const.FORMAT_MESSAGE_IGNORE_INSERTS,
            None, error_code, 0, ctypes.byref(message_buffer), 0, None)

        error_message = message_buffer.value
        kernel32.LocalFree(message_buffer)
        return error_message

    def get_last_error(self):
        error_code = kernel32.GetLastError()
        kernel32.SetLastError(0)
        return error_code

    def local_free(self, handle):
        try:
            self._run_and_check_output(kernel32.LocalFree, handle)
        except exceptions.Win32Exception:
            LOG.exception("Could not deallocate memory. "
                          "There could be a memory leak.")

    def close_handle(self, handle):
        kernel32.CloseHandle(handle)

    def wait_for_multiple_objects(self, handles, wait_all=True,
                                  milliseconds=w_const.INFINITE):
        handle_array = (wintypes.HANDLE * len(handles))(*handles)
        ret_val = self.run_and_check_output(
            kernel32.WaitForMultipleObjects,
            len(handles),
            handle_array,
            wait_all,
            milliseconds,
            kernel32_lib_func=True,
            error_ret_vals=[w_const.WAIT_FAILED])
        if ret_val == w_const.ERROR_WAIT_TIMEOUT:
            raise exceptions.Timeout()

        return ret_val

    def wait_for_single_object(self, handle,
                               milliseconds=w_const.INFINITE):
        ret_val = self.run_and_check_output(
            kernel32.WaitForSingleObject,
            handle,
            milliseconds,
            kernel32_lib_func=True,
            error_ret_vals=[w_const.WAIT_FAILED])
        if ret_val == w_const.ERROR_WAIT_TIMEOUT:
            raise exceptions.Timeout()

        return ret_val
