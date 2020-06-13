# Copyright 2016 Cloudbase Solutions Srl
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

import collections
import ctypes

import ddt
import mock
import six

from os_win import _utils
from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils.storage.initiator import iscsi_utils
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi.errmsg import iscsierr
from os_win.utils.winapi.libs import iscsidsc as iscsi_struct


@ddt.ddt
class ISCSIInitiatorUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V ISCSIInitiatorUtils class."""

    _autospec_classes = [
        iscsi_utils.win32utils.Win32Utils,
        iscsi_utils.diskutils.DiskUtils,
    ]

    def setUp(self):
        super(ISCSIInitiatorUtilsTestCase, self).setUp()

        self._initiator = iscsi_utils.ISCSIInitiatorUtils()
        self._diskutils = self._initiator._diskutils

        self._iscsidsc = mock.patch.object(
            iscsi_utils, 'iscsidsc', create=True).start()

        self._run_mocker = mock.patch.object(self._initiator,
                                             '_run_and_check_output')
        self._mock_run = self._run_mocker.start()

        iscsi_utils.portal_map = collections.defaultdict(set)

    def _mock_ctypes(self):
        self._ctypes = mock.Mock()
        # This is used in order to easily make assertions on the variables
        # passed by reference.
        self._ctypes.byref = lambda x: (x, "byref")

        mock.patch.object(iscsi_utils, 'ctypes', self._ctypes).start()

    def _get_fake_iscsi_utils_getter_func(self, func_side_effect,
                                          decorator_args,
                                          returned_element_count=None,
                                          required_buff_sz=None):
        @iscsi_utils.ensure_buff_and_retrieve_items(**decorator_args)
        def fake_func(inst, buff=None, buff_size=None,
                      element_count=None, *args, **kwargs):
            raised_exc = None
            try:
                # Those arguments will always be ULONGs, as requested
                # by the iscsidsc functions.
                self.assertIsInstance(buff_size, ctypes.c_ulong)
                self.assertIsInstance(element_count, ctypes.c_ulong)
                func_side_effect(buff=buff, buff_size_val=buff_size.value,
                                 element_count_val=element_count.value,
                                 *args, **kwargs)
            except Exception as ex:
                raised_exc = ex

            if returned_element_count:
                element_count.value = returned_element_count
            if required_buff_sz:
                buff_size.value = required_buff_sz

            if raised_exc:
                raise raised_exc
            return mock.sentinel.ret_val
        return fake_func

    @mock.patch.object(iscsi_utils, '_get_items_from_buff')
    def _test_ensure_buff_decorator(self, mock_get_items,
                                    required_buff_sz=None,
                                    returned_element_count=None,
                                    parse_output=False):
        insufficient_buff_exc = exceptions.Win32Exception(
            message='fake_err_msg',
            error_code=w_const.ERROR_INSUFFICIENT_BUFFER)
        func_requests_buff_sz = required_buff_sz is not None
        struct_type = ctypes.c_uint

        decorator_args = dict(struct_type=struct_type,
                              parse_output=parse_output,
                              func_requests_buff_sz=func_requests_buff_sz)

        func_side_effect = mock.Mock(side_effect=(insufficient_buff_exc, None))
        fake_func = self._get_fake_iscsi_utils_getter_func(
            returned_element_count=returned_element_count,
            required_buff_sz=required_buff_sz,
            func_side_effect=func_side_effect,
            decorator_args=decorator_args)

        ret_val = fake_func(self._initiator, fake_arg=mock.sentinel.arg)
        if parse_output:
            self.assertEqual(mock_get_items.return_value, ret_val)
        else:
            self.assertEqual(mock.sentinel.ret_val, ret_val)

        # We expect our decorated method to be called exactly two times.
        first_call_args_dict = func_side_effect.call_args_list[0][1]
        self.assertIsInstance(first_call_args_dict['buff'],
                              ctypes.POINTER(struct_type))
        self.assertEqual(first_call_args_dict['buff_size_val'], 0)
        self.assertEqual(first_call_args_dict['element_count_val'], 0)

        second_call_args_dict = func_side_effect.call_args_list[1][1]
        self.assertIsInstance(second_call_args_dict['buff'],
                              ctypes.POINTER(struct_type))
        self.assertEqual(second_call_args_dict['buff_size_val'],
                         required_buff_sz or 0)
        self.assertEqual(second_call_args_dict['element_count_val'],
                         returned_element_count or 0)

    def test_ensure_buff_func_requests_buff_sz(self):
        self._test_ensure_buff_decorator(required_buff_sz=10,
                                         parse_output=True)

    def test_ensure_buff_func_requests_el_count(self):
        self._test_ensure_buff_decorator(returned_element_count=5)

    def test_ensure_buff_func_unexpected_exception(self):
        fake_exc = exceptions.Win32Exception(message='fake_message',
                                             error_code=1)

        func_side_effect = mock.Mock(side_effect=fake_exc)
        fake_func = self._get_fake_iscsi_utils_getter_func(
            func_side_effect=func_side_effect,
            decorator_args={'struct_type': ctypes.c_ubyte})

        self.assertRaises(exceptions.Win32Exception, fake_func,
                          self._initiator)

    def test_get_items_from_buff(self):
        fake_buff_contents = 'fake_buff_contents'
        fake_buff = (ctypes.c_wchar * len(fake_buff_contents))()
        fake_buff.value = fake_buff_contents

        fake_buff = ctypes.cast(fake_buff, ctypes.POINTER(ctypes.c_ubyte))

        result = iscsi_utils._get_items_from_buff(fake_buff, ctypes.c_wchar,
                                                  len(fake_buff_contents))

        self.assertEqual(fake_buff_contents, result.value)

    def test_run_and_check_output(self):
        self._run_mocker.stop()
        self._initiator._win32utils = mock.Mock()
        mock_win32utils_run_and_check_output = (
            self._initiator._win32utils.run_and_check_output)

        self._initiator._run_and_check_output(mock.sentinel.func,
                                              mock.sentinel.arg,
                                              fake_kwarg=mock.sentinel.kwarg)

        mock_win32utils_run_and_check_output.assert_called_once_with(
            mock.sentinel.func,
            mock.sentinel.arg,
            fake_kwarg=mock.sentinel.kwarg,
            error_msg_src=iscsierr.err_msg_dict,
            failure_exc=exceptions.ISCSIInitiatorAPIException)

    def test_get_iscsi_persistent_logins(self):
        self._mock_ctypes()

        _get_iscsi_persistent_logins = _utils.get_wrapped_function(
            self._initiator._get_iscsi_persistent_logins)
        _get_iscsi_persistent_logins(
            self._initiator,
            buff=mock.sentinel.buff,
            buff_size=mock.sentinel.buff_size,
            element_count=mock.sentinel.element_count)

        self._mock_run.assert_called_once_with(
            self._iscsidsc.ReportIScsiPersistentLoginsW,
            self._ctypes.byref(mock.sentinel.element_count),
            mock.sentinel.buff,
            self._ctypes.byref(mock.sentinel.buff_size))

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_parse_string_list')
    def test_get_targets(self, mock_parse_string_list):
        self._mock_ctypes()

        get_targets = _utils.get_wrapped_function(
            self._initiator.get_targets)
        mock_el_count = mock.Mock(value=mock.sentinel.element_count)

        resulted_target_list = get_targets(
            self._initiator,
            forced_update=mock.sentinel.forced_update,
            element_count=mock_el_count,
            buff=mock.sentinel.buff)
        self.assertEqual(mock_parse_string_list.return_value,
                         resulted_target_list)

        self._mock_run.assert_called_once_with(
            self._iscsidsc.ReportIScsiTargetsW,
            mock.sentinel.forced_update,
            self._ctypes.byref(mock_el_count),
            mock.sentinel.buff)
        mock_parse_string_list.assert_called_once_with(
            mock.sentinel.buff, mock.sentinel.element_count)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_parse_string_list')
    def test_get_initiators(self, mock_parse_string_list):
        self._mock_ctypes()

        get_initiators = _utils.get_wrapped_function(
            self._initiator.get_iscsi_initiators)
        mock_el_count = mock.Mock(value=mock.sentinel.element_count)

        resulted_initator_list = get_initiators(
            self._initiator,
            element_count=mock_el_count,
            buff=mock.sentinel.buff)
        self.assertEqual(mock_parse_string_list.return_value,
                         resulted_initator_list)

        self._mock_run.assert_called_once_with(
            self._iscsidsc.ReportIScsiInitiatorListW,
            self._ctypes.byref(mock_el_count),
            mock.sentinel.buff)
        mock_parse_string_list.assert_called_once_with(
            mock.sentinel.buff, mock.sentinel.element_count)

    def test_parse_string_list(self):
        self._mock_ctypes()

        fake_buff = 'fake\x00buff\x00\x00'
        self._ctypes.cast.return_value = fake_buff

        str_list = self._initiator._parse_string_list(fake_buff,
                                                      len(fake_buff))

        self.assertEqual(['fake', 'buff'], str_list)

        self._ctypes.cast.assert_called_once_with(
            fake_buff, self._ctypes.POINTER.return_value)
        self._ctypes.POINTER.assert_called_once_with(self._ctypes.c_wchar)

    def test_get_iscsi_initiator(self):
        self._mock_ctypes()

        self._ctypes.c_wchar = mock.MagicMock()
        fake_buff = (self._ctypes.c_wchar * (
            w_const.MAX_ISCSI_NAME_LEN + 1))()
        fake_buff.value = mock.sentinel.buff_value

        resulted_iscsi_initiator = self._initiator.get_iscsi_initiator()

        self._mock_run.assert_called_once_with(
            self._iscsidsc.GetIScsiInitiatorNodeNameW,
            fake_buff)
        self.assertEqual(mock.sentinel.buff_value,
                         resulted_iscsi_initiator)

    @mock.patch('socket.getfqdn')
    def test_get_iscsi_initiator_exception(self, mock_get_fqdn):
        fake_fqdn = 'fakehost.FAKE-DOMAIN.com'
        fake_exc = exceptions.ISCSIInitiatorAPIException(
            message='fake_message',
            error_code=1,
            func_name='fake_func')

        self._mock_run.side_effect = fake_exc
        mock_get_fqdn.return_value = fake_fqdn

        resulted_iqn = self._initiator.get_iscsi_initiator()

        expected_iqn = "%s:%s" % (self._initiator._MS_IQN_PREFIX,
                                  fake_fqdn.lower())
        self.assertEqual(expected_iqn, resulted_iqn)

    @mock.patch.object(ctypes, 'byref')
    @mock.patch.object(iscsi_struct, 'ISCSI_UNIQUE_CONNECTION_ID')
    @mock.patch.object(iscsi_struct, 'ISCSI_UNIQUE_SESSION_ID')
    def test_login_iscsi_target(self, mock_cls_ISCSI_UNIQUE_SESSION_ID,
                                mock_cls_ISCSI_UNIQUE_CONNECTION_ID,
                                mock_byref):
        fake_target_name = 'fake_target_name'

        resulted_session_id, resulted_conection_id = (
            self._initiator._login_iscsi_target(fake_target_name))

        args_list = self._mock_run.call_args_list[0][0]

        self.assertIsInstance(args_list[1], ctypes.c_wchar_p)
        self.assertEqual(fake_target_name, args_list[1].value)
        self.assertIsInstance(args_list[4], ctypes.c_ulong)
        self.assertEqual(
            ctypes.c_ulong(w_const.ISCSI_ANY_INITIATOR_PORT).value,
            args_list[4].value)
        self.assertIsInstance(args_list[6], ctypes.c_ulonglong)
        self.assertEqual(0, args_list[6].value)
        self.assertIsInstance(args_list[9], ctypes.c_ulong)
        self.assertEqual(0, args_list[9].value)

        mock_byref.assert_has_calls([
            mock.call(mock_cls_ISCSI_UNIQUE_SESSION_ID.return_value),
            mock.call(mock_cls_ISCSI_UNIQUE_CONNECTION_ID.return_value)])
        self.assertEqual(
            mock_cls_ISCSI_UNIQUE_SESSION_ID.return_value,
            resulted_session_id)
        self.assertEqual(
            mock_cls_ISCSI_UNIQUE_CONNECTION_ID.return_value,
            resulted_conection_id)

    def test_get_iscsi_sessions(self):
        self._mock_ctypes()

        _get_iscsi_sessions = _utils.get_wrapped_function(
            self._initiator._get_iscsi_sessions)
        _get_iscsi_sessions(
            self._initiator,
            buff=mock.sentinel.buff,
            buff_size=mock.sentinel.buff_size,
            element_count=mock.sentinel.element_count)

        self._mock_run.assert_called_once_with(
            self._iscsidsc.GetIScsiSessionListW,
            self._ctypes.byref(mock.sentinel.buff_size),
            self._ctypes.byref(mock.sentinel.element_count),
            mock.sentinel.buff)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_sessions')
    def test_get_iscsi_target_sessions(self, mock_get_iscsi_sessions,
                                       target_sessions_found=True):
        fake_session = mock.Mock(TargetNodeName="FAKE_TARGET_NAME",
                                 ConnectionCount=1)
        fake_disconn_session = mock.Mock(
            TargetNodeName="fake_target_name",
            ConnectionCount=0)
        other_session = mock.Mock(TargetNodeName="other_target_name",
                                  ConnectionCount=1)

        sessions = [fake_session, fake_disconn_session, other_session]
        mock_get_iscsi_sessions.return_value = sessions

        resulted_tgt_sessions = self._initiator._get_iscsi_target_sessions(
            "fake_target_name")

        self.assertEqual([fake_session], resulted_tgt_sessions)

    def test_get_iscsi_session_devices(self):
        self._mock_ctypes()

        _get_iscsi_session_devices = _utils.get_wrapped_function(
            self._initiator._get_iscsi_session_devices)
        _get_iscsi_session_devices(
            self._initiator,
            mock.sentinel.session_id,
            buff=mock.sentinel.buff,
            element_count=mock.sentinel.element_count)

        self._mock_run.assert_called_once_with(
            self._iscsidsc.GetDevicesForIScsiSessionW,
            self._ctypes.byref(mock.sentinel.session_id),
            self._ctypes.byref(mock.sentinel.element_count),
            mock.sentinel.buff)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_session_devices')
    def test_get_iscsi_session_luns(self, mock_get_iscsi_session_devices):
        fake_device = mock.Mock()
        fake_device.StorageDeviceNumber.DeviceType = w_const.FILE_DEVICE_DISK
        mock_get_iscsi_session_devices.return_value = [fake_device,
                                                       mock.Mock()]

        resulted_luns = self._initiator._get_iscsi_session_disk_luns(
            mock.sentinel.session_id)
        expected_luns = [fake_device.ScsiAddress.Lun]

        mock_get_iscsi_session_devices.assert_called_once_with(
            mock.sentinel.session_id)
        self.assertEqual(expected_luns, resulted_luns)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_session_devices')
    def test_get_iscsi_device_from_session(self,
                                           mock_get_iscsi_session_devices):
        fake_device = mock.Mock()
        fake_device.ScsiAddress.Lun = mock.sentinel.target_lun
        mock_get_iscsi_session_devices.return_value = [mock.Mock(),
                                                       fake_device]

        resulted_device = self._initiator._get_iscsi_device_from_session(
            mock.sentinel.session_id,
            mock.sentinel.target_lun)

        mock_get_iscsi_session_devices.assert_called_once_with(
            mock.sentinel.session_id)
        self.assertEqual(fake_device, resulted_device)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       'get_device_number_and_path')
    def test_get_device_number_for_target(self, mock_get_dev_num_and_path):
        dev_num = self._initiator.get_device_number_for_target(
            mock.sentinel.target_name, mock.sentinel.lun,
            mock.sentinel.fail_if_not_found)

        mock_get_dev_num_and_path.assert_called_once_with(
            mock.sentinel.target_name, mock.sentinel.lun,
            mock.sentinel.fail_if_not_found)
        self.assertEqual(mock_get_dev_num_and_path.return_value[0], dev_num)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       'ensure_lun_available')
    def test_get_device_number_and_path(self, mock_ensure_lun_available):
        mock_ensure_lun_available.return_value = (mock.sentinel.dev_num,
                                                  mock.sentinel.dev_path)

        dev_num, dev_path = self._initiator.get_device_number_and_path(
            mock.sentinel.target_name, mock.sentinel.lun,
            retry_attempts=mock.sentinel.retry_attempts,
            retry_interval=mock.sentinel.retry_interval,
            rescan_disks=mock.sentinel.rescan_disks,
            ensure_mpio_claimed=mock.sentinel.ensure_mpio_claimed)

        mock_ensure_lun_available.assert_called_once_with(
            mock.sentinel.target_name, mock.sentinel.lun,
            rescan_attempts=mock.sentinel.retry_attempts,
            retry_interval=mock.sentinel.retry_interval,
            rescan_disks=mock.sentinel.rescan_disks,
            ensure_mpio_claimed=mock.sentinel.ensure_mpio_claimed)

        self.assertEqual(mock.sentinel.dev_num, dev_num)
        self.assertEqual(mock.sentinel.dev_path, dev_path)

    @ddt.data(True, False)
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       'ensure_lun_available')
    def test_get_device_number_and_path_exc(self, fail_if_not_found,
                                            mock_ensure_lun_available):
        raised_exc = exceptions.ISCSILunNotAvailable
        mock_ensure_lun_available.side_effect = raised_exc(
            target_iqn=mock.sentinel.target_iqn,
            target_lun=mock.sentinel.target_lun)

        if fail_if_not_found:
            self.assertRaises(raised_exc,
                              self._initiator.get_device_number_and_path,
                              mock.sentinel.target_name,
                              mock.sentinel.lun,
                              fail_if_not_found)
        else:
            dev_num, dev_path = self._initiator.get_device_number_and_path(
                mock.sentinel.target_name,
                mock.sentinel.lun,
                fail_if_not_found)
            self.assertIsNone(dev_num)
            self.assertIsNone(dev_path)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_target_sessions')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_session_disk_luns')
    def test_get_target_luns(self, mock_get_iscsi_session_disk_luns,
                             mock_get_iscsi_target_sessions):
        fake_session = mock.Mock()
        mock_get_iscsi_target_sessions.return_value = [fake_session]

        retrieved_luns = [mock.sentinel.lun_0]
        mock_get_iscsi_session_disk_luns.return_value = retrieved_luns

        resulted_luns = self._initiator.get_target_luns(
            mock.sentinel.target_name)

        mock_get_iscsi_target_sessions.assert_called_once_with(
            mock.sentinel.target_name)
        mock_get_iscsi_session_disk_luns.assert_called_once_with(
            fake_session.SessionId)
        self.assertEqual(retrieved_luns, resulted_luns)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       'get_target_luns')
    def test_get_target_lun_count(self, mock_get_target_luns):
        target_luns = [mock.sentinel.lun0, mock.sentinel.lun1]
        mock_get_target_luns.return_value = target_luns

        lun_count = self._initiator.get_target_lun_count(
            mock.sentinel.target_name)

        self.assertEqual(len(target_luns), lun_count)
        mock_get_target_luns.assert_called_once_with(
            mock.sentinel.target_name)

    def test_logout_iscsi_target(self):
        self._mock_ctypes()

        self._initiator._logout_iscsi_target(mock.sentinel.session_id)

        self._mock_run.assert_called_once_with(
            self._iscsidsc.LogoutIScsiTarget,
            self._ctypes.byref(mock.sentinel.session_id))

    def test_add_static_target(self):
        self._mock_ctypes()

        is_persistent = True
        self._initiator._add_static_target(mock.sentinel.target_name,
                                           is_persistent=is_persistent)

        self._mock_run.assert_called_once_with(
            self._iscsidsc.AddIScsiStaticTargetW,
            self._ctypes.c_wchar_p(mock.sentinel.target_name),
            None, 0, is_persistent, None, None, None)

    def test_remove_static_target(self):
        self._mock_ctypes()

        self._initiator._remove_static_target(mock.sentinel.target_name)

        expected_ignored_err_codes = [w_const.ISDSC_TARGET_NOT_FOUND]
        self._mock_run.assert_called_once_with(
            self._iscsidsc.RemoveIScsiStaticTargetW,
            self._ctypes.c_wchar_p(mock.sentinel.target_name),
            ignored_error_codes=expected_ignored_err_codes)

    def test_get_login_opts(self):
        fake_username = 'fake_chap_username'
        fake_password = 'fake_chap_secret'
        auth_type = constants.ISCSI_CHAP_AUTH_TYPE
        login_flags = w_const.ISCSI_LOGIN_FLAG_MULTIPATH_ENABLED

        login_opts = self._initiator._get_login_opts(
            auth_username=fake_username,
            auth_password=fake_password,
            auth_type=auth_type,
            login_flags=login_flags)

        self.assertEqual(len(fake_username), login_opts.UsernameLength)
        self.assertEqual(len(fake_password), login_opts.PasswordLength)

        username_struct_contents = ctypes.cast(
            login_opts.Username,
            ctypes.POINTER(ctypes.c_char * len(fake_username))).contents.value
        pwd_struct_contents = ctypes.cast(
            login_opts.Password,
            ctypes.POINTER(ctypes.c_char * len(fake_password))).contents.value

        self.assertEqual(six.b(fake_username), username_struct_contents)
        self.assertEqual(six.b(fake_password), pwd_struct_contents)

        expected_info_bitmap = (w_const.ISCSI_LOGIN_OPTIONS_USERNAME |
                                w_const.ISCSI_LOGIN_OPTIONS_PASSWORD |
                                w_const.ISCSI_LOGIN_OPTIONS_AUTH_TYPE)
        self.assertEqual(expected_info_bitmap,
                         login_opts.InformationSpecified)
        self.assertEqual(login_flags,
                         login_opts.LoginFlags)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_session_devices')
    def test_session_on_path_exists(self, mock_get_iscsi_session_devices):
        mock_device = mock.Mock(InitiatorName=mock.sentinel.initiator_name)
        mock_get_iscsi_session_devices.return_value = [mock_device]

        fake_connection = mock.Mock(TargetAddress=mock.sentinel.portal_addr,
                                    TargetSocket=mock.sentinel.portal_port)
        fake_connections = [mock.Mock(), fake_connection]
        fake_session = mock.Mock(ConnectionCount=len(fake_connections),
                                 Connections=fake_connections)
        fake_sessions = [mock.Mock(Connections=[], ConnectionCount=0),
                         fake_session]

        session_on_path_exists = self._initiator._session_on_path_exists(
            fake_sessions, mock.sentinel.portal_addr,
            mock.sentinel.portal_port,
            mock.sentinel.initiator_name)
        self.assertTrue(session_on_path_exists)
        mock_get_iscsi_session_devices.assert_has_calls(
            [mock.call(session.SessionId) for session in fake_sessions])

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_target_sessions')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_session_on_path_exists')
    def _test_new_session_required(self, mock_session_on_path_exists,
                                   mock_get_iscsi_target_sessions,
                                   sessions=None,
                                   mpio_enabled=False,
                                   session_on_path_exists=False):
        mock_get_iscsi_target_sessions.return_value = sessions
        mock_session_on_path_exists.return_value = session_on_path_exists

        expected_result = (not sessions or
                           (mpio_enabled and not session_on_path_exists))
        result = self._initiator._new_session_required(
            mock.sentinel.target_iqn,
            mock.sentinel.portal_addr,
            mock.sentinel.portal_port,
            mock.sentinel.initiator_name,
            mpio_enabled)
        self.assertEqual(expected_result, result)

        if sessions and mpio_enabled:
            mock_session_on_path_exists.assert_called_once_with(
                sessions,
                mock.sentinel.portal_addr,
                mock.sentinel.portal_port,
                mock.sentinel.initiator_name)

    def test_new_session_required_no_sessions(self):
        self._test_new_session_required()

    def test_new_session_required_existing_sessions_no_mpio(self):
        self._test_new_session_required(sessions=mock.sentinel.sessions)

    def test_new_session_required_existing_sessions_mpio_enabled(self):
        self._test_new_session_required(sessions=mock.sentinel.sessions,
                                        mpio_enabled=True)

    def test_new_session_required_session_on_path_exists(self):
        self._test_new_session_required(sessions=mock.sentinel.sessions,
                                        mpio_enabled=True,
                                        session_on_path_exists=True)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_login_opts')
    @mock.patch.object(iscsi_struct, 'ISCSI_TARGET_PORTAL')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_new_session_required')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils, 'get_targets')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils, '_login_iscsi_target')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       'ensure_lun_available')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_add_static_target')
    def _test_login_storage_target(self, mock_add_static_target,
                                   mock_ensure_lun_available,
                                   mock_login_iscsi_target,
                                   mock_get_targets,
                                   mock_session_required,
                                   mock_cls_ISCSI_TARGET_PORTAL,
                                   mock_get_login_opts,
                                   mpio_enabled=False,
                                   login_required=True):
        fake_portal_addr = '127.0.0.1'
        fake_portal_port = 3260
        fake_target_portal = '%s:%s' % (fake_portal_addr, fake_portal_port)

        fake_portal = mock_cls_ISCSI_TARGET_PORTAL.return_value
        fake_login_opts = mock_get_login_opts.return_value

        mock_get_targets.return_value = []
        mock_login_iscsi_target.return_value = (mock.sentinel.session_id,
                                                mock.sentinel.conn_id)
        mock_session_required.return_value = login_required

        self._initiator.login_storage_target(
            mock.sentinel.target_lun,
            mock.sentinel.target_iqn,
            fake_target_portal,
            auth_username=mock.sentinel.auth_username,
            auth_password=mock.sentinel.auth_password,
            auth_type=mock.sentinel.auth_type,
            mpio_enabled=mpio_enabled,
            rescan_attempts=mock.sentinel.rescan_attempts)

        mock_get_targets.assert_called_once_with()
        mock_add_static_target.assert_called_once_with(
            mock.sentinel.target_iqn)

        if login_required:
            expected_login_flags = (
                w_const.ISCSI_LOGIN_FLAG_MULTIPATH_ENABLED
                if mpio_enabled else 0)
            mock_get_login_opts.assert_called_once_with(
                mock.sentinel.auth_username,
                mock.sentinel.auth_password,
                mock.sentinel.auth_type,
                expected_login_flags)
            mock_cls_ISCSI_TARGET_PORTAL.assert_called_once_with(
                Address=fake_portal_addr,
                Socket=fake_portal_port)
            mock_login_iscsi_target.assert_has_calls([
                mock.call(mock.sentinel.target_iqn,
                          fake_portal,
                          fake_login_opts,
                          is_persistent=True),
                mock.call(mock.sentinel.target_iqn,
                          fake_portal,
                          fake_login_opts,
                          is_persistent=False)])
        else:
            self.assertFalse(mock_login_iscsi_target.called)

        mock_ensure_lun_available.assert_called_once_with(
            mock.sentinel.target_iqn,
            mock.sentinel.target_lun,
            mock.sentinel.rescan_attempts)

    def test_login_storage_target_path_exists(self):
        self._test_login_storage_target(login_required=False)

    def test_login_new_storage_target_no_mpio(self):
        self._test_login_storage_target()

    def test_login_storage_target_new_path_using_mpio(self):
        self._test_login_storage_target(mpio_enabled=True)

    @ddt.data(dict(rescan_disks=True),
              dict(retry_interval=mock.sentinel.retry_interval))
    @ddt.unpack
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_device_from_session')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_target_sessions')
    @mock.patch('time.sleep')
    def test_ensure_lun_available(self, mock_sleep,
                                  mock_get_iscsi_target_sessions,
                                  mock_get_iscsi_device_from_session,
                                  rescan_disks=False, retry_interval=0):
        retry_count = 6
        mock_get_iscsi_target_sessions.return_value = [
            mock.Mock(SessionId=mock.sentinel.session_id)]

        fake_exc = exceptions.ISCSIInitiatorAPIException(
            message='fake_message',
            error_code=1,
            func_name='fake_func')
        dev_num_side_eff = [None, -1] + [mock.sentinel.dev_num] * 3
        dev_path_side_eff = ([mock.sentinel.dev_path] * 2 +
                             [None] + [mock.sentinel.dev_path] * 2)
        fake_device = mock.Mock()
        type(fake_device.StorageDeviceNumber).DeviceNumber = (
            mock.PropertyMock(side_effect=dev_num_side_eff))
        type(fake_device).LegacyName = (
            mock.PropertyMock(side_effect=dev_path_side_eff))

        mock_get_dev_side_eff = [None, fake_exc] + [fake_device] * 5
        mock_get_iscsi_device_from_session.side_effect = mock_get_dev_side_eff
        self._diskutils.is_mpio_disk.side_effect = [False, True]

        dev_num, dev_path = self._initiator.ensure_lun_available(
            mock.sentinel.target_iqn,
            mock.sentinel.target_lun,
            rescan_attempts=retry_count,
            retry_interval=retry_interval,
            rescan_disks=rescan_disks,
            ensure_mpio_claimed=True)

        self.assertEqual(mock.sentinel.dev_num, dev_num)
        self.assertEqual(mock.sentinel.dev_path, dev_path)

        mock_get_iscsi_target_sessions.assert_has_calls(
            [mock.call(mock.sentinel.target_iqn)] * (retry_count + 1))
        mock_get_iscsi_device_from_session.assert_has_calls(
            [mock.call(mock.sentinel.session_id,
                       mock.sentinel.target_lun)] * retry_count)
        self._diskutils.is_mpio_disk.assert_has_calls(
            [mock.call(mock.sentinel.dev_num)] * 2)

        expected_rescan_count = retry_count if rescan_disks else 0
        self.assertEqual(
            expected_rescan_count,
            self._diskutils.rescan_disks.call_count)

        if retry_interval:
            mock_sleep.assert_has_calls(
                [mock.call(retry_interval)] * retry_count)
        else:
            self.assertFalse(mock_sleep.called)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_target_sessions')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_logout_iscsi_target')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_remove_target_persistent_logins')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_remove_static_target')
    def test_logout_storage_target(self, mock_remove_static_target,
                                   mock_remove_target_persistent_logins,
                                   mock_logout_iscsi_target,
                                   mock_get_iscsi_target_sessions):
        fake_session = mock.Mock(SessionId=mock.sentinel.session_id)
        mock_get_iscsi_target_sessions.return_value = [fake_session]

        self._initiator.logout_storage_target(mock.sentinel.target_iqn)

        mock_get_iscsi_target_sessions.assert_called_once_with(
            mock.sentinel.target_iqn, connected_only=False)
        mock_logout_iscsi_target.assert_called_once_with(
            mock.sentinel.session_id)
        mock_remove_target_persistent_logins.assert_called_once_with(
            mock.sentinel.target_iqn)
        mock_remove_static_target.assert_called_once_with(
            mock.sentinel.target_iqn)

    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_remove_persistent_login')
    @mock.patch.object(iscsi_utils.ISCSIInitiatorUtils,
                       '_get_iscsi_persistent_logins')
    def test_remove_target_persistent_logins(self,
                                             mock_get_iscsi_persistent_logins,
                                             mock_remove_persistent_login):
        fake_persistent_login = mock.Mock(TargetName=mock.sentinel.target_iqn)
        mock_get_iscsi_persistent_logins.return_value = [fake_persistent_login]

        self._initiator._remove_target_persistent_logins(
            mock.sentinel.target_iqn)

        mock_remove_persistent_login.assert_called_once_with(
            fake_persistent_login)
        mock_get_iscsi_persistent_logins.assert_called_once_with()

    @mock.patch.object(ctypes, 'byref')
    def test_remove_persistent_login(self, mock_byref):
        fake_persistent_login = mock.Mock()
        fake_persistent_login.InitiatorInstance = 'fake_initiator_instance'
        fake_persistent_login.TargetName = 'fake_target_name'

        self._initiator._remove_persistent_login(fake_persistent_login)

        args_list = self._mock_run.call_args_list[0][0]
        self.assertIsInstance(args_list[1], ctypes.c_wchar_p)
        self.assertEqual(fake_persistent_login.InitiatorInstance,
                         args_list[1].value)
        self.assertIsInstance(args_list[3], ctypes.c_wchar_p)
        self.assertEqual(fake_persistent_login.TargetName,
                         args_list[3].value)
        mock_byref.assert_called_once_with(fake_persistent_login.TargetPortal)
