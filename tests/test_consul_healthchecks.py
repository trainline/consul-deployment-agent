# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from mock import Mock

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
            'healthchecks': healthchecks
        }
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
        with self.assertRaisesRegexp(DeploymentError, 'is missing field \'http\''):
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



