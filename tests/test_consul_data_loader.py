# Copyright (c) Trainline Limited 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import os
import unittest
from .context import agent
from agent import key_naming_convention
from agent.consul_data_loader import ConsulDataLoader
from agent.environment import Environment

class MockConsulSession:
    def __init__(self, environment):
        self.server_role_services_key = key_naming_convention.get_server_role_services_key(environment)
        # Correctly defined service
        self.correctly_defined_service_key = '{0}/Service1'.format(self.server_role_services_key)
        self.correctly_defined_service_definition_key = key_naming_convention.get_service_definition_key(environment, 'Service1', '1.0.0')
        self.correctly_defined_service_installation_key = key_naming_convention.get_service_installation_key(environment, 'Service1', '1.0.0')
        # Incorrectly defined service
        self.incorrectly_defined_service_key = '{0}/Service2'.format(self.server_role_services_key)
        self.incorrectly_defined_service_definition_key = key_naming_convention.get_service_definition_key(environment, 'Service2', '1.0.0')
        self.incorrectly_defined_service_installation_key = key_naming_convention.get_service_installation_key(environment, 'Service2', '1.0.0')
        # Consul KV store
        self.kv = {
            self.correctly_defined_service_key:{ 'Name':'Service1', 'Version':'1.0.0', 'Slice':'blue', 'DeploymentId':'2419483e-6aef-4dd9-a46e-dc00966ba2b2' },
            self.correctly_defined_service_definition_key:{ 'Service':{'Name':'Service1', 'ID':'Service1', 'Address':'', 'Port':20200, 'Tags':['version:1.0.0']} },
            self.correctly_defined_service_installation_key:{ 'PackagePath':'http://some-location/2419483e-6aef-4dd9-a46e-dc00966ba2b2', 'InstallationTimeout':15 },
            self.incorrectly_defined_service_key:{ 'Name':'Service2', 'Version':'1.0.0', 'Slice':'none', 'DeploymentId':'8269ec14-1063-4e27-9e29-38e7454cdd98' },
            self.incorrectly_defined_service_definition_key:{ 'Service':{'Name':'Service2', 'Address':'', 'Port':20202, 'Tags':['version:1.0.0']} },
            self.incorrectly_defined_service_installation_key:{ 'PackagePath':'http://some-location/8269ec14-1063-4e27-9e29-38e7454cdd98', 'InstallationTimeout':15 },
        }

    def find_keys(self, services_key):
        if services_key == self.server_role_services_key:
            return [self.correctly_defined_service_key, self.incorrectly_defined_service_key]
        return []

    def get_json_value(self, key):
        print('requested key: %s' % key)
        print('value: %s' % self.kv.get(key))
        return self.kv.get(key)

    def registered_services(self):
        return {
            'consul':{'Service':'consul', 'ID':'consul', 'Address':'', 'Port':8300, 'Tags':[]},
            'Service1':{'Service':'Service1', 'ID':'Service1', 'Address':'127.0.0.1', 'Port':20200, 'Tags':['version:1.0.0', 'slice:none', 'deployment_id:2419483e-6aef-4dd9-a46e-dc00966ba2b2'] }
        }

class MockEnvironment:
    def __init__(self, environment_name, server_role = None, instance_id = None):
        self.environment_name = environment_name
        self.instance_id = instance_id
        self.ip_address = '127.0.0.1'
        self.server_role = server_role

class TestConsulDataLoader(unittest.TestCase):
    def test_load_server_role(self):
        environment = MockEnvironment('env', 'role')
        consul_data_loader = ConsulDataLoader(MockConsulSession(environment))
        server_role = consul_data_loader.load_server_role(environment)
        self.assertEqual(server_role.id, 'role')
        self.assertEqual(len(server_role.services), 1)
        self.assertEqual(server_role.services['2419483e-6aef-4dd9-a46e-dc00966ba2b2'].id, 'Service1')
        self.assertEqual(server_role.services['2419483e-6aef-4dd9-a46e-dc00966ba2b2'].slice, 'blue')

    def test_load_service_catalog(self):
        consul_data_loader = ConsulDataLoader(MockConsulSession(MockEnvironment('env', 'role',)))
        services = consul_data_loader.load_service_catalog()
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0].id, 'Service1')
