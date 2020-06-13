# Copyright 2015 Cloudbase Solutions SRL
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
Unit tests for the os_win._utils module.
"""

import ddt
import mock

from os_win import _utils
from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base


@ddt.ddt
class UtilsTestCase(test_base.BaseTestCase):

    @mock.patch('oslo_concurrency.processutils.execute')
    def test_execute(self, mock_execute):
        _utils.execute(mock.sentinel.cmd, kwarg=mock.sentinel.kwarg)
        mock_execute.assert_called_once_with(mock.sentinel.cmd,
                                             kwarg=mock.sentinel.kwarg)

    def test_parse_server_string(self):
        result = _utils.parse_server_string('::1')
        self.assertEqual(('::1', ''), result)
        result = _utils.parse_server_string('[::1]:8773')
        self.assertEqual(('::1', '8773'), result)
        result = _utils.parse_server_string('2001:db8::192.168.1.1')
        self.assertEqual(('2001:db8::192.168.1.1', ''), result)
        result = _utils.parse_server_string('[2001:db8::192.168.1.1]:8773')
        self.assertEqual(('2001:db8::192.168.1.1', '8773'), result)
        result = _utils.parse_server_string('192.168.1.1')
        self.assertEqual(('192.168.1.1', ''), result)
        result = _utils.parse_server_string('192.168.1.2:8773')
        self.assertEqual(('192.168.1.2', '8773'), result)
        result = _utils.parse_server_string('192.168.1.3')
        self.assertEqual(('192.168.1.3', ''), result)
        result = _utils.parse_server_string('www.example.com:8443')
        self.assertEqual(('www.example.com', '8443'), result)
        result = _utils.parse_server_string('www.example.com')
        self.assertEqual(('www.example.com', ''), result)
        # error case
        result = _utils.parse_server_string('www.exa:mple.com:8443')
        self.assertEqual(('', ''), result)
        result = _utils.parse_server_string('')
        self.assertEqual(('', ''), result)

    def _get_fake_func_with_retry_decorator(self, side_effect,
                                            decorator=_utils.retry_decorator,
                                            *args, **kwargs):
        func_side_effect = mock.Mock(side_effect=side_effect)

        @decorator(*args, **kwargs)
        def fake_func(*_args, **_kwargs):
            return func_side_effect(*_args, **_kwargs)

        return fake_func, func_side_effect

    @mock.patch.object(_utils, 'time')
    def test_retry_decorator(self, mock_time):
        err_code = 1
        max_retry_count = 5
        max_sleep_time = 2
        timeout = max_retry_count + 1
        mock_time.time.side_effect = range(timeout)

        raised_exc = exceptions.Win32Exception(message='fake_exc',
                                               error_code=err_code)
        side_effect = [raised_exc] * max_retry_count
        side_effect.append(mock.sentinel.ret_val)

        (fake_func,
         fake_func_side_effect) = self._get_fake_func_with_retry_decorator(
            error_codes=err_code,
            exceptions=exceptions.Win32Exception,
            max_retry_count=max_retry_count,
            max_sleep_time=max_sleep_time,
            timeout=timeout,
            side_effect=side_effect)

        ret_val = fake_func(mock.sentinel.arg,
                            kwarg=mock.sentinel.kwarg)
        self.assertEqual(mock.sentinel.ret_val, ret_val)
        fake_func_side_effect.assert_has_calls(
            [mock.call(mock.sentinel.arg, kwarg=mock.sentinel.kwarg)] *
            (max_retry_count + 1))
        self.assertEqual(max_retry_count + 1, mock_time.time.call_count)
        mock_time.sleep.assert_has_calls(
            [mock.call(sleep_time)
             for sleep_time in [1, 2, 2, 2, 1]])

    @mock.patch.object(_utils, 'time')
    def _test_retry_decorator_exceeded(self, mock_time, expected_try_count,
                                       mock_time_side_eff=None,
                                       timeout=None, max_retry_count=None):
        raised_exc = exceptions.Win32Exception(message='fake_exc')
        mock_time.time.side_effect = mock_time_side_eff

        (fake_func,
         fake_func_side_effect) = self._get_fake_func_with_retry_decorator(
            exceptions=exceptions.Win32Exception,
            timeout=timeout,
            side_effect=raised_exc)

        self.assertRaises(exceptions.Win32Exception, fake_func)
        fake_func_side_effect.assert_has_calls(
            [mock.call()] * expected_try_count)

    def test_retry_decorator_tries_exceeded(self):
        self._test_retry_decorator_exceeded(
            max_retry_count=2,
            expected_try_count=3)

    def test_retry_decorator_time_exceeded(self):
        self._test_retry_decorator_exceeded(
            mock_time_side_eff=[0, 1, 4],
            timeout=3,
            expected_try_count=1)

    @mock.patch('time.sleep')
    def _test_retry_decorator_no_retry(self, mock_sleep,
                                       expected_exceptions=(),
                                       expected_error_codes=()):
        err_code = 1
        raised_exc = exceptions.Win32Exception(message='fake_exc',
                                               error_code=err_code)
        fake_func, fake_func_side_effect = (
            self._get_fake_func_with_retry_decorator(
                error_codes=expected_error_codes,
                exceptions=expected_exceptions,
                side_effect=raised_exc))

        self.assertRaises(exceptions.Win32Exception,
                          fake_func, mock.sentinel.arg,
                          fake_kwarg=mock.sentinel.kwarg)

        self.assertFalse(mock_sleep.called)
        fake_func_side_effect.assert_called_once_with(
            mock.sentinel.arg, fake_kwarg=mock.sentinel.kwarg)

    def test_retry_decorator_unexpected_err_code(self):
        self._test_retry_decorator_no_retry(
            expected_exceptions=exceptions.Win32Exception,
            expected_error_codes=2)

    def test_retry_decorator_unexpected_exc(self):
        self._test_retry_decorator_no_retry(
            expected_exceptions=(IOError, AttributeError))

    @mock.patch('time.sleep')
    def test_retry_decorator_explicitly_avoid_retry(self, mock_sleep):
        # Tests the case when there is a function aware of the retry
        # decorator and explicitly requests that no retry should be
        # performed.

        def func_side_effect(fake_arg, retry_context):
            self.assertEqual(mock.sentinel.arg, fake_arg)
            self.assertEqual(retry_context, dict(prevent_retry=False))

            retry_context['prevent_retry'] = True
            raise exceptions.Win32Exception(message='fake_exc',
                                            error_code=1)

        fake_func, mock_side_effect = (
            self._get_fake_func_with_retry_decorator(
                exceptions=exceptions.Win32Exception,
                side_effect=func_side_effect,
                pass_retry_context=True))

        self.assertRaises(exceptions.Win32Exception,
                          fake_func, mock.sentinel.arg)

        self.assertEqual(1, mock_side_effect.call_count)
        self.assertFalse(mock_sleep.called)

    @mock.patch.object(_utils.socket, 'getaddrinfo')
    def test_get_ips(self, mock_getaddrinfo):
        ips = ['1.2.3.4', '5.6.7.8']
        mock_getaddrinfo.return_value = [
            (None, None, None, None, (ip, 0)) for ip in ips]

        resulted_ips = _utils.get_ips(mock.sentinel.addr)
        self.assertEqual(ips, resulted_ips)

        mock_getaddrinfo.assert_called_once_with(
            mock.sentinel.addr, None, 0, 0, 0)

    @mock.patch('eventlet.tpool.execute')
    @mock.patch('eventlet.getcurrent')
    @ddt.data(mock.Mock(), None)
    def test_avoid_blocking_call(self, gt_parent, mock_get_current_gt,
                                 mock_execute):
        mock_get_current_gt.return_value.parent = gt_parent
        mock_execute.return_value = mock.sentinel.ret_val

        def fake_blocking_func(*args, **kwargs):
            self.assertEqual((mock.sentinel.arg, ), args)
            self.assertEqual(dict(kwarg=mock.sentinel.kwarg),
                             kwargs)
            return mock.sentinel.ret_val

        fake_blocking_func_decorated = (
            _utils.avoid_blocking_call_decorator(fake_blocking_func))

        ret_val = fake_blocking_func_decorated(mock.sentinel.arg,
                                               kwarg=mock.sentinel.kwarg)

        self.assertEqual(mock.sentinel.ret_val, ret_val)
        if gt_parent:
            mock_execute.assert_called_once_with(fake_blocking_func,
                                                 mock.sentinel.arg,
                                                 kwarg=mock.sentinel.kwarg)
        else:
            self.assertFalse(mock_execute.called)

    @mock.patch.object(_utils, 'time')
    @ddt.data(True, False)
    def test_wmi_retry_decorator(self, expect_hres, mock_time):
        expected_hres = 0x8007beef
        expected_err_code = expected_hres if expect_hres else 0xbeef
        other_hres = 0x80070001
        max_retry_count = 5
        # The second exception will contain an unexpected error code,
        # in which case we expect the function to propagate the error.
        expected_try_count = 2

        side_effect = [test_base.FakeWMIExc(hresult=expected_hres),
                       test_base.FakeWMIExc(hresult=other_hres)]

        decorator = (_utils.wmi_retry_decorator_hresult if expect_hres
                     else _utils.wmi_retry_decorator)
        (fake_func,
         fake_func_side_effect) = self._get_fake_func_with_retry_decorator(
            error_codes=expected_err_code,
            max_retry_count=max_retry_count,
            decorator=decorator,
            side_effect=side_effect)

        self.assertRaises(test_base.FakeWMIExc,
                          fake_func,
                          mock.sentinel.arg,
                          kwarg=mock.sentinel.kwarg)

        fake_func_side_effect.assert_has_calls(
            [mock.call(mock.sentinel.arg, kwarg=mock.sentinel.kwarg)] *
            expected_try_count)

    def test_get_com_error_hresult(self):
        fake_hres = -5
        expected_hres = (1 << 32) + fake_hres
        mock_excepinfo = [None] * 5 + [fake_hres]
        mock_com_err = mock.Mock(excepinfo=mock_excepinfo)

        ret_val = _utils.get_com_error_hresult(mock_com_err)

        self.assertEqual(expected_hres, ret_val)

    def get_com_error_hresult_missing_excepinfo(self):
        ret_val = _utils.get_com_error_hresult(None)
        self.assertIsNone(ret_val)

    def test_hresult_to_err_code(self):
        # This could differ based on the error source.
        # Only the last 2 bytes of the hresult the error code.
        fake_file_exists_hres = -0x7ff8ffb0
        file_exists_err_code = 0x50

        ret_val = _utils.hresult_to_err_code(fake_file_exists_hres)
        self.assertEqual(file_exists_err_code, ret_val)

    @mock.patch.object(_utils, 'get_com_error_hresult')
    @mock.patch.object(_utils, 'hresult_to_err_code')
    def test_get_com_error_code(self, mock_hres_to_err_code, mock_get_hresult):
        ret_val = _utils.get_com_error_code(mock.sentinel.com_err)

        self.assertEqual(mock_hres_to_err_code.return_value, ret_val)
        mock_get_hresult.assert_called_once_with(mock.sentinel.com_err)
        mock_hres_to_err_code.assert_called_once_with(
            mock_get_hresult.return_value)

    @ddt.data(_utils._WBEM_E_NOT_FOUND, mock.sentinel.wbem_error)
    def test_is_not_found_exc(self, hresult):
        exc = test_base.FakeWMIExc(hresult=hresult)

        result = _utils._is_not_found_exc(exc)

        expected = hresult == _utils._WBEM_E_NOT_FOUND
        self.assertEqual(expected, result)

    @mock.patch.object(_utils, 'get_com_error_hresult')
    def test_not_found_decorator(self, mock_get_com_error_hresult):
        mock_get_com_error_hresult.side_effect = lambda x: x
        translated_exc = exceptions.HyperVVMNotFoundException

        @_utils.not_found_decorator(
            translated_exc=translated_exc)
        def f(to_call):
            to_call()

        to_call = mock.Mock()
        to_call.side_effect = exceptions.x_wmi(
            'expected error', com_error=_utils._WBEM_E_NOT_FOUND)
        self.assertRaises(translated_exc, f, to_call)

        to_call.side_effect = exceptions.x_wmi()
        self.assertRaises(exceptions.x_wmi, f, to_call)

    def test_hex_str_to_byte_array(self):
        fake_hex_str = '0x0010A'

        resulted_array = _utils.hex_str_to_byte_array(fake_hex_str)
        expected_array = bytearray([0, 1, 10])

        self.assertEqual(expected_array, resulted_array)

    def test_byte_array_to_hex_str(self):
        fake_byte_array = bytearray(range(3))

        resulted_string = _utils.byte_array_to_hex_str(fake_byte_array)
        expected_string = '000102'

        self.assertEqual(expected_string, resulted_string)

    def test_required_vm_version(self):
        @_utils.required_vm_version()
        def foo(bar, vmsettings):
            pass

        mock_vmsettings = mock.Mock()

        for good_version in [constants.VM_VERSION_5_0,
                             constants.VM_VERSION_254_0]:
            mock_vmsettings.Version = good_version
            foo(mock.sentinel.bar, mock_vmsettings)

        for bad_version in ['4.99', '254.1']:
            mock_vmsettings.Version = bad_version
            self.assertRaises(exceptions.InvalidVMVersion, foo,
                              mock.sentinel.bar, mock_vmsettings)
