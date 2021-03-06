# aws-pcf-quickstart
#
# Copyright (c) 2017-Present Pivotal Software, Inc. All Rights Reserved.
#
# This program and the accompanying materials are made available under
# the terms of the under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from mock import Mock, patch, mock_open
from os.path import expanduser

import configure_opsman_director
from settings import Settings


class TestConfigureOpsManDirector(unittest.TestCase):
    def setUp(self):
        self.settings = Mock(Settings)
        self.settings.zones = ["zone1"]
        self.settings.pcf_iam_access_key_id = "access_id"
        self.settings.pcf_iam_secret_access_key = "secret_key"
        self.settings.vpc_id = "vpc-123"
        self.settings.stack_name = "my-pcf-stack"
        self.settings.security_group = "sec-123"
        self.settings.key_pair_name = "mytestkeypair"
        self.settings.region = "region-123"
        self.settings.opsman_url = "https://example123.com"
        self.settings.pcf_input_opsmanageradminpassword = "monkey123"
        self.settings.opsman_user = "testuser"

    @patch('configure_opsman_director.generate_ssh_keypair')
    def test_flow(self, mock_generate_ssh_keypair):
        mock_generate_ssh_keypair.return_value = 'my-pcf-keypair', '------blah----'
        with patch('util.run_command') as mock_run_command:
            mock_run_command.side_effect = [("", "", 1)]
            result = configure_opsman_director.configure_opsman_director(
                self.settings)

            self.assertEqual(result[2], 1)
            self.assertEqual(mock_run_command.call_count, 1)

    @patch('configure_opsman_director.generate_ssh_keypair')
    def test_fully_configures(self, mock_generate_ssh_keypair):
        mock_generate_ssh_keypair.return_value = 'my-pcf-keypair', '------blah----'
        with patch('om_manager.get_om_with_auth') as mock_util_get_om_with_auth:
            mock_util_get_om_with_auth.return_value = ["foo"]
            with patch('util.run_command') as mock_call:
                mock_call.return_value = ("", "", 0)
                result = configure_opsman_director.configure_opsman_director(
                    self.settings)

                self.assertEqual(mock_call.call_count, 1)
                self.assertEqual(result[2], 0)

    @patch('os.chmod')
    @patch('boto3.client')
    def test_generate_ssh_keypair(self, mock_client_constructor, mock_chmod):
        self.settings.get_pcf_keypair_name.return_value = 'my-pcf-stack-pcf-keypair'
        mock_client = Mock()
        mock_client.create_key_pair.return_value = {
            'KeyMaterial': "------blah----"
        }
        mock_client_constructor.return_value = mock_client

        expected_key_name = "my-pcf-stack-pcf-keypair"

        my_mock_open = mock_open()
        with patch('configure_opsman_director.open', my_mock_open):
            keyname, keybytes = configure_opsman_director.generate_ssh_keypair(
                self.settings)

        mock_client.create_key_pair.assert_called_with(
            DryRun=False, KeyName=expected_key_name)
        my_mock_open.assert_called()

        handle = my_mock_open()
        handle.write.assert_called_once_with("------blah----")

        home = expanduser("~/.ssh")
        expected_keypath = "{}/my-pcf-stack-pcf-keypair.pem".format(home)

        self.assertEqual(keybytes, "------blah----")
        mock_chmod.assert_called_with(expected_keypath, 0o400)
