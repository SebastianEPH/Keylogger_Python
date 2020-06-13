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
import inspect
from pkg_resources import parse_version
import textwrap
import time
import types

import eventlet
from eventlet import tpool
import netaddr
from oslo_concurrency import lockutils
from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import reflection
import six

from os_win import constants
from os_win import exceptions


LOG = logging.getLogger(__name__)

socket = eventlet.import_patched('socket')
synchronized = lockutils.synchronized_with_prefix('oswin-')

_WBEM_E_NOT_FOUND = 0x80041002


def execute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() method."""
    return processutils.execute(*cmd, **kwargs)


def parse_server_string(server_str):
    """Parses the given server_string and returns a tuple of host and port.

    If it's not a combination of host part and port, the port element
    is an empty string. If the input is invalid expression, return a tuple of
    two empty strings.
    """

    try:
        # First of all, exclude pure IPv6 address (w/o port).
        if netaddr.valid_ipv6(server_str):
            return (server_str, '')

        # Next, check if this is IPv6 address with a port number combination.
        if server_str.find("]:") != -1:
            (address, port) = server_str.replace('[', '', 1).split(']:')
            return (address, port)

        # Third, check if this is a combination of an address and a port
        if server_str.find(':') == -1:
            return (server_str, '')

        # This must be a combination of an address and a port
        (address, port) = server_str.split(':')
        return (address, port)

    except (ValueError, netaddr.AddrFormatError):
        LOG.error('Invalid server_string: %s', server_str)
        return ('', '')


def get_wrapped_function(function):
    """Get the method at the bottom of a stack of decorators."""
    if not hasattr(function, '__closure__') or not function.__closure__:
        return function

    def _get_wrapped_function(function):
        if not hasattr(function, '__closure__') or not function.__closure__:
            return None

        for closure in function.__closure__:
            func = closure.cell_contents

            deeper_func = _get_wrapped_function(func)
            if deeper_func:
                return deeper_func
            elif isinstance(closure.cell_contents, types.FunctionType):
                return closure.cell_contents

    return _get_wrapped_function(function)


def retry_decorator(max_retry_count=5, timeout=None, inc_sleep_time=1,
                    max_sleep_time=1, exceptions=(), error_codes=(),
                    pass_retry_context=False,
                    extract_err_code_func=None):
    """Retries invoking the decorated method in case of expected exceptions.

    :param max_retry_count: The maximum number of retries performed. If 0, no
                            retry is performed. If None, there will be no limit
                            on the number of retries.
    :param timeout: The maximum time for which we'll retry invoking the method.
                    If 0 or None, there will be no time limit.
    :param inc_sleep_time: The time sleep increment used between retries.
    :param max_sleep_time: The maximum time to wait between retries.
    :param exceptions: A list of expected exceptions for which retries will be
                       performed.
    :param error_codes: A list of expected error codes. The error code is
                        retrieved from the 'error_code' exception attribute,
                        for example in case of Win32Exception. If this argument
                        is not passed, retries will be performed for any of the
                        expected exceptions.
    :param pass_retry_context: Convenient way of letting a method aware of
                               this decorator prevent a retry from being
                               performed. The decorated method must accept an
                               argument called 'retry_context', which will
                               include a dict containing the 'prevent_retry'
                               field. If this field is set, no further retries
                               will be performed.
    :param extract_err_code_func: Optional helper function that extracts the
                                  error code from the exception.
    """

    if isinstance(error_codes, six.integer_types):
        error_codes = (error_codes, )

    def wrapper(f):
        def inner(*args, **kwargs):
            try_count = 0
            sleep_time = 0
            time_start = time.time()

            retry_context = dict(prevent_retry=False)
            if pass_retry_context:
                kwargs['retry_context'] = retry_context

            while True:
                try:
                    return f(*args, **kwargs)
                except exceptions as exc:
                    with excutils.save_and_reraise_exception() as ctxt:
                        if extract_err_code_func:
                            err_code = extract_err_code_func(exc)
                        else:
                            err_code = getattr(exc, 'error_code', None)

                        expected_err_code = (err_code in error_codes or not
                                             error_codes)

                        time_elapsed = time.time() - time_start
                        time_left = (timeout - time_elapsed
                                     if timeout else 'undefined')
                        tries_left = (max_retry_count - try_count
                                      if max_retry_count is not None
                                      else 'undefined')

                        should_retry = (
                            not retry_context['prevent_retry'] and
                            expected_err_code and
                            tries_left and
                            (time_left == 'undefined' or
                             time_left > 0))
                        ctxt.reraise = not should_retry

                        if should_retry:
                            try_count += 1
                            func_name = reflection.get_callable_name(f)

                            sleep_time = min(sleep_time + inc_sleep_time,
                                             max_sleep_time)
                            if timeout:
                                sleep_time = min(sleep_time, time_left)

                            LOG.debug("Got expected exception %(exc)s while "
                                      "calling function %(func_name)s. "
                                      "Retries left: %(retries_left)s. "
                                      "Time left: %(time_left)s. "
                                      "Time elapsed: %(time_elapsed)s "
                                      "Retrying in %(sleep_time)s seconds.",
                                      dict(exc=exc,
                                           func_name=func_name,
                                           retries_left=tries_left,
                                           time_left=time_left,
                                           time_elapsed=time_elapsed,
                                           sleep_time=sleep_time))
                            time.sleep(sleep_time)
        return inner
    return wrapper


def wmi_retry_decorator(exceptions=exceptions.x_wmi, **kwargs):
    """Retry decorator that can be used for specific WMI error codes.

    This function will extract the error code from the hresult. Use
    wmi_retry_decorator_hresult if you want the original hresult to
    be checked.
    """

    def err_code_func(exc):
        com_error = getattr(exc, 'com_error', None)
        if com_error:
            return get_com_error_code(com_error)

    return retry_decorator(extract_err_code_func=err_code_func,
                           exceptions=exceptions,
                           **kwargs)


def wmi_retry_decorator_hresult(exceptions=exceptions.x_wmi, **kwargs):
    """Retry decorator that can be used for specific WMI HRESULTs"""

    def err_code_func(exc):
        com_error = getattr(exc, 'com_error', None)
        if com_error:
            return get_com_error_hresult(com_error)

    return retry_decorator(extract_err_code_func=err_code_func,
                           exceptions=exceptions,
                           **kwargs)


def get_ips(addr):
    addr_info = socket.getaddrinfo(addr, None, 0, 0, 0)
    # Returns IPv4 and IPv6 addresses, ordered by protocol family
    addr_info.sort()
    return [a[4][0] for a in addr_info]


def avoid_blocking_call(f, *args, **kwargs):
    """Ensures that the invoked method will not block other greenthreads.

    Performs the call in a different thread using tpool.execute when called
    from a greenthread.
    """
    # Note that eventlet.getcurrent will always return a greenlet object.
    # In case of a greenthread, the parent greenlet will always be the hub
    # loop greenlet.
    if eventlet.getcurrent().parent:
        return tpool.execute(f, *args, **kwargs)
    else:
        return f(*args, **kwargs)


def avoid_blocking_call_decorator(f):
    def wrapper(*args, **kwargs):
        return avoid_blocking_call(f, *args, **kwargs)
    return wrapper


def hresult_to_err_code(hresult):
    # The last 2 bytes of the hresult store the error code.
    return hresult & 0xFFFF


def get_com_error_hresult(com_error):
    try:
        return ctypes.c_uint(com_error.excepinfo[5]).value
    except Exception:
        LOG.debug("Unable to retrieve COM error hresult: %s", com_error)


def get_com_error_code(com_error):
    hres = get_com_error_hresult(com_error)
    if hres is not None:
        return hresult_to_err_code(hres)


def _is_not_found_exc(exc):
    hresult = get_com_error_hresult(exc.com_error)
    return hresult == _WBEM_E_NOT_FOUND


def not_found_decorator(translated_exc=exceptions.NotFound):
    """Wraps x_wmi: Not Found exceptions as os_win.exceptions.NotFound."""

    def wrapper(func):
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions.x_wmi as ex:
                if _is_not_found_exc(ex):
                    LOG.debug('x_wmi: Not Found exception raised while '
                              'running %s', func.__name__)
                    raise translated_exc(message=six.text_type(ex))
                raise
        return inner
    return wrapper


def hex_str_to_byte_array(string):
    string = string.lower().replace('0x', '')
    if len(string) % 2:
        string = "0%s" % string

    return bytearray(
        [int(hex_byte, 16) for hex_byte in textwrap.wrap(string, 2)])


def byte_array_to_hex_str(byte_aray):
    return ''.join('{:02X}'.format(b) for b in byte_aray)


def required_vm_version(min_version=constants.VM_VERSION_5_0,
                        max_version=constants.VM_VERSION_254_0):
    """Ensures that the wrapped method's VM meets the version requirements.

    Some Hyper-V operations require a minimum VM version in order to succeed.
    For example, Production Checkpoints are supported on VM Versions 6.2 and
    newer.

    Clustering Hyper-V compute nodes may change the list of supported VM
    versions list and the default VM version on that host.

    :param min_version: string, the VM's minimum version required for the
        operation to succeed.
    :param max_version: string, the VM's maximum version required for the
        operation to succeed.
    :raises exceptions.InvalidVMVersion: if the VM's version does not meet the
        given requirements.
    """

    def wrapper(func):
        def inner(*args, **kwargs):
            all_args = inspect.getcallargs(func, *args, **kwargs)
            vmsettings = all_args['vmsettings']

            # NOTE(claudiub): VMs on Windows / Hyper-V Server 2012 do not have
            # a Version field, but they are 4.0.
            vm_version_str = getattr(vmsettings, 'Version', '4.0')
            vm_version = parse_version(vm_version_str)
            if (vm_version >= parse_version(min_version) and
                    vm_version <= parse_version(max_version)):
                return func(*args, **kwargs)

            raise exceptions.InvalidVMVersion(
                vm_name=vmsettings.ElementName, version=vm_version_str,
                min_version=min_version, max_version=max_version)

        return inner
    return wrapper
