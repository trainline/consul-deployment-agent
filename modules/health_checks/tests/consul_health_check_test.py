# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See
# LICENSE.txt in the project root for license information.

import unittest

from mock import Mock, MagicMock, patch
from modules.health_checks.lib.health_checks.health_check_errors import RegisterError
from modules.health_checks.lib.health_checks.consul_health_check import ConsulHealthCheck


HEALTHCHECKS = {
    'check_failing': {
        'type': 'script'
    },
    'check_2': {
        'type': 'http'
    }
}


def set_slice(sut, slice):
    sut.service_slice = slice


class MockLogger(object):
    def __init__(self):
        self.info = Mock()
        self.error = Mock()
        self.debug = Mock()


class MockDeployment(object):
    def __init__(self):
        self.logger = MockLogger()
        self.archive_dir = ''
        self.appspec = {
            'healthchecks': HEALTHCHECKS
        }
        self.service = {
            id: 'my-mock-service'
        }


def set_checks(sut, checks):
    sut.appspec = {
        'consul_healthchecks': checks
    }


def set_check(sut, check_id, check):
    sut.appspec = {
        'consul_healthchecks': {
            check_id: check
        }
    }


class TestHealthChecks(unittest.TestCase):
    def setUp(self):
        self.deployment = MockDeployment()
        self.logger = MockLogger()
        self.archive_dir = ''
        self.appspec = {
            'healthchecks': HEALTHCHECKS
        }
        self.service_id = 'my-mock-service'
        self.tested_fn = ConsulHealthCheck(
            name="ConsulHealthCheck",
            logger=self.logger,
            archive_dir=self.archive_dir,
            appspec=self.appspec,
            service_id=self.service_id,
            api=MagicMock()
        )

    def test_failing_check(self):
        check = {
            'type': 'unknown',
            'name': 'check_name'
        }
        set_check(self.tested_fn, 'check_failing', check)
        with self.assertRaisesRegexp(RegisterError, 'only.*check types are supported'):
            self.tested_fn.register()

    def test_missing_name_field(self):
        check = {
            'type': 'http',
            'name': 'check_name'
        }
        set_check(self.tested_fn, 'check_failing', check)
        with self.assertRaisesRegexp(RegisterError, 'is missing field'):
            self.tested_fn.register()

    def test_missing_http_field(self):
        check = {
            'type': 'http',
            'name': 'Missing http'
        }
        set_check(self.tested_fn, 'check_failing', check)
        with self.assertRaisesRegexp(RegisterError, 'is missing field \'http\''):
            self.tested_fn.register()

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
        set_checks(self.tested_fn, checks)
        with self.assertRaisesRegexp(RegisterError, 'health checks require unique ids'):
            self.tested_fn.register()

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
        set_checks(self.tested_fn, checks)
        with self.assertRaisesRegexp(RegisterError, 'health checks require unique names'):
            self.tested_fn.register()

    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_script_check_registration(self, stat, chmod, exists):
        checks = {
            'test_check': self.create_check(True, 'test-script', 'test-script.py', '10')
        }
        set_checks(self.tested_fn, checks)
        self.api = MagicMock()

        with patch.object(ConsulHealthCheck, 'find_health_checks') as mock_health_check:
            mock_health_check.return_value = (checks, '')
            self.tested_fn.register()
            self.tested_fn.api.register_script_check.assert_called_once_with(
                'my-mock-service', 'my-mock-service:test_check', 'test-script', 'test-script.py', '10')

    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_script_check_registration_with_slice(self, stat, chmod, exists):
        checks = {
            'test_check': self.create_check(True, 'test-script', 'test-script.py', '10')
        }
        set_checks(self.tested_fn, checks)
        set_slice(self.tested_fn, 'blue')
        self.tested_fn.api = MagicMock()

        with patch.object(ConsulHealthCheck, 'find_health_checks') as mock_health_check:
            mock_health_check.return_value = (checks, '')
            self.tested_fn.register()
            self.tested_fn.api.register_script_check.assert_called_once_with(
                'my-mock-service', 'my-mock-service:test_check', 'test-script', 'test-script.py blue', '10')

    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_script_http_registration(self, stat, chmod, exists):
        checks = {
            'test_http_check': self.create_check(False, 'test-http', 'http://acme.com/healthcheck', '20')
        }
        set_checks(self.tested_fn, checks)

        with patch.object(ConsulHealthCheck, 'find_health_checks') as mock_health_check:
            mock_health_check.return_value = (checks, '')
            self.tested_fn.register()
            self.tested_fn.api.register_http_check.assert_called_once_with(
                'my-mock-service', 'my-mock-service:test_http_check', 'test-http', 'http://acme.com/healthcheck', '20')

    @patch('os.stat')
    @patch('os.chmod')
    @patch('os.path.exists', return_value=True)
    def test_http_check_registration_with_slice(self, stat, chmod, exists):
        checks = {
            'test_http_check': self.create_check(False, 'test-http', 'http://acme.com/healthcheck', '20')
        }
        set_checks(self.tested_fn, checks)
        set_slice(self.tested_fn, 'blue')

        # Slice value should not affect http value
        with patch.object(ConsulHealthCheck, 'find_health_checks') as mock_health_check:
            mock_health_check.return_value = (checks, '')
            self.tested_fn.register()
            self.tested_fn.api.register_http_check.assert_called_once_with(
                'my-mock-service', 'my-mock-service:test_http_check', 'test-http', 'http://acme.com/healthcheck', '20')

    def create_check(self, is_script, name, value, interval):
        check = {'name': name, 'interval': interval}
        if is_script:
            check['type'] = 'script'
            check['script'] = value
        else:
            check['type'] = 'http'
            check['http'] = value
        return check
