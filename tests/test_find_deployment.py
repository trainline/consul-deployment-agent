# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

from os.path import join
import unittest
from mock import patch
from agent.find_deployment import find_deployment_dir_win

class Fake(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class TestFindDeployment(unittest.TestCase):
    def test_find_deployment_dir_win_finds_none_returns_none(self):
        with patch('agent.find_deployment.exists', return_value=False):
            expected = None
            actual = find_deployment_dir_win('/deployments', 'my_service', 'my_deployment_id')
            self.assertEqual(actual, expected)

    def test_find_deployment_dir_win_finds_both_returns_new(self):
        with patch('agent.find_deployment.exists', return_value=True):
            expected = join('/deployments', 'my_service', 'my_deployment_id')
            actual = find_deployment_dir_win('/deployments', 'my_service', 'my_deployment_id')
            self.assertEqual(actual, expected)

    def test_find_deployment_dir_win_finds_old_returns_old(self):
        expected = join('/deployments', 'my_deployment_id')
        with patch('agent.find_deployment.exists', lambda x: x == expected):
            actual = find_deployment_dir_win('/deployments', 'my_service', 'my_deployment_id')
            self.assertEqual(actual, expected)