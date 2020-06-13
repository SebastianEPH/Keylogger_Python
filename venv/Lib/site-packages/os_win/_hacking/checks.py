# Copyright 2015 Cloudbase Solutions Srl
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

import ast
import os
import re

from os_win.utils.winapi import libs as w_lib

"""
Guidelines for writing new hacking checks

 - Use only for os_win specific tests. OpenStack general tests
   should be submitted to the common 'hacking' module.
 - Pick numbers in the range N3xx. Find the current test with
   the highest allocated number and then pick the next value.
 - Keep the test method code in the source file ordered based
   on the N3xx value.
 - List the new rule in the top level HACKING.rst file
"""

UNDERSCORE_IMPORT_FILES = []

cfg_re = re.compile(r".*\scfg\.")
asse_trueinst_re = re.compile(
    r"(.)*assertTrue\(isinstance\((\w|\.|\'|\"|\[|\])+, "
    "(\w|\.|\'|\"|\[|\])+\)\)")
asse_equal_type_re = re.compile(
    r"(.)*assertEqual\(type\((\w|\.|\'|\"|\[|\])+\), "
    "(\w|\.|\'|\"|\[|\])+\)")
asse_equal_in_end_with_true_or_false_re = re.compile(
    r"assertEqual\("
    r"(\w|[][.'\"])+ in (\w|[][.'\", ])+, (True|False)\)")
asse_equal_in_start_with_true_or_false_re = re.compile(
    r"assertEqual\("
    r"(True|False), (\w|[][.'\"])+ in (\w|[][.'\", ])+\)")
asse_equal_end_with_none_re = re.compile(
    r"assertEqual\(.*?,\s+None\)$")
asse_equal_start_with_none_re = re.compile(
    r"assertEqual\(None,")
asse_true_false_with_in_or_not_in = re.compile(
    r"assert(True|False)\("
    r"(\w|[][.'\"])+( not)? in (\w|[][.'\",])+(, .*)?\)")
asse_true_false_with_in_or_not_in_spaces = re.compile(
    r"assert(True|False)"
    r"\((\w|[][.'\"])+( not)? in [\[|'|\"](\w|[][.'\", ])+"
    r"[\[|'|\"](, .*)?\)")
asse_raises_regexp = re.compile(r"assertRaisesRegexp\(")
conf_attribute_set_re = re.compile(r"CONF\.[a-z0-9_.]+\s*=\s*\w")
_all_log_levels = {'critical', 'error', 'exception', 'info',
                   'warning', 'debug'}
# Since _Lx() have been removed, we just need to check _()
_log_translation_hint = re.compile(
    r".*LOG\.(%(levels)s)\(\s*(%(hints)s)\(" % {
        'levels': '|'.join(_all_log_levels),
        'hints': '_',
    })
mutable_default_args = re.compile(r"^\s*def .+\((.+=\{\}|.+=\[\])")
string_translation = re.compile(r"[^_]*_\(\s*('|\")")
underscore_import_check = re.compile(r"(.)*import _(.)*")
import_translation_for_log_or_exception = re.compile(
    r"(.)*(from\sos_win._i18n\simport)\s_")
# We need this for cases where they have created their own _ function.
custom_underscore_check = re.compile(r"(.)*_\s*=\s*(.)*")
dict_constructor_with_list_copy_re = re.compile(r".*\bdict\((\[)?(\(|\[)")
ctypes_external_lib_re = re.compile(r"ctypes\.(?:win|c|py|ole)dll",
                                    re.IGNORECASE)
ctypes_func_typedefs_re = re.compile(
    r"(?:^|[^\w])(%s)\.(\w+)" % '|'.join(w_lib.libs),
    re.IGNORECASE)

_module_src_cache = {}


class BaseASTChecker(ast.NodeVisitor):
    """Provides a simple framework for writing AST-based checks.

    Subclasses should implement visit_* methods like any other AST visitor
    implementation. When they detect an error for a particular node the
    method should call ``self.add_error(offending_node)``. Details about
    where in the code the error occurred will be pulled from the node
    object.

    Subclasses should also provide a class variable named CHECK_DESC to
    be used for the human readable error message.

    """

    def __init__(self, tree, filename):
        """This object is created automatically by pep8.

        :param tree: an AST tree
        :param filename: name of the file being analyzed
                         (ignored by our checks)
        """
        self._tree = tree
        self._errors = []

    def run(self):
        """Called automatically by pep8."""
        self.visit(self._tree)
        return self._errors

    def add_error(self, node, message=None):
        """Add an error caused by a node to the list of errors for pep8."""
        message = message or self.CHECK_DESC
        error = (node.lineno, node.col_offset, message, self.__class__)
        self._errors.append(error)

    def _check_call_names(self, call_node, names):
        if isinstance(call_node, ast.Call):
            if isinstance(call_node.func, ast.Name):
                if call_node.func.id in names:
                    return True
        return False


