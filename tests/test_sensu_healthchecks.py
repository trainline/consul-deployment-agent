# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See
# LICENSE.txt in the project root for license information.

import unittest
from os import path

from mock import Mock, patch
from agent.deployment_stages.healthcheck_utils import HealthcheckUtils
from agent.deployment_stages.health_check import HealthCheck
from agent.deployment_stages.common import DeploymentError
from agent.deployment_stages.sensu_healthchecks import RegisterSensuHealthChecks

MOCK_PORT = 8899
MOCK_SENSU_PLUGINS = 'sensu_plugins_path'
MOCK_SERVICE_NAME = 'mk1-mockservice'


class MockLogger(object):
    def __init__(self):
        self.info = Mock()
        self.error = Mock()
        self.debug = Mock()
        self.warning = Mock()


class MockService(object):
    slice = None

    def __init__(self):
        self.port = MOCK_PORT
        self.name = MOCK_SERVICE_NAME

    def set_slice(self, slice):
        self.slice = slice


class MockDeployment(object):
    def __init__(self):
        self.logger = MockLogger()
        self.archive_dir = ''
        self.platform = 'windows'
        self.cluster = 'ateam'
        self.instance_tags = {
            'Environment': 'local',
            'Role': 'role',
            'OwningCluster': 'cluster'
        }
        self.sensu = {
            'healthcheck_search_paths': [MOCK_SENSU_PLUGINS]
        }
        self.service = MockService()


