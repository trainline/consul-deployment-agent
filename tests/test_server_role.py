# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from agent.server_role import ServerRole
from agent.actions import InstallAction

class MockService(object):
    def __init__(self, id, deployment_id):
        self.id = id
        self.deployment_id = deployment_id
    def __eq__(self, other):
        return self.id == other.id and self.deployment_id == other.deployment_id

class TestServerRole(unittest.TestCase):
    def test_find_missing_action_none_missing(self):
        server_role = ServerRole('role')
        server_role.actions = [
            InstallAction('2419483e-6aef-4dd9-a46e-dc00966ba2b2', MockService('Service1', '2419483e-6aef-4dd9-a46e-dc00966ba2b2'))
        ]
        registered_services = [MockService('Service1', '2419483e-6aef-4dd9-a46e-dc00966ba2b2')]
        self.assertEqual(server_role.find_action_to_execute(registered_services), None)

    def test_find_missing_action_one_missing(self):
        server_role = ServerRole('role')
        server_role.actions = [
            InstallAction('2419483e-6aef-4dd9-a46e-dc00966ba2b2', MockService('Service1', '2419483e-6aef-4dd9-a46e-dc00966ba2b2'))
        ]
        missing_action_report = server_role.find_action_to_execute([])
        missing_action = missing_action_report[0]
        deployment_info = missing_action_report[1]
        self.assertNotEqual(missing_action, None)
        self.assertEqual(missing_action.service.id, 'Service1')
        self.assertEqual(missing_action.deployment_id, '2419483e-6aef-4dd9-a46e-dc00966ba2b2')
        print deployment_info
        self.assertEqual(deployment_info['last_deployment_id'], None)

    def test_find_missing_action_one_outdated(self):
        server_role = ServerRole('role')
        server_role.actions = [
            InstallAction('2419483e-6aef-4dd9-a46e-dc00966ba2b2', MockService('Service1', '2419483e-6aef-4dd9-a46e-dc00966ba2b2'))
        ]
        registered_services = [MockService('Service1', 'dfc6b093-c102-408c-bd3b-7bc2e2c68d29')]
        missing_action_report = server_role.find_action_to_execute(registered_services)
        missing_service = missing_action_report[0]
        deployment_info = missing_action_report[1]
        self.assertNotEqual(missing_service, None)
        self.assertEqual(missing_service.service.id, 'Service1')
        self.assertEqual(missing_service.deployment_id, '2419483e-6aef-4dd9-a46e-dc00966ba2b2')
        self.assertEqual(deployment_info['last_deployment_id'], 'dfc6b093-c102-408c-bd3b-7bc2e2c68d29')

    def test_find_missing_action_one_missing_but_quarantined(self):
        server_role = ServerRole('role')
        server_role.actions = [
            InstallAction('2419483e-6aef-4dd9-a46e-dc00966ba2b2', MockService('Service1', '2419483e-6aef-4dd9-a46e-dc00966ba2b2'))
        ]
        server_role.quarantine = ['2419483e-6aef-4dd9-a46e-dc00966ba2b2']
        self.assertEqual(server_role.find_action_to_execute([]), None)
