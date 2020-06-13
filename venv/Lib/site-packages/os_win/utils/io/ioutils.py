# Copyright 2014 Cloudbase Solutions Srl
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
import struct
import sys

from eventlet import patcher
from oslo_log import log as logging
from oslo_utils import units
import six

from os_win import _utils
from os_win import constants
from os_win import exceptions
from os_win.utils import win32utils
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi import libs as w_lib
from os_win.utils.winapi import wintypes

kernel32 = w_lib.get_shared_lib_handle(w_lib.KERNEL32)

LOG = logging.getLogger(__name__)

# Avoid using six.moves.queue as we need a non monkey patched class
if sys.version_info > (3, 0):
    Queue = patcher.original('queue')
else:
    Queue = patcher.original('Queue')

WAIT_PIPE_DEFAULT_TIMEOUT = 5  # seconds
WAIT_IO_COMPLETION_TIMEOUT = 2 * units.k
WAIT_INFINITE_TIMEOUT = 0xFFFFFFFF

IO_QUEUE_TIMEOUT = 2
IO_QUEUE_BURST_TIMEOUT = 0.05


class IOUtils(object):
    """Asyncronous IO helper class."""

    def __init__(self):
        self._win32_utils = win32utils.Win32Utils()

    def _run_and_check_output(self, *args, **kwargs):
        eventlet_blocking_mode = kwargs.get('eventlet_nonblocking_mode', False)
        kwargs.update(kernel32_lib_func=True,
                      failure_exc=exceptions.Win32IOException,
                      eventlet_nonblocking_mode=eventlet_blocking_mode)
        return self._win32_utils.run_and_check_output(*args, **kwargs)

    def create_pipe(self, security_attributes=None, size=0,
                    inherit_handle=False):
        """Create an anonymous pipe.

        The main advantage of this method over os.pipe is that it allows
        creating inheritable pipe handles (which is flawed on most Python
        versions).
        """
        r = wintypes.HANDLE()
        w = wintypes.HANDLE()

        if inherit_handle and not security_attributes:
            security_attributes = wintypes.SECURITY_ATTRIBUTES()
            security_attributes.bInheritHandle = inherit_handle
            security_attributes.nLength = ctypes.sizeof(security_attributes)

        self._run_and_check_output(
            kernel32.CreatePipe,
            ctypes.byref(r),
            ctypes.byref(w),
            ctypes.byref(security_attributes) if security_attributes else None,
            size)

        return r.value, w.value

    @_utils.retry_decorator(exceptions=exceptions.Win32IOException,
                            max_sleep_time=2)
    def wait_named_pipe(self, pipe_name, timeout=WAIT_PIPE_DEFAULT_TIMEOUT):
        """Wait a given amount of time for a pipe to become available."""
        self._run_and_check_output(kernel32.WaitNamedPipeW,
                                   ctypes.c_wchar_p(pipe_name),
                                   timeout * units.k)

    def open(self, path, desired_access=0, share_mode=0,
             creation_disposition=0, flags_and_attributes=0):
        error_ret_vals = [w_const.INVALID_HANDLE_VALUE]
        handle = self._run_and_check_output(kernel32.CreateFileW,
                                            ctypes.c_wchar_p(path),
                                            desired_access,
                                            share_mode,
                                            None,
                                            creation_disposition,
                                            flags_and_attributes,
                                            None,
                                            error_ret_vals=error_ret_vals)
        return handle

    def close_handle(self, handle):
        self._run_and_check_output(kernel32.CloseHandle, handle)

    def cancel_io(self, handle, overlapped_structure=None,
                  ignore_invalid_handle=False):
        """Cancels pending IO on specified handle.

        If an overlapped structure is passed, only the IO requests that
        were issued with the specified overlapped structure are canceled.
        """
        # Ignore errors thrown when there are no requests
        # to be canceled.
        ignored_error_codes = [w_const.ERROR_NOT_FOUND]
        if ignore_invalid_handle:
            ignored_error_codes.append(w_const.ERROR_INVALID_HANDLE)
        lp_overlapped = (ctypes.byref(overlapped_structure)
                         if overlapped_structure else None)

        self._run_and_check_output(kernel32.CancelIoEx,
                                   handle,
                                   lp_overlapped,
                                   ignored_error_codes=ignored_error_codes)

    def _wait_io_completion(self, event):
        # In order to cancel this, we simply set the event.
        self._run_and_check_output(kernel32.WaitForSingleObjectEx,
                                   event, WAIT_INFINITE_TIMEOUT,
                                   True, error_ret_vals=[w_const.WAIT_FAILED])

    def set_event(self, event):
        self._run_and_check_output(kernel32.SetEvent, event)

    def _reset_event(self, event):
        self._run_and_check_output(kernel32.ResetEvent, event)

    def _create_event(self, event_attributes=None, manual_reset=True,
                      initial_state=False, name=None):
        return self._run_and_check_output(kernel32.CreateEventW,
                                          event_attributes, manual_reset,
                                          initial_state, name,
                                          error_ret_vals=[None])

    def get_completion_routine(self, callback=None):
        def _completion_routine(error_code, num_bytes, lpOverLapped):
            """Sets the completion event and executes callback, if passed."""
            overlapped = ctypes.cast(lpOverLapped,
                                     wintypes.LPOVERLAPPED).contents
            self.set_event(overlapped.hEvent)

            if callback:
                callback(num_bytes)

        return wintypes.LPOVERLAPPED_COMPLETION_ROUTINE(_completion_routine)

    def get_new_overlapped_structure(self):
        """Structure used for asynchronous IO operations."""
        # Event used for signaling IO completion
        hEvent = self._create_event()

        overlapped_structure = wintypes.OVERLAPPED()
        overlapped_structure.hEvent = hEvent
        return overlapped_structure

    def read(self, handle, buff, num_bytes,
             overlapped_structure, completion_routine):
        self._reset_event(overlapped_structure.hEvent)
        self._run_and_check_output(kernel32.ReadFileEx,
                                   handle, buff, num_bytes,
                                   ctypes.byref(overlapped_structure),
                                   completion_routine)
        self._wait_io_completion(overlapped_structure.hEvent)

    def read_file(self, handle, buff, num_bytes, overlapped_structure=None):
        # Similar to IOUtils.read, but intended for synchronous operations.
        num_bytes_read = wintypes.DWORD(0)
        overlapped_structure_ref = (
            ctypes.byref(overlapped_structure) if overlapped_structure
            else None)
        self._run_and_check_output(kernel32.ReadFile,
                                   handle, buff, num_bytes,
                                   ctypes.byref(num_bytes_read),
                                   overlapped_structure_ref)
        return num_bytes_read.value

    def write(self, handle, buff, num_bytes,
              overlapped_structure, completion_routine):
        self._reset_event(overlapped_structure.hEvent)
        self._run_and_check_output(kernel32.WriteFileEx,
                                   handle, buff, num_bytes,
                                   ctypes.byref(overlapped_structure),
                                   completion_routine)
        self._wait_io_completion(overlapped_structure.hEvent)

    def write_file(self, handle, buff, num_bytes, overlapped_structure=None):
        # Similar to IOUtils.write, but intended for synchronous operations.
        num_bytes_written = wintypes.DWORD(0)
        overlapped_structure_ref = (
            ctypes.byref(overlapped_structure) if overlapped_structure
            else None)
        self._run_and_check_output(kernel32.WriteFile,
                                   handle, buff, num_bytes,
                                   ctypes.byref(num_bytes_written),
                                   overlapped_structure_ref)
        return num_bytes_written.value

    @classmethod
    def get_buffer(cls, buff_size, data=None):
        buff = (ctypes.c_ubyte * buff_size)()
        if data:
            cls.write_buffer_data(buff, data)
        return buff

    @staticmethod
    def get_buffer_data(buff, num_bytes):
        return bytes(bytearray(buff[:num_bytes]))

    @staticmethod
    def write_buffer_data(buff, data):
        for i, c in enumerate(data):
            buff[i] = struct.unpack('B', six.b(c))[0]


class IOQueue(Queue.Queue, object):
    def __init__(self, client_connected):
        Queue.Queue.__init__(self)
        self._client_connected = client_connected

    def get(self, timeout=IO_QUEUE_TIMEOUT, continue_on_timeout=True):
        while self._client_connected.isSet():
            try:
                return Queue.Queue.get(self, timeout=timeout)
            except Queue.Empty:
                if continue_on_timeout:
                    continue
                else:
                    break

    def put(self, item, timeout=IO_QUEUE_TIMEOUT):
        while self._client_connected.isSet():
            try:
                return Queue.Queue.put(self, item, timeout=timeout)
            except Queue.Full:
                continue

    def get_burst(self, timeout=IO_QUEUE_TIMEOUT,
                  burst_timeout=IO_QUEUE_BURST_TIMEOUT,
                  max_size=constants.SERIAL_CONSOLE_BUFFER_SIZE):
        # Get as much data as possible from the queue
        # to avoid sending small chunks.
        data = self.get(timeout=timeout)

        while data and len(data) <= max_size:
            chunk = self.get(timeout=burst_timeout,
                             continue_on_timeout=False)
            if chunk:
                data += chunk
            else:
                break
        return data