def use_timeutils_utcnow(logical_line, filename):
    # tools are OK to use the standard datetime module
    if "/tools/" in filename:
        return

    msg = "N310: timeutils.utcnow() must be used instead of datetime.%s()"

    datetime_funcs = ['now', 'utcnow']
    for f in datetime_funcs:
        pos = logical_line.find('datetime.%s' % f)
        if pos != -1:
            yield (pos, msg % f)


def capital_cfg_help(logical_line, tokens):
    msg = "N313: capitalize help string"

    if cfg_re.match(logical_line):
        for t in range(len(tokens)):
            if tokens[t][1] == "help":
                txt = tokens[t + 2][1]
                if len(txt) > 1 and txt[1].islower():
                        yield(0, msg)


def assert_true_instance(logical_line):
    """Check for assertTrue(isinstance(a, b)) sentences

    N316
    """
    if asse_trueinst_re.match(logical_line):
        yield (0, "N316: assertTrue(isinstance(a, b)) sentences not allowed")


def assert_equal_type(logical_line):
    """Check for assertEqual(type(A), B) sentences

    N317
    """
    if asse_equal_type_re.match(logical_line):
        yield (0, "N317: assertEqual(type(A), B) sentences not allowed")


def assert_equal_none(logical_line):
    """Check for assertEqual(A, None) or assertEqual(None, A) sentences

    N318
    """
    res = (asse_equal_start_with_none_re.search(logical_line) or
           asse_equal_end_with_none_re.search(logical_line))
    if res:
        yield (0, "N318: assertEqual(A, None) or assertEqual(None, A) "
               "sentences not allowed")


def no_translate_logs(logical_line):
    """Check for 'LOG.*(_('

    Starting with the Pike series, OpenStack no longer supports log
    translation. We shouldn't translate logs.

    - This check assumes that 'LOG' is a logger.
    - Use filename so we can start enforcing this in specific folders
      instead of needing to do so all at once.

    C312
    """
    if _log_translation_hint.match(logical_line):
        yield(0, "C312: Log messages should not be translated!")


def no_import_translation_in_tests(logical_line, filename):
    """Check for 'from os_win._i18n import _'

    N337
    """

    if 'os_win/tests/' in filename:
        res = import_translation_for_log_or_exception.match(logical_line)
        if res:
            yield(0, "N337 Don't import translation in tests")


def no_setting_conf_directly_in_tests(logical_line, filename):
    """Check for setting CONF.* attributes directly in tests

    The value can leak out of tests affecting how subsequent tests run.
    Using self.flags(option=value) is the preferred method to temporarily
    set config options in tests.

    N320
    """

    if 'os_win/tests/' in filename:
        res = conf_attribute_set_re.match(logical_line)
        if res:
            yield (0, "N320: Setting CONF.* attributes directly in tests is "
                      "forbidden. Use self.flags(option=value) instead")


def no_mutable_default_args(logical_line):
    msg = "N322: Method's default argument shouldn't be mutable!"
    if mutable_default_args.match(logical_line):
        yield (0, msg)


def check_explicit_underscore_import(logical_line, filename):
    """Check for explicit import of the _ function

    We need to ensure that any files that are using the _() function
    to translate logs are explicitly importing the _ function.  We
    can't trust unit test to catch whether the import has been
    added so we need to check for it here.
    """

    # Build a list of the files that have _ imported.  No further
    # checking needed once it is found.
    if filename in UNDERSCORE_IMPORT_FILES:
        pass
    elif (underscore_import_check.match(logical_line) or
          custom_underscore_check.match(logical_line)):
        UNDERSCORE_IMPORT_FILES.append(filename)
    elif string_translation.match(logical_line):
        yield(0, "N323: Found use of _() without explicit import of _ !")


def use_jsonutils(logical_line, filename):
    # tools are OK to use the standard json module
    if "/tools/" in filename:
        return

    msg = "N324: jsonutils.%(fun)s must be used instead of json.%(fun)s"

    if "json." in logical_line:
        json_funcs = ['dumps(', 'dump(', 'loads(', 'load(']
        for f in json_funcs:
            pos = logical_line.find('json.%s' % f)
            if pos != -1:
                yield (pos, msg % {'fun': f[:-1]})


class CheckForStrUnicodeExc(BaseASTChecker):
    """Checks for the use of str() or unicode() on an exception.

    This currently only handles the case where str() or unicode()
    is used in the scope of an exception handler.  If the exception
    is passed into a function, returned from an assertRaises, or
    used on an exception created in the same scope, this does not
    catch it.
    """

    CHECK_DESC = ('N325 str() and unicode() cannot be used on an '
                  'exception.  Remove or use six.text_type()')

    def __init__(self, tree, filename):
        super(CheckForStrUnicodeExc, self).__init__(tree, filename)
        self.name = []
        self.already_checked = []

    def visit_TryExcept(self, node):
        for handler in node.handlers:
            if handler.name:
                self.name.append(handler.name.id)
                super(CheckForStrUnicodeExc, self).generic_visit(node)
                self.name = self.name[:-1]
            else:
                super(CheckForStrUnicodeExc, self).generic_visit(node)

    def visit_Call(self, node):
        if self._check_call_names(node, ['str', 'unicode']):
            if node not in self.already_checked:
                self.already_checked.append(node)
                if isinstance(node.args[0], ast.Name):
                    if node.args[0].id in self.name:
                        self.add_error(node.args[0])
        super(CheckForStrUnicodeExc, self).generic_visit(node)


