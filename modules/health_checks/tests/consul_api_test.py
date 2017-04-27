import base64
import json
import responses
import unittest
from modules.health_checks.lib.api.consul.consul_api import ConsulApi, ConsulError
from mock import patch

consul_config = {'scheme': 'http', 'host': 'localhost',
                 'port': 8500, 'version': 'v1', 'acl_token': None}


class TestConsulApi(unittest.TestCase):
    @responses.activate
    def test_check_connectivity_succeeds(self):
        responses.add(responses.GET, 'http://localhost:8500/v1/agent/self',
                      json={'some': 'content'}, status=200)
        consul_api = ConsulApi(consul_config)
        consul_api.check_connectivity()

    @patch('modules.health_checks.lib.api.consul.consul_api.ConsulApi._api_get')
    def test_check_connectivity_fails(self, mock_call):
        mock_call.side_effect = ConsulError('Some error message')
        consul_api = ConsulApi(consul_config)
        with self.assertRaises(ConsulError) as cm:
            consul_api.check_connectivity()
        error = cm.exception
        self.assertEqual(str(error), 'Some error message')

    @responses.activate
    def test_get_keys_for_existing_key_prefix(self):
        key_prefix = 'keyprefix'
        keys = ['key1', 'key2/key3']
        responses.add(
            responses.GET, 'http://localhost:8500/v1/kv/{0}'.format(key_prefix), json=keys, status=200)
        consul_api = ConsulApi(consul_config)
        actual_keys = consul_api.get_keys(key_prefix)
        self.assertEqual(len(actual_keys), len(keys))
        self.assertEqual(actual_keys, keys)

    @responses.activate
    def test_get_keys_for_unknown_key_prefix(self):
        key_prefix = 'keyprefix'
        responses.add(
            responses.GET, 'http://localhost:8500/v1/kv/{0}'.format(key_prefix), status=404)
        consul_api = ConsulApi(consul_config)
        actual_keys = consul_api.get_keys(key_prefix)
        self.assertEqual(actual_keys, [])

    @responses.activate
    def test_get_value_for_existing_key(self):
        key = 'key'
        decoded_value = {'property': 'some_value'}
        value = [{'Key': key, 'Value': base64.b64encode(json.dumps(
            decoded_value)), 'LockIndex': 0, 'CreateIndex': 100, 'ModifyIndex': 100, 'Flags': 0}]
        responses.add(
            responses.GET, 'http://localhost:8500/v1/kv/{0}'.format(key), json=value, status=200)
        consul_api = ConsulApi(consul_config)
        actual_value = consul_api.get_value(key)
        self.assertEqual(actual_value, decoded_value)

    @responses.activate
    def test_get_value_for_unknown_key(self):
        key = 'key'
        responses.add(
            responses.GET, 'http://localhost:8500/v1/kv/{0}'.format(key), status=404)
        consul_api = ConsulApi(consul_config)
        actual_value = consul_api.get_value(key)
        self.assertEqual(actual_value, None)

    @responses.activate
    def test_get_service_catalogue(self):
        service_catalogue = {'consul': {'Service': 'consul', 'Tags': [], 'ModifyIndex': 0,
                                        'EnableTagOverride': False, 'ID': 'consul', 'Address': '', 'CreateIndex': 0, 'Port': 8300}}
        responses.add(responses.GET, 'http://localhost:8500/v1/agent/services',
                      json=service_catalogue, status=200)
        consul_api = ConsulApi(consul_config)
        actual_service_catalogue = consul_api.get_service_catalogue()
        self.assertEqual(actual_service_catalogue, service_catalogue)

    @responses.activate
    def test_register_http_check_succeeds(self):
        responses.add(
            responses.PUT, 'http://localhost:8500/v1/agent/check/register', status=200)
        consul_api = ConsulApi(consul_config)
        is_success = consul_api.register_http_check(
            'Ping', id='http_check', name='Ping', url='http://127.0.0.1:8080/ping', interval='10s')
        self.assertEqual(is_success, True)

    @responses.activate
    def test_register_http_check_fails(self):
        responses.add(
            responses.PUT, 'http://localhost:8500/v1/agent/check/register', status=400)
        consul_api = ConsulApi(consul_config)
        is_success = consul_api.register_http_check(
            'Ping', id='http_check', name='Ping', url='http://127.0.0.1:8080/ping', interval='10s')
        self.assertEqual(is_success, False)

    @responses.activate
    def test_register_script_check_succeeds(self):
        responses.add(
            responses.PUT, 'http://localhost:8500/v1/agent/check/register', status=200)
        consul_api = ConsulApi(consul_config)
        is_success = consul_api.register_script_check(
            'serviceActive', id='script_check', name='Service active', script_path='/opt/service_name/scripts/health_check.py', interval='30s')
        self.assertEqual(is_success, True)

    @responses.activate
    def test_register_check_fails(self):
        responses.add(
            responses.PUT, 'http://localhost:8500/v1/agent/check/register', status=400)
        consul_api = ConsulApi(consul_config)
        is_success = consul_api.register_script_check(
            'serviceActive', id='script_check', name='Service active', script_path='/opt/service_name/scripts/health_check.py', interval='30s')
        self.assertEqual(is_success, False)

    @responses.activate
    def test_register_service_succeeds(self):
        responses.add(
            responses.PUT, 'http://localhost:8500/v1/agent/service/register', status=200)
        consul_api = ConsulApi(consul_config)
        is_success = consul_api.register_service(
            id='service_id', name='service_name', address='127.0.0.1', port=8080, tags=['tag'])
        self.assertEqual(is_success, True)

    @responses.activate
    def test_register_service_fails(self):
        responses.add(
            responses.PUT, 'http://localhost:8500/v1/agent/service/register', status=400)
        consul_api = ConsulApi(consul_config)
        is_success = consul_api.register_service(
            id='service_id', name='service_name', address='127.0.0.1', port=8080, tags=['tag'])
        self.assertEqual(is_success, False)
