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

import os
import textwrap

import mock
import pycodestyle

from os_win._hacking import checks
from os_win.tests.unit import test_base


class HackingTestCase(test_base.OsWinBaseTestCase):
    """This class tests the hacking checks in os_win.hacking.checks.

    This is accomplished by passing strings to the check methods like the
    pep8/flake8 parser would. The parser loops over each line in the file and
    then passes the parameters to the check method. The parameter names in the
    check method dictate what type of object is passed to the check method.

    The parameter types are:
        logical_line: A processed line with the following modifications:
            - Multi-line statements converted to a single line.
            - Stripped left and right.
            - Contents of strings replaced with "xxx" of same length.
            - Comments removed.
        physical_line: Raw line of text from the input file.
        lines: a list of the raw lines from the input file
        tokens: the tokens that contribute to this logical line
        line_number: line number in the input file
        total_lines: number of lines in the input file
        blank_lines: blank lines before this one
        indent_char: indentation character in this file (" " or "\t")
        indent_level: indentation (with tabs expanded to multiples of 8)
        previous_indent_level: indentation on previous line
        previous_logical: previous logical line
        filename: Path of the file being run through pep8

    When running a test on a check method the return will be False/None if
    there is no violation in the sample input. If there is an error a tuple is
    returned with a position in the line, and a message. So to check the result
    just assertTrue if the check is expected to fail and assertFalse if it
    should pass.
    """

    def _run_check(self, code, checker, filename=None):
        # We are patching pycodestyle (pep8) so that only the check under test
        # is actually installed.
        mock_checks = {'physical_line': {}, 'logical_line': {}, 'tree': {}}
        with mock.patch('pycodestyle._checks', mock_checks):
            pycodestyle.register_check(checker)

            lines = textwrap.dedent(code).strip().splitlines(True)

            checker = pycodestyle.Checker(filename=filename, lines=lines)
            # NOTE(sdague): the standard reporter has printing to stdout
            # as a normal part of check_all, which bleeds through to the
            # test output stream in an unhelpful way. This blocks that
            # printing.
            with mock.patch('pycodestyle.StandardReport.get_file_results'):
                checker.check_all()
            checker.report._deferred_print.sort()
            return checker.report._deferred_print

    def _assert_has_errors(self, code, checker, expected_errors=None,
                           filename=None):
        actual_errors = [e[:3] for e in
                         self._run_check(code, checker, filename)]
        self.assertEqual(expected_errors or [], actual_errors)

    def _assert_has_no_errors(self, code, checker, filename=None):
        self._assert_has_errors(code, checker, filename=filename)

    def test_ctypes_libs_not_used_directly(self):
        checker = checks.assert_ctypes_libs_not_used_directly
        errors = [(1, 0, 'O301')]

        code = "ctypes.cdll.hbaapi"
        self._assert_has_errors(code, checker, expected_errors=errors)

        code = "ctypes.windll.hbaapi.fake_func(fake_arg)"
        self._assert_has_errors(code, checker, expected_errors=errors)

        code = "fake_var = ctypes.oledll.hbaapi.fake_func(fake_arg)"
        self._assert_has_errors(code, checker, expected_errors=errors)

        code = "foo(ctypes.pydll.hbaapi.fake_func(fake_arg))"
        self._assert_has_errors(code, checker, expected_errors=errors)

        code = "ctypes.cdll.LoadLibrary(fake_lib)"
        self._assert_has_errors(code, checker, expected_errors=errors)

        code = "ctypes.WinDLL('fake_lib_path')"
        self._assert_has_errors(code, checker, expected_errors=errors)

        code = "ctypes.cdll.hbaapi"
        filename = os.path.join("os_win", "utils", "winapi",
                                "libs", "hbaapi.py")
        self._assert_has_no_errors(code, checker, filename=filename)

    def test_ctypes_foreign_func_argtypes_defined(self):
        checker = checks.assert_ctypes_foreign_func_argtypes_defined
        errors = [(1, 0, 'O302')]

        code = "kernel32.FakeFunc(fake_arg)"
        self._assert_has_errors(code, checker, errors)

        code = "fake_func(kernel32.FakeFunc(fake_arg))"
        self._assert_has_errors(code, checker, errors)

        code = "kernel32.WaitNamedPipeW(x, y)"
        self._assert_has_no_errors(code, checker)

        code = "_fake_kernel32.WaitNamedPipeW(x, y)"
        self._assert_has_no_errors(code, checker)

    def test_no_log_translations(self):
        for log in checks._all_log_levels:
            bad = 'LOG.%s(_("Bad"))' % log
            self.assertEqual(1, len(list(checks.no_translate_logs(bad))))
            # Catch abuses when used with a variable and not a literal
            bad = 'LOG.%s(_(msg))' % log
            self.assertEqual(1, len(list(checks.no_translate_logs(bad))))
