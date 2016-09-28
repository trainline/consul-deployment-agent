# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from .context import agent
from agent import key_naming_convention
from agent.environment import Environment

class MockEnvironment:
    def __init__(self, environment_name, server_role = None, instance_id = None):
        self.environment_name = environment_name
        self.instance_id = instance_id
        self.server_role = server_role

class TestKeyNamingConvention(unittest.TestCase):
    def test_deployment_key(self):
        self.assertEqual(key_naming_convention.get_deployment_key('deployment_id'), 'deployments/deployment_id')

    def test_deployment_key_throws_exception(self):
        with self.assertRaises(ValueError) as cm:
            key_naming_convention.get_deployment_key(None)
        error = cm.exception
        self.assertEqual(str(error), 'deployment_id must be specified.')

    def test_instance_deployment_key(self):
        self.assertEqual(key_naming_convention.get_instance_deployment_key(MockEnvironment('env', 'role', 'some-instance-id'), 'deployment_id'), 'deployments/deployment_id/nodes/some-instance-id')

    def test_server_role_key(self):
        self.assertEqual(key_naming_convention.get_server_role_key(MockEnvironment('env', 'role')), 'environments/env/roles/role')

    def test_server_role_key_throws_exception(self):
        with self.assertRaises(ValueError) as cm:
            key_naming_convention.get_server_role_key(None)
        error = cm.exception
        self.assertEqual(str(error), 'environment must be specified.')

    def test_server_role_config_key(self):
        self.assertEqual(key_naming_convention.get_server_role_config_key(MockEnvironment('env', 'role')), 'environments/env/roles/role/configuration')

    def test_server_role_config_key(self):
        self.assertEqual(key_naming_convention.get_server_role_services_key(MockEnvironment('env', 'role')), 'environments/env/roles/role/services')

    def test_service_key(self):
        self.assertEqual(key_naming_convention.get_service_key(MockEnvironment('env'), 'name', 'version'), 'environments/env/services/name/version')

    def test_service_key_throws_exception(self):
        with self.assertRaises(ValueError) as cm:
            key_naming_convention.get_service_key(None, 'name', 'version')
        error = cm.exception
        self.assertEqual(str(error), 'environment must be specified.')

        with self.assertRaises(ValueError) as cm:
            key_naming_convention.get_service_key(MockEnvironment('env'), None, 'version')
        error = cm.exception
        self.assertEqual(str(error), 'name must be specified.')

        with self.assertRaises(ValueError) as cm:
            key_naming_convention.get_service_key(MockEnvironment('env'), 'name', None)
        error = cm.exception
        self.assertEqual(str(error), 'version must be specified.')

    def test_service_definition_key(self):
        self.assertEqual(key_naming_convention.get_service_definition_key(MockEnvironment('env'), 'name', 'version'), 'environments/env/services/name/version/definition')

    def test_service_installation_key(self):
        self.assertEqual(key_naming_convention.get_service_installation_key(MockEnvironment('env'), 'name', 'version'), 'environments/env/services/name/version/installation')
