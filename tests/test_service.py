# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import os
import unittest
from .context import agent
from agent.service import Service

class TestService(unittest.TestCase):
    def setUp(self):
        self.service_definition = {
            'Address':'127.0.0.1',
            'ID':'Service-blue',
            'Name':'Service',
            'Port':12345,
            'Tags':['version:1.0.0', 'deployment_id:12345', 'slice:blue']
        }

    def test_service_instantiation_from_catalog(self):
        service = Service(self.service_definition)
        self.assertEqual(service.address, '127.0.0.1')
        self.assertEqual(service.deployment_id, '12345')
        self.assertEqual(service.id, 'Service-blue')
        self.assertEqual(service.installation.get('timeout'), 3600)
        self.assertEqual(service.installation.get('package_bucket'), None)
        self.assertEqual(service.installation.get('package_key'), None)
        self.assertEqual(service.name, 'Service-blue')
        self.assertEqual(service.port, 12345)
        self.assertEqual(service.slice, 'blue')
        self.assertEqual(service.version, '1.0.0')

    def test_service_instantiation_from_server_role(self):
        definition = {
            'Address':'127.0.0.1',
            'ID':'Service-blue',
            'Name':'Service',
            'Port':12345,
            'Tags':['version:1.0.0']
        }
        installation_info = {
            'InstallationTimeout':60,
            'PackageBucket':'some-bucket',
            'PackageKey':'some-key'
        }
        service = Service(definition, installation_info)
        self.assertEqual(service.address, '127.0.0.1')
        self.assertEqual(service.deployment_id, None)
        self.assertEqual(service.id, 'Service-blue')
        self.assertEqual(service.installation.get('timeout'), 3600)
        self.assertEqual(service.installation.get('package_bucket'), 'some-bucket')
        self.assertEqual(service.installation.get('package_key'), 'some-key')
        self.assertEqual(service.name, 'Service-blue')
        self.assertEqual(service.port, 12345)
        self.assertEqual(service.slice, None)
        self.assertEqual(service.version, '1.0.0')

    def test_service_instantiation_failure(self):
        definition = {
            'Address':None,
            'ID':None,
            'Name':None,
            'Tags':[]
        }
        with self.assertRaises(ValueError) as cm:
            Service(definition)
        error = cm.exception
        self.assertEqual(str(error), 'Service address must be specified.')
        definition['Address'] = '127.0.0.1'

        with self.assertRaises(ValueError) as cm:
            Service(definition)
        error = cm.exception
        self.assertEqual(str(error), 'Service ID must be specified.')

    def test_extract_tag_with_prefix_found(self):
        service = Service(self.service_definition)
        self.assertEqual(service._extract_tag_with_prefix('version:'), '1.0.0')

    def test_extract_tag_with_prefix_not_found(self):
        service = Service(self.service_definition)
        self.assertEqual(service._extract_tag_with_prefix('deployment_id:'), '12345')

    def test_new_tag(self):
        service = Service(self.service_definition)
        service.tag('prefix:', 'value')
        self.assertTrue('prefix:value' in service.tags)

    def test_overwrite_tag(self):
        service = Service(self.service_definition)
        service.tag('prefix:', 'value1')
        service.tag('prefix:', 'value2')
        self.assertEqual(1, len([tag for tag in service.tags if tag.startswith('prefix:')]))
