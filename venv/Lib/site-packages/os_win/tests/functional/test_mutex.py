# Copyright 2019 Cloudbase Solutions Srl
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

import threading
import uuid

from os_win import exceptions
from os_win.tests.functional import test_base
from os_win.utils import processutils


class MutexTestCase(test_base.OsWinBaseFunctionalTestCase):
    def setUp(self):
        super(MutexTestCase, self).setUp()

        mutex_name = str(uuid.uuid4())
        self._mutex = processutils.Mutex(name=mutex_name)

        self.addCleanup(self._mutex.close)

    def acquire_mutex_in_separate_thread(self, mutex):
        # We'll wait for a signal before releasing the mutex.
        stop_event = threading.Event()

        def target():
            mutex.acquire()

            stop_event.wait()

            mutex.release()

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()

        return thread, stop_event

    def test_already_acquired_mutex(self):
        thread, stop_event = self.acquire_mutex_in_separate_thread(
            self._mutex)

        # We shouldn't be able to acquire a mutex held by a
        # different thread.
        self.assertFalse(self._mutex.acquire(timeout_ms=0))

        stop_event.set()

        # We should now be able to acquire the mutex.
        # We're using a timeout, giving the other thread some
        # time to release it.
        self.assertTrue(self._mutex.acquire(timeout_ms=2000))

    def test_release_unacquired_mutex(self):
        self.assertRaises(exceptions.Win32Exception,
                          self._mutex.release)

    def test_multiple_acquire(self):
        # The mutex owner should be able to acquire it multiple times.
        self._mutex.acquire(timeout_ms=0)
        self._mutex.acquire(timeout_ms=0)

        self._mutex.release()
        self._mutex.release()
