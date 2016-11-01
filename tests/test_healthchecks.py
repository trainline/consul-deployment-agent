# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from mock import MagicMock, Mock

from .context import agent
from agent import key_naming_convention
from agent.deployment_stages import RegisterHealthChecks

class MockDeployment:
    def __init__(self):
        self.logger = {}
        self.logger.info = Mock()

class TestKeyNamingConvention(unittest.TestCase):
    def setUp(self):
        self.deployment = MockDeployment()
        self.tested_fn = RegisterHealthChecks()
    def test_health_checks(self):
        self.tested_fn._run(self.deployment)
        # self.assertEqual(key_naming_convention.get_deployment_key('deployment_id'), 'deployments/deployment_id')
