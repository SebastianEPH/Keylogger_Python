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

import ctypes

from oslo_log import log as logging

from os_win import exceptions
from os_win.utils import win32utils
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi import libs as w_lib
from os_win.utils.winapi.libs import kernel32 as kernel32_struct

kernel32 = w_lib.get_shared_lib_handle(w_lib.KERNEL32)

LOG = logging.getLogger(__name__)


class ProcessUtils(object):
    def __init__(self):
        self._win32_utils = win32utils.Win32Utils()

    def _run_and_check_output(self, *args, **kwargs):
        kwargs.update(kernel32_lib_func=True)
        return self._win32_utils.run_and_check_output(*args, **kwargs)

    def create_job_object(self, name=None):
        """Create or open a job object.

        :param name: (Optional) the job name.
        :returns: a handle of the created job.
        """
        pname = None if name is None else ctypes.c_wchar_p(name)
        return self._run_and_check_output(kernel32.CreateJobObjectW,
                                          None,  # job security attributes
                                          pname,
                                          error_ret_vals=[None])

    def set_information_job_object(self, job_handle, job_object_info_class,
                                   job_object_info):
        self._run_and_check_output(kernel32.SetInformationJobObject,
                                   job_handle,
                                   job_object_info_class,
                                   ctypes.byref(job_object_info),
                                   ctypes.sizeof(job_object_info))

    def assign_process_to_job_object(self, job_handle, process_handle):
        self._run_and_check_output(kernel32.AssignProcessToJobObject,
                                   job_handle, process_handle)

    def open_process(self, pid, desired_access, inherit_handle=False):
        """Open an existing process."""
        return self._run_and_check_output(kernel32.OpenProcess,
                                          desired_access,
                                          inherit_handle,
                                          pid,
                                          error_ret_vals=[None])

    def kill_process_on_job_close(self, pid):
        """Associates a new job to the specified process.

        The process is immediately killed when the last job handle is closed.
        This mechanism can be useful when ensuring that child processes get
        killed along with a parent process.

        This method does not check if the specified process is already part of
        a job. Starting with WS 2012, nested jobs are available.

        :returns: the job handle, if a job was successfully created and
                  associated with the process, otherwise "None".
        """

        process_handle = None
        job_handle = None
        job_associated = False

        try:
            desired_process_access = (w_const.PROCESS_SET_QUOTA |
                                      w_const.PROCESS_TERMINATE)
            process_handle = self.open_process(pid, desired_process_access)
            job_handle = self.create_job_object()

            job_info = kernel32_struct.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            job_info.BasicLimitInformation.LimitFlags = (
                w_const.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
            job_info_class = w_const.JobObjectExtendedLimitInformation

            self.set_information_job_object(job_handle,
                                            job_info_class,
                                            job_info)

            self.assign_process_to_job_object(job_handle, process_handle)
            job_associated = True
        finally:
            if process_handle:
                self._win32_utils.close_handle(process_handle)

            if not job_associated and job_handle:
                # We have an unassociated job object. Closing the handle
                # will also destroy the job object.
                self._win32_utils.close_handle(job_handle)

        return job_handle

    def wait_for_multiple_processes(self, pids, wait_all=True,
                                    milliseconds=w_const.INFINITE):
        handles = []
        try:
            for pid in pids:
                handle = self.open_process(pid,
                                           desired_access=w_const.SYNCHRONIZE)
                handles.append(handle)

            return self._win32_utils.wait_for_multiple_objects(
                handles, wait_all, milliseconds)
        finally:
            for handle in handles:
                self._win32_utils.close_handle(handle)

    def create_mutex(self, name=None, initial_owner=False,
                     security_attributes=None):
        sec_attr_ref = (ctypes.byref(security_attributes)
                        if security_attributes else None)
        return self._run_and_check_output(
            kernel32.CreateMutexW,
            sec_attr_ref,
            initial_owner,
            name)

    def release_mutex(self, handle):
        return self._run_and_check_output(
            kernel32.ReleaseMutex,
            handle)


class Mutex(object):
    def __init__(self, name=None):
        self.name = name

        self._processutils = ProcessUtils()
        self._win32_utils = win32utils.Win32Utils()

        # This is supposed to be a simple interface.
        # We're not exposing the "initial_owner" flag,
        # nor are we informing the caller if the mutex
        # already exists.
        self._handle = self._processutils.create_mutex(
            self.name)

    def acquire(self, timeout_ms=w_const.INFINITE):
        try:
            self._win32_utils.wait_for_single_object(
                self._handle, timeout_ms)
            return True
        except exceptions.Timeout:
            return False

    def release(self):
        self._processutils.release_mutex(self._handle)

    def close(self):
        if self._handle:
            self._win32_utils.close_handle(self._handle)
        self._handle = None

    __del__ = close

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
