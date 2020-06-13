#  Copyright 2014 IBM Corp.
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
import os
import shutil

import ddt
import mock

from os_win import constants
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils import pathutils
from os_win.utils.winapi import constants as w_const
from os_win.utils.winapi.libs import advapi32 as advapi32_def
from os_win.utils.winapi.libs import kernel32 as kernel32_def
from os_win.utils.winapi import wintypes


@ddt.ddt
class PathUtilsTestCase(test_base.OsWinBaseTestCase):
    """Unit tests for the Hyper-V PathUtils class."""

    _autospec_classes = [
        pathutils.ioutils.IOUtils,
        pathutils.win32utils.Win32Utils,
        pathutils._acl_utils.ACLUtils,
    ]

    def setUp(self):
        super(PathUtilsTestCase, self).setUp()
        self._setup_lib_mocks()

        self._pathutils = pathutils.PathUtils()
        self._mock_run = self._pathutils._win32_utils.run_and_check_output
        self._acl_utils = self._pathutils._acl_utils
        self._io_utils = self._pathutils._io_utils

    def _setup_lib_mocks(self):
        self._ctypes = mock.Mock()
        self._wintypes = mock.Mock()

        self._wintypes.BOOL = lambda x: (x, 'BOOL')
        self._ctypes.c_wchar_p = lambda x: (x, "c_wchar_p")
        self._ctypes.pointer = lambda x: (x, 'pointer')

        self._ctypes_patcher = mock.patch.object(
            pathutils, 'ctypes', new=self._ctypes)
        self._ctypes_patcher.start()

        mock.patch.multiple(pathutils,
                            wintypes=self._wintypes,
                            kernel32=mock.DEFAULT,
                            create=True).start()

    @mock.patch.object(pathutils.PathUtils, 'copy')
    @mock.patch.object(os.path, 'isfile')
    @mock.patch.object(os, 'listdir')
    @mock.patch.object(pathutils.PathUtils, 'check_create_dir')
    def test_copy_folder_files(self, mock_check_create_dir, mock_listdir,
                               mock_isfile, mock_copy):
        src_dir = 'src'
        dest_dir = 'dest'
        fname = 'tmp_file.txt'
        subdir = 'tmp_folder'
        src_fname = os.path.join(src_dir, fname)
        dest_fname = os.path.join(dest_dir, fname)

        # making sure src_subdir is not copied.
        mock_listdir.return_value = [fname, subdir]
        mock_isfile.side_effect = [True, False]

        self._pathutils.copy_folder_files(src_dir, dest_dir)

        mock_check_create_dir.assert_called_once_with(dest_dir)
        mock_copy.assert_called_once_with(src_fname, dest_fname)

    @mock.patch.object(pathutils.PathUtils, 'rename')
    @mock.patch.object(os.path, 'isfile')
    @mock.patch.object(os, 'listdir')
    def test_move_folder_files(self, mock_listdir, mock_isfile, mock_rename):
        src_dir = 'src'
        dest_dir = 'dest'
        fname = 'tmp_file.txt'
        subdir = 'tmp_folder'
        src_fname = os.path.join(src_dir, fname)
        dest_fname = os.path.join(dest_dir, fname)

        # making sure src_subdir is not moved.
        mock_listdir.return_value = [fname, subdir]
        mock_isfile.side_effect = [True, False]

        self._pathutils.move_folder_files(src_dir, dest_dir)
        mock_rename.assert_called_once_with(src_fname, dest_fname)

    @mock.patch('time.sleep')
    @mock.patch.object(pathutils.shutil, 'rmtree')
    def test_rmtree(self, mock_rmtree, mock_sleep):
        exc = exceptions.WindowsError()
        exc.winerror = w_const.ERROR_DIR_IS_NOT_EMPTY
        mock_rmtree.side_effect = [exc] * 5 + [None]

        self._pathutils.rmtree(mock.sentinel.FAKE_PATH)

        mock_rmtree.assert_has_calls([mock.call(mock.sentinel.FAKE_PATH)] * 6)

    @mock.patch('time.sleep')
    @mock.patch.object(pathutils.shutil, 'rmtree')
    def _check_rmtree(self, mock_rmtree, mock_sleep, side_effect):
        mock_rmtree.side_effect = side_effect
        self.assertRaises(exceptions.WindowsError, self._pathutils.rmtree,
                          mock.sentinel.FAKE_PATH)

    def test_rmtree_unexpected(self):
        self._check_rmtree(side_effect=exceptions.WindowsError)

    @mock.patch('time.time')
    def test_rmtree_exceeded(self, mock_time):
        mock_time.side_effect = range(1, 100, 10)
        exc = exceptions.WindowsError()
        exc.winerror = w_const.ERROR_DIR_IS_NOT_EMPTY
        self._check_rmtree(side_effect=exc)

    @mock.patch.object(pathutils.PathUtils, 'makedirs')
    @mock.patch.object(pathutils.PathUtils, 'exists')
    def test_check_create_dir(self, mock_exists, mock_makedirs):
        fake_dir = 'dir'
        mock_exists.return_value = False
        self._pathutils.check_create_dir(fake_dir)

        mock_exists.assert_called_once_with(fake_dir)
        mock_makedirs.assert_called_once_with(fake_dir)

    @mock.patch.object(pathutils.PathUtils, 'rmtree')
    @mock.patch.object(pathutils.PathUtils, 'exists')
    def test_check_remove_dir(self, mock_exists, mock_rmtree):
        fake_dir = 'dir'
        self._pathutils.check_remove_dir(fake_dir)

        mock_exists.assert_called_once_with(fake_dir)
        mock_rmtree.assert_called_once_with(fake_dir)

    @mock.patch('os.path.isdir')
    @mock.patch('os.path.islink')
    def _test_check_symlink(self, mock_is_symlink, mock_is_dir,
                            is_symlink=True, python_version=(2, 7),
                            is_dir=True):
        fake_path = r'c:\\fake_path'
        if is_symlink:
            f_attr = 0x400
        else:
            f_attr = 0x80

        mock_is_dir.return_value = is_dir
        mock_is_symlink.return_value = is_symlink
        self._mock_run.return_value = f_attr

        with mock.patch('sys.version_info', python_version):
            ret_value = self._pathutils.is_symlink(fake_path)

        if python_version >= (3, 2):
            mock_is_symlink.assert_called_once_with(fake_path)
        else:
            self._mock_run.assert_called_once_with(
                pathutils.kernel32.GetFileAttributesW,
                fake_path,
                error_ret_vals=[w_const.INVALID_FILE_ATTRIBUTES],
                kernel32_lib_func=True)

        self.assertEqual(is_symlink, ret_value)

    def test_is_symlink(self):
        self._test_check_symlink()

    def test_is_not_symlink(self):
        self._test_check_symlink(is_symlink=False)

    def test_is_symlink_python_gt_3_2(self):
        self._test_check_symlink(python_version=(3, 3))

    def test_create_sym_link(self):
        tg_is_dir = False
        self._pathutils.create_sym_link(mock.sentinel.path,
                                        mock.sentinel.target,
                                        target_is_dir=tg_is_dir)

        self._mock_run.assert_called_once_with(
            pathutils.kernel32.CreateSymbolicLinkW,
            mock.sentinel.path,
            mock.sentinel.target,
            tg_is_dir,
            kernel32_lib_func=True)

    @mock.patch('os.path.isdir')
    def _test_copy(self, mock_isdir, dest_isdir=False):
        mock_isdir.return_value = dest_isdir
        fail_if_exists = False

        fake_src = r'fake_src_fname'
        fake_dest = r'fake_dest'

        expected_dest = (os.path.join(fake_dest, fake_src)
                         if dest_isdir else fake_dest)

        self._pathutils.copy(fake_src, fake_dest,
                             fail_if_exists=fail_if_exists)

        self._mock_run.assert_called_once_with(
            pathutils.kernel32.CopyFileW,
            self._ctypes.c_wchar_p(fake_src),
            self._ctypes.c_wchar_p(expected_dest),
            self._wintypes.BOOL(fail_if_exists),
            kernel32_lib_func=True)

    def test_copy_dest_is_fpath(self):
        self._test_copy()

    def test_copy_dest_is_dir(self):
        self._test_copy(dest_isdir=True)

    @mock.patch('os.path.isdir')
    def test_copy_exc(self, mock_isdir):
        mock_isdir.return_value = False
        self._mock_run.side_effect = exceptions.Win32Exception(
            func_name='mock_copy',
            error_code='fake_error_code',
            error_message='fake_error_msg')
        self.assertRaises(IOError,
                          self._pathutils.copy,
                          mock.sentinel.src,
                          mock.sentinel.dest)

    @mock.patch('os.close')
    @mock.patch('tempfile.mkstemp')
    def test_create_temporary_file(self, mock_mkstemp, mock_close):
        fd = mock.sentinel.file_descriptor
        path = mock.sentinel.absolute_pathname
        mock_mkstemp.return_value = (fd, path)

        output = self._pathutils.create_temporary_file(
            suffix=mock.sentinel.suffix)

        self.assertEqual(path, output)
        mock_close.assert_called_once_with(fd)
        mock_mkstemp.assert_called_once_with(suffix=mock.sentinel.suffix)

    @mock.patch('oslo_utils.fileutils.delete_if_exists')
    def test_temporary_file(self, mock_delete):
        self._pathutils.create_temporary_file = mock.MagicMock()
        self._pathutils.create_temporary_file.return_value = (
            mock.sentinel.temporary_file)
        with self._pathutils.temporary_file() as tmp_file:
            self.assertEqual(mock.sentinel.temporary_file, tmp_file)
            self.assertFalse(mock_delete.called)
        mock_delete.assert_called_once_with(mock.sentinel.temporary_file)

    @mock.patch.object(shutil, 'copytree')
    @mock.patch('os.path.abspath')
    def test_copy_dir(self, mock_abspath, mock_copytree):
        mock_abspath.side_effect = [mock.sentinel.src, mock.sentinel.dest]
        self._pathutils.copy_dir(mock.sentinel.src, mock.sentinel.dest)

        mock_abspath.has_calls(
            [mock.call(mock.sentinel.src), mock.call(mock.sentinel.dest)])
        mock_copytree.assert_called_once_with(mock.sentinel.src,
                                              mock.sentinel.dest)

    def test_add_acl_rule(self):
        # We raise an expected exception in order to
        # easily verify the resource cleanup.
        raised_exc = exceptions.OSWinException
        self._ctypes_patcher.stop()

        fake_trustee = 'FAKEDOMAIN\\FakeUser'
        mock_sec_info = dict(pp_sec_desc=mock.Mock(),
                             pp_dacl=mock.Mock())
        self._acl_utils.get_named_security_info.return_value = mock_sec_info
        self._acl_utils.set_named_security_info.side_effect = raised_exc
        pp_new_dacl = self._acl_utils.set_entries_in_acl.return_value

        self.assertRaises(raised_exc,
                          self._pathutils.add_acl_rule,
                          path=mock.sentinel.path,
                          trustee_name=fake_trustee,
                          access_rights=constants.ACE_GENERIC_READ,
                          access_mode=constants.ACE_GRANT_ACCESS,
                          inheritance_flags=constants.ACE_OBJECT_INHERIT)

        self._acl_utils.get_named_security_info.assert_called_once_with(
            obj_name=mock.sentinel.path,
            obj_type=w_const.SE_FILE_OBJECT,
            security_info_flags=w_const.DACL_SECURITY_INFORMATION)
        self._acl_utils.set_entries_in_acl.assert_called_once_with(
            entry_count=1,
            p_explicit_entry_list=mock.ANY,
            p_old_acl=mock_sec_info['pp_dacl'].contents)
        self._acl_utils.set_named_security_info.assert_called_once_with(
            obj_name=mock.sentinel.path,
            obj_type=w_const.SE_FILE_OBJECT,
            security_info_flags=w_const.DACL_SECURITY_INFORMATION,
            p_dacl=pp_new_dacl.contents)

        p_access = self._acl_utils.set_entries_in_acl.call_args_list[0][1][
            'p_explicit_entry_list']
        access = ctypes.cast(
            p_access,
            ctypes.POINTER(advapi32_def.EXPLICIT_ACCESS)).contents

        self.assertEqual(constants.ACE_GENERIC_READ,
                         access.grfAccessPermissions)
        self.assertEqual(constants.ACE_GRANT_ACCESS,
                         access.grfAccessMode)
        self.assertEqual(constants.ACE_OBJECT_INHERIT,
                         access.grfInheritance)
        self.assertEqual(w_const.TRUSTEE_IS_NAME,
                         access.Trustee.TrusteeForm)
        self.assertEqual(fake_trustee,
                         access.Trustee.pstrName)

        self._pathutils._win32_utils.local_free.assert_has_calls(
            [mock.call(pointer)
             for pointer in [mock_sec_info['pp_sec_desc'].contents,
                             pp_new_dacl.contents]])

    def test_copy_acls(self):
        raised_exc = exceptions.OSWinException

        mock_sec_info = dict(pp_sec_desc=mock.Mock(),
                             pp_dacl=mock.Mock())
        self._acl_utils.get_named_security_info.return_value = mock_sec_info
        self._acl_utils.set_named_security_info.side_effect = raised_exc

        self.assertRaises(raised_exc,
                          self._pathutils.copy_acls,
                          mock.sentinel.src,
                          mock.sentinel.dest)

        self._acl_utils.get_named_security_info.assert_called_once_with(
            obj_name=mock.sentinel.src,
            obj_type=w_const.SE_FILE_OBJECT,
            security_info_flags=w_const.DACL_SECURITY_INFORMATION)
        self._acl_utils.set_named_security_info.assert_called_once_with(
            obj_name=mock.sentinel.dest,
            obj_type=w_const.SE_FILE_OBJECT,
            security_info_flags=w_const.DACL_SECURITY_INFORMATION,
            p_dacl=mock_sec_info['pp_dacl'].contents)

        self._pathutils._win32_utils.local_free.assert_called_once_with(
            mock_sec_info['pp_sec_desc'].contents)

    def _get_file_id_info(self, volume_id, file_id, as_dict=False):
        identifier = (wintypes.BYTE * 16)()
        assert file_id < 1 << 128

        idx = 0
        while file_id:
            identifier[idx] = file_id & 0xffff
            file_id >>= 8
            idx += 1

        file_id_info = kernel32_def.FILE_ID_INFO(
            VolumeSerialNumber=volume_id,
            FileId=kernel32_def.FILE_ID_128(Identifier=identifier))

        if as_dict:
            return dict(volume_serial_number=file_id_info.VolumeSerialNumber,
                        file_id=bytearray(file_id_info.FileId.Identifier))
        return file_id_info

    @ddt.data((1, 2, 1, 2),  # same file
              (1, 2, 1, 3),  # same volume id, different file id
              (1, 2, 2, 2))  # same file id, different volume id
    @ddt.unpack
    @mock.patch.object(pathutils.PathUtils, 'get_file_id')
    def test_is_same_file(self, volume_id_a, file_id_a,
                          volume_id_b, file_id_b, mock_get_file_id):
        file_info_a = self._get_file_id_info(volume_id_a, file_id_a,
                                             as_dict=True)
        file_info_b = self._get_file_id_info(volume_id_b, file_id_b,
                                             as_dict=True)

        mock_get_file_id.side_effect = [file_info_a, file_info_b]

        same_file = self._pathutils.is_same_file(
            mock.sentinel.path_a,
            mock.sentinel.path_b)

        self.assertEqual(volume_id_a == volume_id_b and file_id_a == file_id_b,
                         same_file)

        mock_get_file_id.assert_has_calls(
            [mock.call(mock.sentinel.path_a),
             mock.call(mock.sentinel.path_b)])

    def test_get_file_id(self):
        self._ctypes_patcher.stop()

        fake_file_id = 1 << 64
        fake_volume_id = 1 << 31

        def fake_get_file_id(func, handle, file_info_class, file_info,
                             buffer_size, kernel32_lib_func):
            self.assertEqual(func,
                             pathutils.kernel32.GetFileInformationByHandleEx)
            self.assertTrue(kernel32_lib_func)
            self.assertEqual(self._io_utils.open.return_value, handle)
            self.assertEqual(w_const.FileIdInfo, file_info_class)
            self.assertLessEqual(ctypes.sizeof(kernel32_def.FILE_ID_INFO),
                                 buffer_size)

            file_id = self._get_file_id_info(fake_volume_id, fake_file_id)
            ctypes.memmove(file_info, ctypes.byref(file_id),
                           ctypes.sizeof(kernel32_def.FILE_ID_INFO))

        self._mock_run.side_effect = fake_get_file_id

        file_id = self._pathutils.get_file_id(mock.sentinel.path)
        exp_identifier = [0] * 16
        exp_identifier[8] = 1
        exp_file_id = dict(volume_serial_number=fake_volume_id,
                           file_id=bytearray(exp_identifier))
        self.assertEqual(exp_file_id, file_id)

        self._io_utils.open.assert_called_once_with(
            mock.sentinel.path,
            desired_access=0,
            share_mode=(w_const.FILE_SHARE_READ |
                        w_const.FILE_SHARE_WRITE |
                        w_const.FILE_SHARE_DELETE),
            creation_disposition=w_const.OPEN_EXISTING)
        self._io_utils.close_handle.assert_called_once_with(
            self._io_utils.open.return_value)

    def test_get_file_id_exc(self):
        self._mock_run.side_effect = exceptions.Win32Exception(
            message="fake exc")

        self.assertRaises(exceptions.Win32Exception,
                          self._pathutils.get_file_id,
                          mock.sentinel.path)
        self._io_utils.close_handle.assert_called_once_with(
            self._io_utils.open.return_value)