class TestRegisterSensuHealthChecks(unittest.TestCase):
    def setUp(self):
        self.deployment = MockDeployment()

    def test_validate_all_ids_unique(self):
        checks = {
            'check_1': {
                'name': 'missing-http-1',
                'local_script': 'script.sh',
                'interval': 10
            },
            'cheCK_1': {
                'name': 'missing-http-2',
                'local_script': 'script.sh',
                'interval': 10
            }
        }
        with self.assertRaisesRegexp(DeploymentError, 'Sensu check definitions require unique ids'):
            RegisterSensuHealthChecks.validate_unique_ids(checks)

    def test_validate_all_names_unique(self):
        checks = {
            'check_1': {
                'name': 'missing-http',
                'script': 'script.sh',
                'type': 'script',
                'interval': 10
            },
            'check_2': {
                'name': 'missing-http',
                'script': 'script.sh',
                'type': 'script',
                'interval': 10
            }
        }
        with self.assertRaisesRegexp(DeploymentError, 'Sensu check definitions require unique names'):
            RegisterSensuHealthChecks.validate_unique_names(checks)

    def test_warning_deprecated_properties(self):
        check = {
            'name': 'sensu-check1',
            'script': 'foo.py',
            'type': 'script',
            'notification_email': ['foo@bar.com', 'bar@biz.uk'],
            'interval': 10
        }
        definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        self.deployment.logger.warning.assert_called_with(
            "'notification_email' property is deprecated, please use 'override_notification_email' instead")
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(definition['checks'][unique_check_name]
                         ['notification_email'], 'foo@bar.com,bar@biz.uk')

    def test_generate_check_definition_with_valid_team_property(self):
        check = {
            'name': 'sensu-check1',
            'script': 'foo.py',
            'type': 'script',
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['team'], 'ateam')
        check['override_notification_settings'] = 'dietcode'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['team'], 'dietcode')

    def test_generate_check_definition_with_valid_list_of_emails_and_slack_channels(self):
        check = {
            'name': 'sensu-check1',
            'script': 'fuj.py',
            'type': 'script',
            'override_notification_email': ['email1@ble.pl', 'email2@ble.pl'],
            'override_chat_channel': ['channel1', 'channel2'],
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]
                         ['notification_email'], 'email1@ble.pl,email2@ble.pl')
        self.assertEqual(
            check_definition['checks'][unique_check_name]['slack_channel'], 'channel1,channel2')

    def test_generate_check_definition_with_default_values(self):
        check = {
            'name': 'sensu-check1',
            'type': 'script',
            'script': 'foo.py',
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['aggregate'], False)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['alert_after'], 600)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['handlers'], ['default'])
        self.assertEqual(
            check_definition['checks'][unique_check_name]['notification_email'], 'undef')
        self.assertEqual(
            check_definition['checks'][unique_check_name]['occurrences'], 5)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['page'], False)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['project'], False)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['realert_every'], 30)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['slack_channel'], 'undefined')
        self.assertEqual(
            check_definition['checks'][unique_check_name]['standalone'], True)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['subscribers'], ['sensu-base'])
        self.assertEqual(
            check_definition['checks'][unique_check_name]['ticket'], False)
        self.assertEqual(
            check_definition['checks'][unique_check_name]['timeout'], 120)

    @patch('os.stat')
    @patch('os.chmod')
    def test_generate_check_definition_with_instance_tags(self, stat, chmod):
        check = {
            'name': 'sensu-check1',
            'script': 'foo.py',
            'type': 'script',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]
                         ['ttl_environment'], self.deployment.instance_tags['Environment'])
        self.assertEqual(check_definition['checks'][unique_check_name]
                         ['ttl_owningcluster'], self.deployment.instance_tags['OwningCluster'])
        self.assertEqual(check_definition['checks'][unique_check_name]
                         ['ttl_role'], self.deployment.instance_tags['Role'])

    @patch('os.path.exists', return_value=True)
    def test_generate_linux_check_definition_with_command_and_no_arguments(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'foo.sh',
            'type': 'plugin',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]
                         ['command'], path.join(MOCK_SENSU_PLUGINS, 'foo.sh'))

    @patch('os.path.exists', return_value=True)
    def test_generate_linux_check_definition_with_command_and_none_slice_and_no_arguments(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'foo.sh',
            'type': 'plugin',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'none'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]
                         ['command'], path.join(MOCK_SENSU_PLUGINS, 'foo.sh'))

    @patch('os.stat')
    @patch('os.chmod')
    def test_generate_linux_local_check_definition_with_command_and_slice_and_no_arguments(self, stat, chmod):
        check = {
            'name': 'sensu-check1',
            'script': 'foo.sh',
            'type': 'script',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'green'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]
                         ['command'], '{0} green'.format(path.join('healthchecks', 'sensu', 'foo.sh')))

    @patch('os.path.exists', return_value=True)
    def test_generate_linux_server_check_definition_with_command_and_slice_and_no_arguments(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'foo.sh',
            'type': 'plugin',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'green'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]
                         ['command'], path.join(MOCK_SENSU_PLUGINS, 'foo.sh'))

    @patch('os.path.exists', return_value=True)
    def test_generate_linux_check_definition_with_command_and_arguments(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'foo.sh',
            'type': 'plugin',
            'plugin_arguments': '-o service_name',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         '{0} -o service_name'.format(path.join(MOCK_SENSU_PLUGINS, 'foo.sh')))

    @patch('os.stat')
    @patch('os.chmod')
    def test_generate_linux_local_check_definition_with_command_and_slice_and_arguments(self, stat, chmod):
        check = {
            'name': 'sensu-check1',
            'script': 'foo.sh',
            'type': 'script',
            'script_arguments': '-o service_name',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'blue'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]
                         ['command'], '{0} -o service_name blue'.format(path.join('healthchecks', 'sensu', 'foo.sh')))

    @patch('os.path.exists', return_value=True)
    def test_generate_linux_server_check_definition_with_command_and_slice_and_arguments(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'foo.sh',
            'type': 'plugin',
            'plugin_arguments': '-o service_name',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'blue'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         '{0} -o service_name'.format(path.join(MOCK_SENSU_PLUGINS, 'foo.sh')))

    @patch('os.path.exists', return_value=True)
    def test_generate_windows_check_definition_with_command_and_no_arguments(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'foo.ps1',
            'type': 'plugin',
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "{0}"'.format(path.join(MOCK_SENSU_PLUGINS, 'foo.ps1')))

    @patch('os.path.exists', return_value=True)
    def test_powershell_is_given_file_rather_than_command(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'foo.ps1',
            'type': 'plugin',
            'interval': 10,
            'server_script_isfile': 'yes'
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -File "{0}"'.format(path.join(MOCK_SENSU_PLUGINS, 'foo.ps1')))

    @patch('os.path.exists', return_value=True)
    def test_generate_windows_check_definition_with_command_and_none_slice_and_no_arguments(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'foo.ps1',
            'type': 'plugin',
            'interval': 10
        }
        self.deployment.service.slice = 'none'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "{0}"'.format(path.join(MOCK_SENSU_PLUGINS, 'foo.ps1')))

    @patch('os.path.exists', return_value=True)
    def test_generate_windows_check_definition_with_command_and_arguments(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'check-windows-service.ps1',
            'type': 'plugin',
            'plugin_arguments': '-ServiceName service_name',
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "{0}" -ServiceName service_name'.format(path.join(MOCK_SENSU_PLUGINS, 'check-windows-service.ps1')))

    def test_generate_local_check_definition_with_command_and_arguments_and_slice(self):
        check = {
            'name': 'sensu-check1',
            'type': 'script',
            'script': 'check-windows-service.ps1',
            'script_arguments': '-ServiceName service_name',
            'interval': 10
        }
        self.deployment.service.slice = 'green'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "{0}" -ServiceName service_name green'.format(path.join('healthchecks', 'sensu', 'check-windows-service.ps1')))

    @patch('os.path.exists', return_value=True)
    def test_generate_server_check_definition_with_command_and_arguments_and_slice(self, mock_exists):
        check = {
            'name': 'sensu-check1',
            'plugin': 'check-windows-service.ps1',
            'type': 'plugin',
            'plugin_arguments': '-ServiceName service_name',
            'interval': 10
        }
        self.deployment.service.slice = 'green'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "{0}" -ServiceName service_name'.format(path.join(MOCK_SENSU_PLUGINS, 'check-windows-service.ps1')))

    @patch('os.path.exists', return_value=True)
    def test_generate_windows_http_check(self, mock_patch):
        check = {
            'name': 'sensu-http-win-check',
            'type': 'http',
            'url': 'https://localhost/my/service',
            'interval': 10
        }
        self.deployment.service.slice = 'none'
        self.deployment.platform = 'windows'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         '{0} https://localhost/my/service'.format(path.join(MOCK_SENSU_PLUGINS, 'ttl-check-http.bat')))

    @patch('os.path.exists', return_value=True)
    def test_generate_windows_http_check_with_port(self, mock_patch):
        check = {
            'name': 'sensu-http-win-check',
            'type': 'http',
            'url': 'https://localhost:${PORT}/my/service',
            'interval': 10
        }
        self.deployment.service.slice = 'none'
        self.deployment.platform = 'windows'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         '{0} https://localhost:{1}/my/service'.format(path.join(MOCK_SENSU_PLUGINS, 'ttl-check-http.bat'), MOCK_PORT))

    @patch('os.path.exists', return_value=True)
    def test_generate_linux_http_check(self, mock_patch):
        check = {
            'name': 'sensu-http-linux-check',
            'type': 'http',
            'url': 'https://localhost/my/service',
            'interval': 10
        }
        self.deployment.service.slice = 'none'
        self.deployment.platform = 'linux'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         '{0} -u https://localhost/my/service'.format(path.join(MOCK_SENSU_PLUGINS, 'check-http.rb')))

    @patch('os.path.exists', return_value=True)
    def test_generate_linux_http_check_with_port(self, mock_patch):
        check = {
            'name': 'sensu-http-linux-check',
            'type': 'http',
            'url': 'https://localhost:${PORT}/my/service',
            'interval': 10
        }
        self.deployment.service.slice = 'none'
        self.deployment.platform = 'linux'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(
            HealthCheck.create(check, self.deployment), self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(
            check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'],
                         '{0} -u https://localhost:{1}/my/service'.format(path.join(MOCK_SENSU_PLUGINS, 'check-http.rb'), MOCK_PORT))
