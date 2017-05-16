# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest

from mock import Mock, MagicMock, patch
from agent.deployment_stages.common import DeploymentError
from agent.deployment_stages.consul_healthchecks import RegisterConsulHealthChecks

healthchecks = {
    'check_failing': {
        'type': 'script'
    },
    'check_2': {
        'type': 'http'
    }
}

MOCK_PORT = 4455

class MockService(object):
    slice = None

    def __init__(self):
        self.id = 'my-mock-service'
        self.port = MOCK_PORT

    def set_slice(self, slice):
        self.slice = slice

class MockLogger(object):
    def __init__(self):
        self.info = Mock()
        self.error = Mock()
        self.debug = Mock()

class MockDeployment(object):
    def __init__(self):
        self.logger = MockLogger()
        self.archive_dir = ''
        self.platform = 'linux'
        self.appspec = {
            'healthchecks': healthchecks
        }
        self.service = MockService()

    def set_check(self, check_id, check):
        self.appspec = {
            'consul_healthchecks': {
                check_id: check
            }
        }

    def set_checks(self, checks):
        self.appspec = {
            'consul_healthchecks': checks
        }

    def set_platform(self, platform):
        self.platform = platform


class TestHealthChecks(unittest.TestCase):
    def setUp(self):
        self.deployment = MockDeployment()
        self.tested_fn = RegisterConsulHealthChecks()

    def test_failing_check(self):
        check = {
            'type': 'unknown',
            'name': 'check_name'
        }
        self.deployment.set_check('check_failing', check)
        with self.assertRaisesRegexp(DeploymentError, 'only.*check types are supported'):
            self.tested_fn._run(self.deployment)

    def test_missing_name_field(self):
        check = {
            'type': 'http',
            'name': 'check_name'
        }
        self.deployment.set_check('check_failing', check)
        with self.assertRaisesRegexp(DeploymentError, 'is missing field'):
            self.tested_fn._run(self.deployment)

    def test_missing_http_field(self):
        check = {
            'type': 'http',
            'name': 'Missing http'
        }
        self.deployment.set_check('check_failing', check)
        with self.assertRaisesRegexp(DeploymentError, 'is missing field \'url\''):
            self.tested_fn._run(self.deployment)

    def test_case_insensitive_id_conflict(self):
        checks = {
            'check_1': {
                'type': 'http',
                'name': 'Missing http 1'

            },
            'cheCK_1': {
                'type': 'http',
                'name': 'Missing http 2'
            }
        }
        self.deployment.set_checks(checks)
        with self.assertRaisesRegexp(DeploymentError, 'health checks require unique ids'):
            self.tested_fn._run(self.deployment)

    def test_case_insensitive_name_conflict(self):
        checks = {
            'check_1': {
                'type': 'http',
                'name': 'Missing http'

            },
            'check_2': {
                'type': 'http',
                'name': 'Missing http'
            }
        }
        self.deployment.set_checks(checks)
        with self.assertRaisesRegexp(DeploymentError, 'health checks require unique names'):
            self.tested_fn._run(self.deployment)

    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_script_check_registration(self, stat, chmod, exists):
        checks = {
            'test_check': self.create_check(True, 'test-script', 'test-script.py', '10')
        }
        self.deployment.set_checks(checks)
        self.deployment.consul_api = MagicMock()

        with patch('agent.deployment_stages.consul_healthchecks.find_healthchecks', return_value=(checks, '')):
            self.tested_fn._run(self.deployment)
            self.deployment.consul_api.register_script_check.assert_called_once_with('my-mock-service', 'my-mock-service:test_check', 'test-script', 'test-script.py', '10')

    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_script_check_registration_with_slice(self, stat, chmod, exists):
        checks = {
            'test_check': self.create_check(True, 'test-script', 'test-script.py', '10')
        }
        self.deployment.set_checks(checks)
        self.deployment.service.set_slice('blue')
        self.deployment.consul_api = MagicMock()

        with patch('agent.deployment_stages.consul_healthchecks.find_healthchecks', return_value=(checks, '')):
            self.tested_fn._run(self.deployment)
            self.deployment.consul_api.register_script_check.assert_called_once_with('my-mock-service', 'my-mock-service:test_check', 'test-script', 'test-script.py blue', '10')

    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_windows_script_check_registration(self, stat, chmod, exists):
        checks = {
            'test_check': self.create_check(True, 'test-script', 'test-script.ps1', '10')
        }
        self.deployment.set_checks(checks)
        self.deployment.consul_api = MagicMock()
        self.deployment.set_platform('windows')

        with patch('agent.deployment_stages.consul_healthchecks.find_healthchecks', return_value=(checks, '')):
                self.tested_fn._run(self.deployment)
                self.deployment.consul_api.register_script_check.assert_called_once_with('my-mock-service', 'my-mock-service:test_check', 'test-script', 'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "test-script.ps1"', '10')

    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_windows_script_check_registration_with_slice(self, stat, chmod, exists):
        checks = {
            'test_check': self.create_check(True, 'test-script', 'test-script.ps1', '10')
        }
        self.deployment.set_checks(checks)
        self.deployment.service.set_slice('blue')
        self.deployment.consul_api = MagicMock()
        self.deployment.set_platform('windows')

        with patch('agent.deployment_stages.consul_healthchecks.find_healthchecks', return_value=(checks, '')):
            self.tested_fn._run(self.deployment)
            self.deployment.consul_api.register_script_check.assert_called_once_with('my-mock-service', 'my-mock-service:test_check', 'test-script', 'powershell.exe -NonInteractive -NoProfile -ExecutionPolicy RemoteSigned -Command "test-script.ps1" blue', '10')

    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_script_http_registration(self, stat, chmod, exists):
        checks = {
            'test_http_check': self.create_check(False, 'test-http', 'http://acme.com/healthcheck', '20')
        }
        self.deployment.set_checks(checks)
        self.deployment.consul_api = MagicMock()

        with patch('agent.deployment_stages.consul_healthchecks.find_healthchecks', return_value=(checks, '')):
            self.tested_fn._run(self.deployment)
            self.deployment.consul_api.register_http_check.assert_called_once_with('my-mock-service', 'my-mock-service:test_http_check', 'test-http', 'http://acme.com/healthcheck', '20')
    
    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_script_http_registration_with_port(self, stat, chmod, exists):
        checks = {
                'test_http_check': self.create_check(False, 'test-http', 'http://localhost:${PORT}/service/api', '20')
        }
        self.deployment.set_checks(checks)
        self.deployment.consul_api = MagicMock()

        with patch('agent.deployment_stages.consul_healthchecks.find_healthchecks', return_value=(checks, '')):
            self.tested_fn._run(self.deployment)
            expected_url = 'http://localhost:{0}/service/api'.format(MOCK_PORT)
            self.deployment.consul_api.register_http_check.assert_called_once_with('my-mock-service', 'my-mock-service:test_http_check', 'test-http', expected_url, '20')
    
    @patch('os.stat')   
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_http_check_registration_with_slice(self, stat, chmod, exists):
        checks = {
            'test_http_check': self.create_check(False, 'test-http', 'http://acme.com/healthcheck', '20')
        }
        self.deployment.set_checks(checks)
        self.deployment.service.set_slice('blue')
        self.deployment.consul_api = MagicMock()

        # Slice value should not affect http value
        with patch('agent.deployment_stages.consul_healthchecks.find_healthchecks', return_value=(checks, '')):
            self.tested_fn._run(self.deployment)
            self.deployment.consul_api.register_http_check.assert_called_once_with('my-mock-service', 'my-mock-service:test_http_check', 'test-http', 'http://acme.com/healthcheck', '20')
    
    def create_check(self, is_script, name, value, interval):
        check = { 'name':name, 'interval':interval }
        if is_script:
            check['type'] = 'script'
            check['script'] = value
        else:
            check['type'] = 'http'
            check['url'] = value
        return check
