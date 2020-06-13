# Copyright 2016 Cloudbase Solutions Srl
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

# Error codes and descriptions, as provided by iscsierr.h

from os_win._i18n import _
from os_win.utils.winapi import constants as w_const

err_msg_dict = {
    w_const.ISDSC_NON_SPECIFIC_ERROR:
        _('A non specific error occurred.'),
    w_const.ISDSC_LOGIN_FAILED:
        _('Login Failed.'),
    w_const.ISDSC_CONNECTION_FAILED:
        _('Connection Failed.'),
    w_const.ISDSC_INITIATOR_NODE_ALREADY_EXISTS:
        _('Initiator Node Already Exists.'),
    w_const.ISDSC_INITIATOR_NODE_NOT_FOUND:
        _('Initiator Node Does Not Exist.'),
    w_const.ISDSC_TARGET_MOVED_TEMPORARILY:
        _('Target Moved Temporarily.'),
    w_const.ISDSC_TARGET_MOVED_PERMANENTLY:
        _('Target Moved Permanently.'),
    w_const.ISDSC_INITIATOR_ERROR:
        _('Initiator Error.'),
    w_const.ISDSC_AUTHENTICATION_FAILURE:
        _('Authentication Failure.'),
    w_const.ISDSC_AUTHORIZATION_FAILURE:
        _('Authorization Failure.'),
    w_const.ISDSC_NOT_FOUND:
        _('Not Found.'),
    w_const.ISDSC_TARGET_REMOVED:
        _('Target Removed.'),
    w_const.ISDSC_UNSUPPORTED_VERSION:
        _('Unsupported Version.'),
    w_const.ISDSC_TOO_MANY_CONNECTIONS:
        _('Too many Connections.'),
    w_const.ISDSC_MISSING_PARAMETER:
        _('Missing Parameter.'),
    w_const.ISDSC_CANT_INCLUDE_IN_SESSION:
        _('Can not include in session.'),
    w_const.ISDSC_SESSION_TYPE_NOT_SUPPORTED:
        _('Session type not supported.'),
    w_const.ISDSC_TARGET_ERROR:
        _('Target Error.'),
    w_const.ISDSC_SERVICE_UNAVAILABLE:
        _('Service Unavailable.'),
    w_const.ISDSC_OUT_OF_RESOURCES:
        _('Out of Resources.'),
    w_const.ISDSC_CONNECTION_ALREADY_EXISTS:
        _('Connections already exist on initiator node.'),
    w_const.ISDSC_SESSION_ALREADY_EXISTS:
        _('Session Already Exists.'),
    w_const.ISDSC_INITIATOR_INSTANCE_NOT_FOUND:
        _('Initiator Instance Does Not Exist.'),
    w_const.ISDSC_TARGET_ALREADY_EXISTS:
        _('Target Already Exists.'),
    w_const.ISDSC_DRIVER_BUG:
        _('The iscsi driver implementation did '
          'not complete an operation correctly.'),
    w_const.ISDSC_INVALID_TEXT_KEY:
        _('An invalid key text was encountered.'),
    w_const.ISDSC_INVALID_SENDTARGETS_TEXT:
        _('Invalid SendTargets response text was encountered.'),
    w_const.ISDSC_INVALID_SESSION_ID:
        _('Invalid Session Id.'),
    w_const.ISDSC_SCSI_REQUEST_FAILED:
        _('The scsi request failed.'),
    w_const.ISDSC_TOO_MANY_SESSIONS:
        _('Exceeded max sessions for this initiator.'),
    w_const.ISDSC_SESSION_BUSY:
        _('Session is busy since a request is already in progress.'),
    w_const.ISDSC_TARGET_MAPPING_UNAVAILABLE:
        _('The target mapping requested is not available.'),
    w_const.ISDSC_ADDRESS_TYPE_NOT_SUPPORTED:
        _('The Target Address type given is not supported.'),
    w_const.ISDSC_LOGON_FAILED:
        _('Logon Failed.'),
    w_const.ISDSC_SEND_FAILED:
        _('TCP Send Failed.'),
    w_const.ISDSC_TRANSPORT_ERROR:
        _('TCP Transport Error'),
    w_const.ISDSC_VERSION_MISMATCH:
        _('iSCSI Version Mismatch'),
    w_const.ISDSC_TARGET_MAPPING_OUT_OF_RANGE:
        _('The Target Mapping Address passed is out of range for the '
          'adapter configuration.'),
    w_const.ISDSC_TARGET_PRESHAREDKEY_UNAVAILABLE:
        _('The preshared key for the target or IKE identification '
          'payload is not available.'),
    w_const.ISDSC_TARGET_AUTHINFO_UNAVAILABLE:
        _('The authentication information for '
          'the target is not available.'),
    w_const.ISDSC_TARGET_NOT_FOUND:
        _('The target name is not found or is '
          'marked as hidden from login.'),
    w_const.ISDSC_LOGIN_USER_INFO_BAD:
        _('One or more parameters specified in '
          'LoginTargetIN structure is invalid.'),
    w_const.ISDSC_TARGET_MAPPING_EXISTS:
        _('Given target mapping already exists.'),
    w_const.ISDSC_HBA_SECURITY_CACHE_FULL:
        _('The HBA security information cache '
          'is full.'),
    w_const.ISDSC_INVALID_PORT_NUMBER:
        _('The port number passed is '
          'not valid for the initiator.'),
    w_const.ISDSC_OPERATION_NOT_ALL_SUCCESS:
        _('The operation was not successful '
          'for all initiators or discovery '
          'methods.'),
    w_const.ISDSC_HBA_SECURITY_CACHE_NOT_SUPPORTED:
        _('The HBA security information '
          'cache is not supported by '
          'this adapter.'),
    w_const.ISDSC_IKE_ID_PAYLOAD_TYPE_NOT_SUPPORTED:
        _('The IKE id payload type '
          'specified is not supported.'),
    w_const.ISDSC_IKE_ID_PAYLOAD_INCORRECT_SIZE:
        _('The IKE id payload size '
          'specified is not correct.'),
    w_const.ISDSC_TARGET_PORTAL_ALREADY_EXISTS:
        _('Target Portal Structure '
          'Already Exists.'),
    w_const.ISDSC_TARGET_ADDRESS_ALREADY_EXISTS:
        _('Target Address Structure '
          'Already Exists.'),
    w_const.ISDSC_NO_AUTH_INFO_AVAILABLE:
        _('There is no IKE authentication '
          'information available.'),
    w_const.ISDSC_NO_TUNNEL_OUTER_MODE_ADDRESS:
        _('There is no tunnel mode outer '
          'address specified.'),
    w_const.ISDSC_CACHE_CORRUPTED:
        _('Authentication or tunnel '
          'address cache is corrupted.'),
    w_const.ISDSC_REQUEST_NOT_SUPPORTED:
        _('The request or operation '
          'is not supported.'),
    w_const.ISDSC_TARGET_OUT_OF_RESORCES:
        _('The target does not have enough '
          'resources to process the '
          'given request.'),
    w_const.ISDSC_SERVICE_DID_NOT_RESPOND:
        _('The initiator service did '
          'not respond to the request '
          'sent by the driver.'),
    w_const.ISDSC_ISNS_SERVER_NOT_FOUND:
        _('The Internet Storage Name Server (iSNS) '
          'server was not found or is unavailable.'),
    w_const.ISDSC_OPERATION_REQUIRES_REBOOT:
        _('The operation was successful but '
          'requires a driver reload or reboot '
          'to become effective.'),
    w_const.ISDSC_NO_PORTAL_SPECIFIED:
        _('There is no target portal available '
          'to complete the login.'),
    w_const.ISDSC_CANT_REMOVE_LAST_CONNECTION:
        _('Cannot remove the last '
          'connection for a session.'),
    w_const.ISDSC_SERVICE_NOT_RUNNING:
        _('The Microsoft iSCSI initiator '
          'service has not been started.'),
    w_const.ISDSC_TARGET_ALREADY_LOGGED_IN:
        _('The target has already been '
          'logged in via an iSCSI session.'),
    w_const.ISDSC_DEVICE_BUSY_ON_SESSION:
        _('The session cannot be logged out '
          'since a device on that session is '
          'currently being used.'),
    w_const.ISDSC_COULD_NOT_SAVE_PERSISTENT_LOGIN_DATA:
        _('Failed to save persistent '
          'login information.'),
    w_const.ISDSC_COULD_NOT_REMOVE_PERSISTENT_LOGIN_DATA:
        _('Failed to remove '
          'persistent login '
          'information.'),
    w_const.ISDSC_PORTAL_NOT_FOUND:
        _('The specified portal was not found.'),
    w_const.ISDSC_INITIATOR_NOT_FOUND:
        _('The specified initiator '
          'name was not found.'),
    w_const.ISDSC_DISCOVERY_MECHANISM_NOT_FOUND:
        _('The specified discovery '
          'mechanism was not found.'),
    w_const.ISDSC_IPSEC_NOT_SUPPORTED_ON_OS:
        _('iSCSI does not support IPSEC '
          'for this version of the OS.'),
    w_const.ISDSC_PERSISTENT_LOGIN_TIMEOUT:
        _('The iSCSI service timed out waiting '
          'for all persistent logins to '
          'complete.'),
    w_const.ISDSC_SHORT_CHAP_SECRET:
        _('The specified CHAP secret is less than '
          '96 bits and will not be usable for '
          'authenticating over non ipsec connections.'),
    w_const.ISDSC_EVALUATION_PEROID_EXPIRED:
        _('The evaluation period for the '
          'iSCSI initiator service has '
          'expired.'),
    w_const.ISDSC_INVALID_CHAP_SECRET:
        _('CHAP secret given does not conform '
          'to the standard. Please see system '
          'event log for more information.'),
    w_const.ISDSC_INVALID_TARGET_CHAP_SECRET:
        _('Target CHAP secret given is invalid. Maximum size of CHAP secret'
          'is 16 bytes. Minimum size is 12 bytes if IPSec is not used.'),
    w_const.ISDSC_INVALID_INITIATOR_CHAP_SECRET:
        _('Initiator CHAP secret given is '
          'invalid. Maximum size of CHAP '
          'secret is 16 bytes. Minimum size '
          'is 12 bytes if IPSec is '
          'not used.'),
    w_const.ISDSC_INVALID_CHAP_USER_NAME:
        _('CHAP Username given is invalid.'),
    w_const.ISDSC_INVALID_LOGON_AUTH_TYPE:
        _('Logon Authentication type '
          'given is invalid.'),
    w_const.ISDSC_INVALID_TARGET_MAPPING:
        _('Target Mapping information '
          'given is invalid.'),
    w_const.ISDSC_INVALID_TARGET_ID:
        _('Target Id given in '
          'Target Mapping is invalid.'),
    w_const.ISDSC_INVALID_ISCSI_NAME:
        _('The iSCSI name specified contains '
          'invalid characters or is too long.'),
    w_const.ISDSC_INCOMPATIBLE_ISNS_VERSION:
        _('The version number returned from the '
          'Internet Storage Name Server (iSNS) '
          'server is not compatible with this '
          'version of the iSNS client.'),
    w_const.ISDSC_FAILED_TO_CONFIGURE_IPSEC:
        _('Initiator failed to configure IPSec '
          'for the given connection. This could '
          'be because of low resources.'),
    w_const.ISDSC_BUFFER_TOO_SMALL:
        _('The buffer given for processing '
          'the request is too small.'),
    w_const.ISDSC_INVALID_LOAD_BALANCE_POLICY:
        _('The given Load Balance '
          'policy is not recognized '
          'by iScsi initiator.'),
    w_const.ISDSC_INVALID_PARAMETER:
        _('One or more paramaters '
          'specified is not valid.'),
    w_const.ISDSC_DUPLICATE_PATH_SPECIFIED:
        _('Duplicate PathIds were '
          'specified in the call to '
          'set Load Balance Policy.'),
    w_const.ISDSC_PATH_COUNT_MISMATCH:
        _('Number of paths specified in '
          'Set Load Balance Policy does not '
          'match the number of paths to the target.'),
    w_const.ISDSC_INVALID_PATH_ID:
        _('Path Id specified in the call to '
          'set Load Balance Policy is not valid'),
    w_const.ISDSC_MULTIPLE_PRIMARY_PATHS_SPECIFIED:
        _('Multiple primary paths '
          'specified when only one '
          'primary path is expected.'),
    w_const.ISDSC_NO_PRIMARY_PATH_SPECIFIED:
        _('No primary path specified when '
          'at least one is expected.'),
    w_const.ISDSC_DEVICE_ALREADY_PERSISTENTLY_BOUND:
        _('Device is already a '
          'persistently bound device.'),
    w_const.ISDSC_DEVICE_NOT_FOUND:
        _('Device was not found.'),
    w_const.ISDSC_DEVICE_NOT_ISCSI_OR_PERSISTENT:
        _('The device specified does not '
          'originate from an iSCSI disk '
          'or a persistent iSCSI login.'),
    w_const.ISDSC_DNS_NAME_UNRESOLVED:
        _('The DNS name specified was not resolved.'),
    w_const.ISDSC_NO_CONNECTION_AVAILABLE:
        _('There is no connection available '
          'in the iSCSI session to '
          'process the request.'),
    w_const.ISDSC_LB_POLICY_NOT_SUPPORTED:
        _('The given Load Balance '
          'policy is not supported.'),
    w_const.ISDSC_REMOVE_CONNECTION_IN_PROGRESS:
        _('A remove connection request '
          'is already in progress for '
          'this session.'),
    w_const.ISDSC_INVALID_CONNECTION_ID:
        _('Given connection was not '
          'found in the session.'),
    w_const.ISDSC_CANNOT_REMOVE_LEADING_CONNECTION:
        _('The leading connection in '
          'the session cannot be '
          'removed.'),
    w_const.ISDSC_RESTRICTED_BY_GROUP_POLICY:
        _('The operation cannot be performed '
          'since it does not conform with '
          'the group policy assigned to '
          'this computer.'),
    w_const.ISDSC_ISNS_FIREWALL_BLOCKED:
        _('The operation cannot be performed since '
          'the Internet Storage Name Server '
          '(iSNS) firewall exception has '
          'not been enabled.'),
    w_const.ISDSC_FAILURE_TO_PERSIST_LB_POLICY:
        _('Failed to persist load '
          'balancing policy parameters.'),
    w_const.ISDSC_INVALID_HOST:
        _('The name could not be resolved to an IP Address.'),
}
