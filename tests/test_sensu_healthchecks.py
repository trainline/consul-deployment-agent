# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from mock import MagicMock, Mock

from .context import agent
from agent import key_naming_convention
from agent.deployment_stages import RegisterSensuHealthChecks, DeploymentError
from agent.deployment_stages.sensu_healthchecks import create_and_copy_check, create_check_definition

healthchecks = {
    'check_failing': {
        'type': 'script'
    },
    'check_2': {
        'type': 'http'
    }
}

class MockLogger:
  def __init__(self):
    self.info = Mock()
    self.error = Mock()
    self.debug = Mock()

class MockService:
  def __init__(self):
    self.id = 'test_service'

class MockDeployment:
    def __init__(self):
        self.logger = MockLogger()
        self.archive_dir = ''
        self.service = MockService()
        self.cluster = 'default_team'
        self.sensu = {
            'sensu_check_path': 'test_sensu_check_path'
        }
        self.appspec = {
            'healthchecks': healthchecks
        }
    def set_check(self, check_id, check):
        self.appspec = {
            'sensu_healthchecks': {
                check_id: check
            }
        }
    def set_checks(self, checks):
        self.appspec = {
            'sensu_healthchecks': checks
        }


class TestHealthChecks(unittest.TestCase):
    def setUp(self):
        self.deployment = MockDeployment()
        self.tested_fn = RegisterSensuHealthChecks()
        
    def test_missing_name_field(self):
        check = {
        }
        self.deployment.set_check('check_failing', check)
        with self.assertRaisesRegexp(DeploymentError, 'is missing field'):
            self.tested_fn._run(self.deployment)

    def test_missing_interval_field(self):
        check = {
            'name': 'Missing interval'
        }
        self.deployment.set_check('check_failing', check)
        with self.assertRaisesRegexp(DeploymentError, 'is missing field \'interval\''):
            self.tested_fn._run(self.deployment)

    def test_missing_script_field(self):
        check = {
            'name': 'Missing interval',
            'interval': '10s'
        }
        self.deployment.set_check('check_failing', check)
        with self.assertRaisesRegexp(DeploymentError, 'you need at least one of'):
            self.tested_fn._run(self.deployment)

    def test_both_script_fields(self):
        check = {
            'name': 'Missing interval',
            'interval': '10s',
            'local_script': 'a',
            'server_script': 'b',
        }
        self.deployment.set_check('check_failing', check)
        with self.assertRaisesRegexp(DeploymentError, "you can use either 'local_script' or 'server_script'"):
            self.tested_fn._run(self.deployment)

    def test_case_insensitive_id_conflict(self):
        checks = {
            'check_1': {
                'name': 'Missing http 1',
                'local_script': 'a',
                'interval': '10s'
            },
            'cheCK_1': {
                'name': 'Missing http 2',
                'local_script': 'a',
                'interval': '10s'
            }
        }
        self.deployment.set_checks(checks)
        with self.assertRaisesRegexp(DeploymentError, 'health checks require unique ids'):
            self.tested_fn._run(self.deployment)

    def test_case_insensitive_name_conflict(self):
        checks = {
            'check_1': {
                'name': 'Missing http',
                'local_script': 'a',
                'interval': '10s'
            },
            'check_2': {
                'name': 'Missing http',
                'local_script': 'a',
                'interval': '10s'
            }
        }
        self.deployment.set_checks(checks)
        with self.assertRaisesRegexp(DeploymentError, 'health checks require unique names'):
            self.tested_fn._run(self.deployment)

    def test_missing_script(self):
        check = {
            'name': 'Missing http',
            'local_script': 'a',
            'interval': '10s'
        }
        checks = {
            'check_1': check
        }
        self.deployment.set_checks(checks)
        with self.assertRaisesRegexp(DeploymentError, "Couldn't find Sensu health check script"):
            self.tested_fn._run(self.deployment)

    def test_team(self):
        check = {
            'name': 'sensu check1',
            'local_script': 'foo.py',
            'interval': '10s'
        }
        checks = {
            'check_1': check
        }
        self.deployment.set_checks(checks)
        
        definition = create_check_definition(self.deployment, 'test_path', 'test_check_id', check)
        obj = definition['checks']['sensu check1']
        self.assertEqual(obj['team'], 'default_team')
        
        check['team'] = 'test_team1'
        definition = create_check_definition(self.deployment, 'test_path', 'test_check_id', check)
        obj = definition['checks']['sensu check1']
        self.assertEqual(obj['team'], 'test_team1')

    def test_defaults(self):
        check = {
            'name': 'sensu check1',
            'local_script': 'foo.py',
            'interval': '10s'
        }
        checks = {
            'check_1': check
        }
        self.deployment.set_checks(checks)
        
        definition = create_check_definition(self.deployment, 'test_path', 'test_check_id', check)
        obj = definition['checks']['sensu check1']
        self.assertEqual(obj['alert_after'], 600)
        self.assertEqual(obj['realert_every'], 30)
        self.assertEqual(obj['notification_email'], False)