class CheckForTransAdd(BaseASTChecker):
    """Checks for the use of concatenation on a translated string.

    Translations should not be concatenated with other strings, but
    should instead include the string being added to the translated
    string to give the translators the most information.
    """

    CHECK_DESC = ('N326 Translated messages cannot be concatenated.  '
                  'String should be included in translated message.')

    TRANS_FUNC = ['_', '_LI', '_LW', '_LE', '_LC']

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Add):
            if self._check_call_names(node.left, self.TRANS_FUNC):
                self.add_error(node.left)
            elif self._check_call_names(node.right, self.TRANS_FUNC):
                self.add_error(node.right)
        super(CheckForTransAdd, self).generic_visit(node)


def assert_true_or_false_with_in(logical_line):
    """Check for assertTrue/False(A in B), assertTrue/False(A not in B),

    assertTrue/False(A in B, message) or assertTrue/False(A not in B, message)
    sentences.

    N334
    """

    res = (asse_true_false_with_in_or_not_in.search(logical_line) or
           asse_true_false_with_in_or_not_in_spaces.search(logical_line))
    if res:
        yield (0, "N334: Use assertIn/NotIn(A, B) rather than "
                  "assertTrue/False(A in/not in B) when checking collection "
                  "contents.")


def assert_raises_regexp(logical_line):
    """Check for usage of deprecated assertRaisesRegexp

    N335
    """

    res = asse_raises_regexp.search(logical_line)
    if res:
        yield (0, "N335: assertRaisesRegex must be used instead "
                  "of assertRaisesRegexp")


def dict_constructor_with_list_copy(logical_line):
    msg = ("N336: Must use a dict comprehension instead of a dict constructor"
           " with a sequence of key-value pairs."
           )
    if dict_constructor_with_list_copy_re.match(logical_line):
        yield (0, msg)


def assert_equal_in(logical_line):
    """Check for assertEqual(A in B, True), assertEqual(True, A in B),

    assertEqual(A in B, False) or assertEqual(False, A in B) sentences

    N338
    """

    res = (asse_equal_in_start_with_true_or_false_re.search(logical_line) or
           asse_equal_in_end_with_true_or_false_re.search(logical_line))
    if res:
        yield (0, "N338: Use assertIn/NotIn(A, B) rather than "
                  "assertEqual(A in B, True/False) when checking collection "
                  "contents.")


def assert_ctypes_libs_not_used_directly(logical_line, filename):
    # We allow this only for the modules containing the library definitions.
    w_lib_path = os.path.join(*w_lib.__name__.split('.'))

    if w_lib_path in filename:
        return

    res = ctypes_external_lib_re.search(logical_line)
    if res:
        yield (0, "O301: Using external libraries via ctypes directly "
                  "is not allowed. Please use the following function to "
                  "retrieve a supported library handle: "
                  "%s.get_shared_lib_handle" % w_lib.__name__)


def _get_module_src(path):
    if not _module_src_cache.get(path):
        with open(path, 'r') as f:
            _module_src_cache[path] = f.read()

    return _module_src_cache[path]


def assert_ctypes_foreign_func_argtypes_defined(logical_line):
    res = ctypes_func_typedefs_re.findall(logical_line)

    for lib_name, func_name in res:
        mod_path = "%s.py" % os.path.join(os.path.dirname(w_lib.__file__),
                                          lib_name)
        module_src = _get_module_src(mod_path)

        argtypes_expr = "%s.argtypes =" % func_name
        restype_expr = "%s.restype =" % func_name

        if not (argtypes_expr in module_src and restype_expr in module_src):
            yield (0, "O302: Foreign function called using ctypes without "
                      "having its argument and return value types declared "
                      "in %s.%s.py." % (w_lib.__name__, lib_name))


def factory(register):
    register(use_timeutils_utcnow)
    register(capital_cfg_help)
    register(no_import_translation_in_tests)
    register(assert_true_instance)
    register(assert_equal_type)
    register(assert_equal_none)
    register(assert_raises_regexp)
    register(no_translate_logs)
    register(no_setting_conf_directly_in_tests)
    register(no_mutable_default_args)
    register(check_explicit_underscore_import)
    register(use_jsonutils)
    register(CheckForStrUnicodeExc)
    register(CheckForTransAdd)
    register(assert_true_or_false_with_in)
    register(dict_constructor_with_list_copy)
    register(assert_equal_in)
    register(assert_ctypes_libs_not_used_directly)
    register(assert_ctypes_foreign_func_argtypes_defined)
