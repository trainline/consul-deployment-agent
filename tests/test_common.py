# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from os import path

import yaml
from mock import patch, call, MagicMock
from agent.deployment_stages.common import find_healthchecks

class TestCommonDeploymentStageUtils(unittest.TestCase):

    @patch('os.path.exists', return_value=True)
    @patch('agent.deployment_stages.common.open', return_value=True)
    @patch('yaml.safe_load', side_effect=yaml.scanner.ScannerError)
    def test_find_healtchecks_safely_handles_invalid_yaml(self, exists, mock_open, mock_safe_load):
        logger = MagicMock()
        (healthchecks, script_dir) = find_healthchecks('sensu', '', {}, logger)
        self.assertEqual(logger.error.mock_calls[0], call('{0} contains invalid YAML'.format(path.join('healthchecks', 'sensu', 'healthchecks.yml'))))
        self.assertEqual(healthchecks, None)

