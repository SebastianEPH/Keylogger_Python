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

import ctypes

import mock
import six

from os_win import _utils
from os_win import exceptions
from os_win.tests.unit import test_base
from os_win.utils.storage.initiator import fc_utils
from os_win.utils.winapi.libs import hbaapi as fc_struct


class FCUtilsTestCase(test_base.BaseTestCase):
    """Unit tests for the Hyper-V FCUtils class."""

    _autospec_classes = [
        fc_utils.win32utils.Win32Utils,
        fc_utils.diskutils.DiskUtils,
    ]

    _FAKE_ADAPTER_NAME = 'fake_adapter_name'
    _FAKE_ADAPTER_WWN = list(range(8))

    def setUp(self):
        super(FCUtilsTestCase, self).setUp()
        self._setup_lib_mocks()

        self._fc_utils = fc_utils.FCUtils()
        self._diskutils = self._fc_utils._diskutils

        self._run_mocker = mock.patch.object(self._fc_utils,
                                             '_run_and_check_output')
        self._run_mocker.start()

        self._mock_run = self._fc_utils._run_and_check_output

        self.addCleanup(mock.patch.stopall)

    def _setup_lib_mocks(self):
        self._ctypes = mock.Mock()
        # This is used in order to easily make assertions on the variables
        # passed by reference.
        self._ctypes.byref = lambda x: (x, "byref")

        mock.patch.object(fc_utils, 'hbaapi', create=True).start()
        self._ctypes_mocker = mock.patch.object(fc_utils, 'ctypes',
                                                self._ctypes)
        self._ctypes_mocker.start()

    def test_run_and_check_output(self):
        self._run_mocker.stop()
        self._fc_utils._run_and_check_output(
            adapter_name=self._FAKE_ADAPTER_NAME)

        mock_win32_run = self._fc_utils._win32_utils.run_and_check_output
        mock_win32_run.assert_called_once_with(
            adapter_name=self._FAKE_ADAPTER_NAME,
            failure_exc=exceptions.FCWin32Exception)

    def test_get_wwn_struct_from_hex_str(self):
        wwn_b_array = list(range(8))
        wwn_str = _utils.byte_array_to_hex_str(wwn_b_array)

        wwn_struct = self._fc_utils._wwn_struct_from_hex_str(wwn_str)
        self.assertEqual(wwn_b_array, list(wwn_struct.wwn))

    def test_get_fc_hba_count(self):
        hba_count = self._fc_utils.get_fc_hba_count()

        fc_utils.hbaapi.HBA_GetNumberOfAdapters.assert_called_once_with()
        self.assertEqual(fc_utils.hbaapi.HBA_GetNumberOfAdapters.return_value,
                         hba_count)

    def test_open_adapter_by_name(self):
        self._ctypes_mocker.stop()

        self._mock_run.return_value = mock.sentinel.handle

        resulted_handle = self._fc_utils._open_adapter_by_name(
            self._FAKE_ADAPTER_NAME)

        args_list = self._mock_run.call_args_list[0][0]
        self.assertEqual(fc_utils.hbaapi.HBA_OpenAdapter, args_list[0])
        self.assertEqual(six.b(self._FAKE_ADAPTER_NAME), args_list[1].value)

        self.assertEqual(mock.sentinel.handle, resulted_handle)

    @mock.patch.object(fc_utils.fc_struct, 'HBA_HANDLE')
    def test_open_adapter_by_wwn(self, mock_hba_handle_struct):
        exp_handle = mock_hba_handle_struct.return_value
        resulted_handle = self._fc_utils._open_adapter_by_wwn(
            mock.sentinel.wwn)

        self.assertEqual(exp_handle, resulted_handle)

        self._mock_run.assert_called_once_with(
            fc_utils.hbaapi.HBA_OpenAdapterByWWN,
            self._ctypes.byref(exp_handle),
            mock.sentinel.wwn)

    def test_close_adapter(self):
        self._fc_utils._close_adapter(mock.sentinel.hba_handle)
        fc_utils.hbaapi.HBA_CloseAdapter.assert_called_once_with(
            mock.sentinel.hba_handle)

    @mock.patch.object(fc_utils.FCUtils, '_open_adapter_by_name')
    @mock.patch.object(fc_utils.FCUtils, '_close_adapter')
    def test_get_hba_handle_by_name(self, mock_close_adapter,
                                    mock_open_adapter):
        with self._fc_utils._get_hba_handle(
                adapter_name=self._FAKE_ADAPTER_NAME) as handle:
            self.assertEqual(mock_open_adapter.return_value, handle)
            mock_open_adapter.assert_called_once_with(
                self._FAKE_ADAPTER_NAME)
        mock_close_adapter.assert_called_once_with(
            mock_open_adapter.return_value)

    @mock.patch.object(fc_utils.FCUtils, '_open_adapter_by_wwn')
    @mock.patch.object(fc_utils.FCUtils, '_close_adapter')
    def test_get_hba_handle_by_wwn(self, mock_close_adapter,
                                   mock_open_adapter):
        with self._fc_utils._get_hba_handle(
                adapter_wwn_struct=mock.sentinel.wwn) as handle:
            self.assertEqual(mock_open_adapter.return_value, handle)
            mock_open_adapter.assert_called_once_with(mock.sentinel.wwn)
        mock_close_adapter.assert_called_once_with(
            mock_open_adapter.return_value)

    def test_get_hba_handle_missing_params(self):
        self.assertRaises(exceptions.FCException,
                          self._fc_utils._get_hba_handle().__enter__)

    def test_get_adapter_name(self):
        self._ctypes_mocker.stop()
        fake_adapter_index = 1

        def update_buff(func, adapter_index, buff):
            buff.value = six.b(self._FAKE_ADAPTER_NAME)

        self._mock_run.side_effect = update_buff

        resulted_adapter_name = self._fc_utils._get_adapter_name(
            fake_adapter_index)

        args_list = self._mock_run.call_args_list[0][0]

        self.assertEqual(fc_utils.hbaapi.HBA_GetAdapterName,
                         args_list[0])
        self.assertIsInstance(args_list[1], ctypes.c_uint32)
        self.assertEqual(fake_adapter_index, args_list[1].value)

        buff = ctypes.cast(args_list[2], ctypes.POINTER(
            ctypes.c_char * 256)).contents
        self.assertIsInstance(buff, ctypes.c_char * 256)
        self.assertEqual(self._FAKE_ADAPTER_NAME, resulted_adapter_name)

    @mock.patch.object(fc_struct, 'get_target_mapping_struct')
    def test_get_target_mapping(self, mock_get_target_mapping):
        fake_entry_count = 10
        hresults = [fc_utils.HBA_STATUS_ERROR_MORE_DATA,
                    fc_utils.HBA_STATUS_OK]
        mock_mapping = mock.Mock(NumberOfEntries=fake_entry_count)
        mock_get_target_mapping.return_value = mock_mapping
        self._mock_run.side_effect = hresults

        resulted_mapping = self._fc_utils._get_target_mapping(
            mock.sentinel.hba_handle)

        expected_calls = [
            mock.call(fc_utils.hbaapi.HBA_GetFcpTargetMapping,
                      mock.sentinel.hba_handle,
                      self._ctypes.byref(mock_mapping),
                      ignored_error_codes=[fc_utils.HBA_STATUS_ERROR_MORE_DATA]
                      )] * 2
        self._mock_run.assert_has_calls(expected_calls)
        self.assertEqual(mock_mapping, resulted_mapping)
        mock_get_target_mapping.assert_has_calls([mock.call(0),
                                                  mock.call(fake_entry_count)])

    @mock.patch.object(fc_struct, 'HBA_PortAttributes')
    def test_get_adapter_port_attributes(self, mock_class_HBA_PortAttributes):
        resulted_port_attributes = self._fc_utils._get_adapter_port_attributes(
            mock.sentinel.hba_handle, mock.sentinel.port_index)

        self._mock_run.assert_called_once_with(
            fc_utils.hbaapi.HBA_GetAdapterPortAttributes,
            mock.sentinel.hba_handle,
            mock.sentinel.port_index,
            self._ctypes.byref(mock_class_HBA_PortAttributes.return_value))

        self.assertEqual(mock_class_HBA_PortAttributes.return_value,
                         resulted_port_attributes)

    @mock.patch.object(fc_struct, 'HBA_AdapterAttributes')
    def test_get_adapter_attributes(self, mock_class_HBA_AdapterAttributes):
        resulted_hba_attributes = self._fc_utils._get_adapter_attributes(
            mock.sentinel.hba_handle)

        self._mock_run.assert_called_once_with(
            fc_utils.hbaapi.HBA_GetAdapterAttributes,
            mock.sentinel.hba_handle,
            self._ctypes.byref(mock_class_HBA_AdapterAttributes.return_value))

        self.assertEqual(mock_class_HBA_AdapterAttributes.return_value,
                         resulted_hba_attributes)

    @mock.patch.object(fc_utils.FCUtils, 'get_fc_hba_count')
    def test_get_fc_hba_ports_missing_hbas(self, mock_get_fc_hba_count):
        mock_get_fc_hba_count.return_value = 0

        resulted_hba_ports = self._fc_utils.get_fc_hba_ports()

        self.assertEqual([], resulted_hba_ports)

    @mock.patch.object(fc_utils.FCUtils, '_get_fc_hba_adapter_ports')
    @mock.patch.object(fc_utils.FCUtils, '_get_adapter_name')
    @mock.patch.object(fc_utils.FCUtils, 'get_fc_hba_count')
    def test_get_fc_hba_ports(self, mock_get_fc_hba_count,
                              mock_get_adapter_name,
                              mock_get_adapter_ports):
        fake_adapter_count = 3

        mock_get_adapter_name.side_effect = [Exception,
                                             mock.sentinel.adapter_name,
                                             mock.sentinel.adapter_name]
        mock_get_fc_hba_count.return_value = fake_adapter_count
        mock_get_adapter_ports.side_effect = [Exception,
                                              [mock.sentinel.port]]

        expected_hba_ports = [mock.sentinel.port]
        resulted_hba_ports = self._fc_utils.get_fc_hba_ports()
        self.assertEqual(expected_hba_ports, resulted_hba_ports)
        self.assertEqual(expected_hba_ports, resulted_hba_ports)

        mock_get_adapter_name.assert_has_calls(
            [mock.call(index) for index in range(fake_adapter_count)])
        mock_get_adapter_ports.assert_has_calls(
            [mock.call(mock.sentinel.adapter_name)] * 2)

    @mock.patch.object(fc_utils.FCUtils, '_open_adapter_by_name')
    @mock.patch.object(fc_utils.FCUtils, '_close_adapter')
    @mock.patch.object(fc_utils.FCUtils, '_get_adapter_port_attributes')
    @mock.patch.object(fc_utils.FCUtils, '_get_adapter_attributes')
    def test_get_fc_hba_adapter_ports(self, mock_get_adapter_attributes,
                                      mock_get_adapter_port_attributes,
                                      mock_close_adapter,
                                      mock_open_adapter):
        fake_port_count = 1
        fake_port_index = 0
        # Local WWNs
        fake_node_wwn = list(range(3))
        fake_port_wwn = list(range(3))

        mock_adapter_attributes = mock.MagicMock()
        mock_adapter_attributes.NumberOfPorts = fake_port_count
        mock_port_attributes = mock.MagicMock()
        mock_port_attributes.NodeWWN.wwn = fake_node_wwn
        mock_port_attributes.PortWWN.wwn = fake_port_wwn

        mock_get_adapter_attributes.return_value = mock_adapter_attributes
        mock_get_adapter_port_attributes.return_value = mock_port_attributes

        resulted_hba_ports = self._fc_utils._get_fc_hba_adapter_ports(
            mock.sentinel.adapter_name)

        expected_hba_ports = [{
            'node_name': _utils.byte_array_to_hex_str(fake_node_wwn),
            'port_name': _utils.byte_array_to_hex_str(fake_port_wwn)
        }]
        self.assertEqual(expected_hba_ports, resulted_hba_ports)

        mock_open_adapter.assert_called_once_with(mock.sentinel.adapter_name)
        mock_close_adapter.assert_called_once_with(
            mock_open_adapter(mock.sentinel.adapter_nam))
        mock_get_adapter_attributes.assert_called_once_with(
            mock_open_adapter.return_value)
        mock_get_adapter_port_attributes.assert_called_once_with(
            mock_open_adapter.return_value, fake_port_index)

    @mock.patch.object(fc_utils.FCUtils, '_wwn_struct_from_hex_str')
    @mock.patch.object(fc_utils.FCUtils, '_open_adapter_by_wwn')
    @mock.patch.object(fc_utils.FCUtils, '_close_adapter')
    @mock.patch.object(fc_utils.FCUtils, '_get_target_mapping')
    def test_get_fc_target_mapping(self, mock_get_target_mapping,
                                   mock_close_adapter, mock_open_adapter,
                                   mock_wwn_struct_from_hex_str):
        # Remote WWNs
        fake_node_wwn = list(range(8))
        fake_port_wwn = list(range(8)[::-1])

        mock_fcp_mappings = mock.MagicMock()
        mock_entry = mock.MagicMock()
        mock_entry.FcpId.NodeWWN.wwn = fake_node_wwn
        mock_entry.FcpId.PortWWN.wwn = fake_port_wwn
        mock_fcp_mappings.Entries = [mock_entry]
        mock_get_target_mapping.return_value = mock_fcp_mappings

        resulted_mappings = self._fc_utils.get_fc_target_mappings(
            mock.sentinel.local_wwnn)

        expected_mappings = [{
            'node_name': _utils.byte_array_to_hex_str(fake_node_wwn),
            'port_name': _utils.byte_array_to_hex_str(fake_port_wwn),
            'device_name': mock_entry.ScsiId.OSDeviceName,
            'lun': mock_entry.ScsiId.ScsiOSLun,
            'fcp_lun': mock_entry.FcpId.FcpLun
        }]
        self.assertEqual(expected_mappings, resulted_mappings)

        mock_wwn_struct_from_hex_str.assert_called_once_with(
            mock.sentinel.local_wwnn)
        mock_open_adapter.assert_called_once_with(
            mock_wwn_struct_from_hex_str.return_value)

        mock_close_adapter.assert_called_once_with(
            mock_open_adapter.return_value)

    def test_refresh_hba_configuration(self):
        self._fc_utils.refresh_hba_configuration()

        expected_func = fc_utils.hbaapi.HBA_RefreshAdapterConfiguration
        expected_func.assert_called_once_with()

    def test_send_scsi_inquiry_v2(self):
        self._ctypes_mocker.stop()

        fake_port_wwn = fc_struct.HBA_WWN()
        fake_remote_port_wwn = fc_struct.HBA_WWN()
        fake_fcp_lun = 11

        fake_cdb_byte_1 = 1
        fake_cdb_byte_2 = 0x80

        fake_resp = bytearray(range(200))
        fake_sense_data = bytearray(range(200)[::-1])
        fake_scsi_status = 5

        def mock_run(func, hba_handle, port_wwn_struct,
                     remote_port_wwn_struct, fcp_lun, cdb_byte1,
                     cdb_byte2, p_resp_buff, p_resp_buff_sz,
                     p_scsi_status, p_sense_buff, p_sense_buff_sz):
            self.assertEqual(fc_utils.hbaapi.HBA_ScsiInquiryV2, func)
            self.assertEqual(mock.sentinel.hba_handle, hba_handle)
            self.assertEqual(fake_port_wwn, port_wwn_struct)
            self.assertEqual(fake_remote_port_wwn, remote_port_wwn_struct)

            self.assertEqual(fake_fcp_lun, fcp_lun.value)
            self.assertEqual(fake_cdb_byte_1, cdb_byte1.value)
            self.assertEqual(fake_cdb_byte_2, cdb_byte2.value)

            resp_buff_sz = ctypes.cast(
                p_resp_buff_sz,
                ctypes.POINTER(ctypes.c_uint32)).contents
            sense_buff_sz = ctypes.cast(
                p_sense_buff_sz,
                ctypes.POINTER(ctypes.c_uint32)).contents
            scsi_status = ctypes.cast(
                p_scsi_status,
                ctypes.POINTER(ctypes.c_ubyte)).contents

            self.assertEqual(fc_utils.SCSI_INQ_BUFF_SZ, resp_buff_sz.value)
            self.assertEqual(fc_utils.SENSE_BUFF_SZ, sense_buff_sz.value)

            resp_buff_type = (ctypes.c_ubyte * resp_buff_sz.value)
            sense_buff_type = (ctypes.c_ubyte * sense_buff_sz.value)

            resp_buff = ctypes.cast(p_resp_buff,
                                    ctypes.POINTER(resp_buff_type)).contents
            sense_buff = ctypes.cast(p_sense_buff,
                                     ctypes.POINTER(sense_buff_type)).contents

            resp_buff[:len(fake_resp)] = fake_resp
            sense_buff[:len(fake_sense_data)] = fake_sense_data

            resp_buff_sz.value = len(fake_resp)
            sense_buff_sz.value = len(fake_sense_data)
            scsi_status.value = fake_scsi_status

        self._mock_run.side_effect = mock_run

        resp_buff = self._fc_utils._send_scsi_inquiry_v2(
            mock.sentinel.hba_handle,
            fake_port_wwn,
            fake_remote_port_wwn,
            fake_fcp_lun,
            fake_cdb_byte_1,
            fake_cdb_byte_2)

        self.assertEqual(fake_resp, bytearray(resp_buff[:len(fake_resp)]))

    @mock.patch.object(fc_utils.FCUtils, '_send_scsi_inquiry_v2')
    def test_get_scsi_device_id_vpd(self, mock_send_scsi_inq):
        self._fc_utils._get_scsi_device_id_vpd(
            mock.sentinel.hba_handle, mock.sentinel.port_wwn,
            mock.sentinel.remote_port_wwn, mock.sentinel.fcp_lun)

        mock_send_scsi_inq.assert_called_once_with(
            mock.sentinel.hba_handle, mock.sentinel.port_wwn,
            mock.sentinel.remote_port_wwn, mock.sentinel.fcp_lun,
            1, 0x83)

    @mock.patch.object(fc_utils.FCUtils, '_wwn_struct_from_hex_str')
    @mock.patch.object(fc_utils.FCUtils, '_open_adapter_by_wwn')
    @mock.patch.object(fc_utils.FCUtils, '_close_adapter')
    @mock.patch.object(fc_utils.FCUtils, '_get_scsi_device_id_vpd')
    def test_get_scsi_device_identifiers(self, mock_get_scsi_dev_id_vpd,
                                         mock_close_adapter, mock_open_adapter,
                                         mock_wwn_struct_from_hex_str):

        mock_wwn_struct_from_hex_str.side_effect = (
            mock.sentinel.local_wwnn_struct, mock.sentinel.local_wwpn_struct,
            mock.sentinel.remote_wwpn_struct)
        self._diskutils._parse_scsi_page_83.return_value = (
            mock.sentinel.identifiers)

        identifiers = self._fc_utils.get_scsi_device_identifiers(
            mock.sentinel.local_wwnn, mock.sentinel.local_wwpn,
            mock.sentinel.remote_wwpn, mock.sentinel.fcp_lun,
            mock.sentinel.select_supp_ids)

        self.assertEqual(mock.sentinel.identifiers, identifiers)

        mock_wwn_struct_from_hex_str.assert_has_calls(
            [mock.call(wwn)
             for wwn in (mock.sentinel.local_wwnn, mock.sentinel.local_wwpn,
                         mock.sentinel.remote_wwpn)])

        mock_get_scsi_dev_id_vpd.assert_called_once_with(
            mock_open_adapter.return_value,
            mock.sentinel.local_wwpn_struct,
            mock.sentinel.remote_wwpn_struct,
            mock.sentinel.fcp_lun)
        self._diskutils._parse_scsi_page_83.assert_called_once_with(
            mock_get_scsi_dev_id_vpd.return_value,
            select_supported_identifiers=mock.sentinel.select_supp_ids)

        mock_open_adapter.assert_called_once_with(
            mock.sentinel.local_wwnn_struct)
        mock_close_adapter.assert_called_once_with(
            mock_open_adapter.return_value)
