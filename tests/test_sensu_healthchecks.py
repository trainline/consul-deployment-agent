# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from jsonschema import ValidationError
from mock import Mock, patch
from agent.healthcheck_utils import HealthcheckUtils
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

    def test_validate_missing_name_property(self):
        check = {}
        with self.assertRaisesRegexp(ValidationError, "'name' is a required property"):
            RegisterSensuHealthChecks.validate_check_properties('check_id', check)

    def test_validate_missing_interval_property(self):
        check = {
            'name': 'Missing-interval'
        }
        with self.assertRaisesRegexp(ValidationError, "'interval' is a required property"):
            RegisterSensuHealthChecks.validate_check_properties('check_id', check)

    def test_validate_missing_script_property(self):
        check = {
            'name': 'Missing-interval',
            'interval': 10
        }
        with self.assertRaisesRegexp(DeploymentError, 'you need at least one of'):
            RegisterSensuHealthChecks.validate_check_properties('check_id', check)

    def test_validate_both_scripts_properties_provided(self):
        check = {
            'name': 'missing-interval',
            'interval': 10,
            'local_script': 'a',
            'server_script': 'b',
        }
        with self.assertRaisesRegexp(DeploymentError, "you can use either 'local_script' or 'server_script'"):
            RegisterSensuHealthChecks.validate_check_properties('check_id', check)

    def test_validate_name_does_not_match_regexp(self):
        check = {
            'name': 'missing http',
            'local_script': 'a',
            'interval': 10,
        }
        with self.assertRaisesRegexp(DeploymentError, 'match required Sensu name expression'):
            RegisterSensuHealthChecks.validate_check_properties('check_id', check)

    def test_validate_integer_type_properties(self):
        check = {
            'name': 'missing-http',
            'local_script': 'a',
            'team': 'some_team'
        }
        property_names = ['interval', 'realert_every', 'timeout', 'occurrences', 'refresh']
        last_property_name = None
        for property_name in property_names:
            if last_property_name is not None:
                check[property_name] = 10
            check[property_name] = '10s'
            last_property_name = property_name
            with self.assertRaisesRegexp(ValidationError, "'{0}' is not of type 'number'".format(check[property_name])):
                RegisterSensuHealthChecks.validate_check_properties('check_id', check)

    def test_validate_override_notification_email_property(self):
        check = {
            'name': 'sensu-check1',
            'local_script': 'foo.py',
            'override_notification_email': ['foo', 'bar'],
            'interval': 10
        }
        with self.assertRaisesRegexp(ValidationError, "'foo' does not match"):
            RegisterSensuHealthChecks.validate_check_properties('check_id', check)

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
                'local_script': 'script.sh',
                'interval': 10
            },
            'check_2': {
                'name': 'missing-http',
                'local_script': 'script.sh',
                'interval': 10
            }
        }
        with self.assertRaisesRegexp(DeploymentError, 'Sensu check definitions require unique names'):
            RegisterSensuHealthChecks.validate_unique_names(checks)

    def test_validate_missing_local_script(self):
        def file_exists(path):
            return False
        patcher = patch('os.path.exists')
        mock = patcher.start()
        mock.side_effect = file_exists

        check = {
            'name': 'missing-http',
            'local_script': 'script.sh',
            'interval': 10,
            'team': 'some_team'
        }
        with self.assertRaisesRegexp(DeploymentError, "Couldn't find Sensu check script"):
            RegisterSensuHealthChecks.validate_check_script(check, '/some/path', self.deployment)

    def test_validate_missing_sensu_plugin_script(self):
        def file_exists(path):
            return False
        patcher = patch('os.path.exists')
        mock = patcher.start()
        mock.side_effect = file_exists

        check = {
            'name': 'missing-http',
            'server_script': 'script.sh',
            'interval': 10,
            'team': 'some_team'
        }
        with self.assertRaisesRegexp(DeploymentError, "Couldn't find Sensu plugin script"):
            RegisterSensuHealthChecks.validate_check_script(check, None, self.deployment)

    def test_warning_deprecated_properties(self):
        check = {
            'name': 'sensu-check1',
            'local_script': 'foo.py',
            'notification_email': ['foo@bar.com', 'bar@biz.uk'],
            'interval': 10
        }
        definition = RegisterSensuHealthChecks.generate_check_definition(check, 'test_path', self.deployment)
        self.deployment.logger.warning.assert_called_with("'notification_email' property is deprecated, please use 'override_notification_email' instead")
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(definition['checks'][unique_check_name]['notification_email'], 'foo@bar.com,bar@biz.uk')

    def test_generate_check_definition_with_valid_team_property(self):
        check = {
            'name': 'sensu-check1',
            'local_script': 'foo.py',
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, 'test_path', self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['team'], 'ateam')
        check['override_notification_settings'] = 'dietcode'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, 'test_path', self.deployment)
        self.assertEqual(check_definition['checks'][unique_check_name]['team'], 'dietcode')

    def test_generate_check_definition_with_valid_list_of_emails_and_slack_channels(self):
        check = {
            'name': 'sensu-check1',
            'local_script': 'fuj.py',
            'override_notification_email': ['email1@ble.pl', 'email2@ble.pl'],
            'override_chat_channel': ['channel1', 'channel2'],
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, 'test_path', self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['notification_email'], 'email1@ble.pl,email2@ble.pl')
        self.assertEqual(check_definition['checks'][unique_check_name]['slack_channel'], 'channel1,channel2')

    def test_generate_check_definition_with_default_values(self):
        check = {
            'name': 'sensu-check1',
            'local_script': 'foo.py',
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, 'test_path', self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['aggregate'], False)
        self.assertEqual(check_definition['checks'][unique_check_name]['alert_after'], 600)
        self.assertEqual(check_definition['checks'][unique_check_name]['handlers'], ['default'])
        self.assertEqual(check_definition['checks'][unique_check_name]['notification_email'], 'undef')
        self.assertEqual(check_definition['checks'][unique_check_name]['occurrences'], 5)
        self.assertEqual(check_definition['checks'][unique_check_name]['page'], False)
        self.assertEqual(check_definition['checks'][unique_check_name]['project'], False)
        self.assertEqual(check_definition['checks'][unique_check_name]['realert_every'], 30)
        self.assertEqual(check_definition['checks'][unique_check_name]['slack_channel'], 'undef')
        self.assertEqual(check_definition['checks'][unique_check_name]['standalone'], True)
        self.assertEqual(check_definition['checks'][unique_check_name]['subscribers'], ['sensu-base'])
        self.assertEqual(check_definition['checks'][unique_check_name]['ticket'], False)
        self.assertEqual(check_definition['checks'][unique_check_name]['timeout'], 120)

    def test_generate_check_definition_with_instance_tags(self):
        check = {
            'name': 'sensu-check1',
            'local_script': 'foo.py',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, 'test_path', self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['ttl_environment'], self.deployment.instance_tags['Environment'])
        self.assertEqual(check_definition['checks'][unique_check_name]['ttl_owningcluster'], self.deployment.instance_tags['OwningCluster'])
        self.assertEqual(check_definition['checks'][unique_check_name]['ttl_role'], self.deployment.instance_tags['Role'])

    def test_generate_linux_check_definition_with_command_and_no_arguments(self):
        check = {
            'name': 'sensu-check1',
            'server_script': 'foo.sh',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['server_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'foo.sh')

    def test_generate_linux_check_definition_with_command_and_none_slice_and_no_arguments(self):
        check = {
            'name': 'sensu-check1',
            'server_script': 'foo.sh',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'none'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['server_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'foo.sh')
    
    def test_generate_linux_local_check_definition_with_command_and_slice_and_no_arguments(self):
        check = {
            'name': 'sensu-check1',
            'local_script': 'foo.sh',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'green'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['local_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'foo.sh green')
    
    def test_generate_linux_server_check_definition_with_command_and_slice_and_no_arguments(self):
        check = {
            'name': 'sensu-check1',
            'server_script': 'foo.sh',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'green'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['server_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'foo.sh')
    
    def test_generate_linux_check_definition_with_command_and_arguments(self):
        check = {
            'name': 'sensu-check1',
            'server_script': 'foo.sh',
            'script_arguments': '-o service_name',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['server_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'foo.sh -o service_name')

    def test_generate_linux_local_check_definition_with_command_and_slice_and_arguments(self):
        check = {
            'name': 'sensu-check1',
            'local_script': 'foo.sh',
            'script_arguments': '-o service_name',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'blue'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['local_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'foo.sh -o service_name blue')
    
    def test_generate_linux_server_check_definition_with_command_and_slice_and_arguments(self):
        check = {
            'name': 'sensu-check1',
            'server_script': 'foo.sh',
            'script_arguments': '-o service_name',
            'interval': 10
        }
        self.deployment.platform = 'linux'
        self.deployment.service.slice = 'blue'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['server_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'foo.sh -o service_name')
    
    def test_generate_windows_check_definition_with_command_and_no_arguments(self):
        check = {
            'name': 'sensu-check1',
            'server_script': 'foo.ps1',
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['server_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "foo.ps1"')

    def test_generate_windows_check_definition_with_command_and_none_slice_and_no_arguments(self):
        check = {
            'name': 'sensu-check1',
            'server_script': 'foo.ps1',
            'interval': 10
        }
        self.deployment.service.slice = 'none'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['server_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "foo.ps1"')
    
    def test_generate_windows_check_definition_with_command_and_arguments(self):
        check = {
            'name': 'sensu-check1',
            'server_script': 'C:\\Programs Files (x86)\\Sensu\\plugins\\check-windows-service.ps1',
            'script_arguments': '-ServiceName service_name',
            'interval': 10
        }
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['server_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "C:\\Programs Files (x86)\\Sensu\\plugins\\check-windows-service.ps1" -ServiceName service_name')

    def test_generate_local_check_definition_with_command_and_arguments_and_slice(self):
        check = {
            'name': 'sensu-check1',
            'local_script': 'C:\\Programs Files (x86)\\Sensu\\plugins\\check-windows-service.ps1',
            'script_arguments': '-ServiceName service_name',
            'interval': 10
        }
        self.deployment.service.slice = 'green'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['local_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "C:\\Programs Files (x86)\\Sensu\\plugins\\check-windows-service.ps1" -ServiceName service_name green')
    
    def test_generate_server_check_definition_with_command_and_arguments_and_slice(self):
        check = {
            'name': 'sensu-check1',
            'server_script': 'C:\\Programs Files (x86)\\Sensu\\plugins\\check-windows-service.ps1',
            'script_arguments': '-ServiceName service_name',
            'interval': 10
        }
        self.deployment.service.slice = 'green'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, check['server_script'], self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], 'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "C:\\Programs Files (x86)\\Sensu\\plugins\\check-windows-service.ps1" -ServiceName service_name')

    @patch('os.path.exists', return_value=True)
    def test_generate_windows_http_check(self, mock_patch):
        check = {
            'name': 'sensu-http-win-check',
            'type': 'http',
            'http': 'https://localhost/my/service',
            'interval': 10
        }
        self.deployment.service.slice = 'none'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, '', self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], '{0}/ttl-check-http.bat https://localhost/my/service'.format(MOCK_SENSU_PLUGINS))

    @patch('os.path.exists', return_value=True)
    def test_generate_windows_http_check_with_port(self, mock_patch):
        check = {
            'name': 'sensu-http-win-check',
            'type': 'http',
            'http': 'https://localhost:${PORT}/my/service',
            'interval': 10
        }
        self.deployment.service.slice = 'none'
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, '', self.deployment)
        unique_check_name = HealthcheckUtils.get_unique_name(check, self.deployment.service)
        self.assertEqual(check_definition['checks'][unique_check_name]['command'], '{0}/ttl-check-http.bat https://localhost:{1}/my/service'.format(MOCK_SENSU_PLUGINS, MOCK_PORT))

    @patch('os.path.exists', return_value=True)
    def test_linux_http_checks_unsupported(self, mock_patch):
        check = {
            'name': 'sensu-http-win-check',
            'type': 'http',
            'http': 'https://localhost/my/service',
            'interval': 10
        }
        self.deployment.service.slice = 'none'
        self.deployment.platform = 'linux'
        with self.assertRaises(Exception) as context:
            RegisterSensuHealthChecks.generate_check_definition(check, '', self.deployment)
        self.assertTrue('HTTP checks are not yet supported on Linux' in context.exception)

