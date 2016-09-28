# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import consulate, json, logging, requests, sys
from retrying import retry

class ConsulError(RuntimeError):
    pass

class ConsulSession:
    def __init__(self, consul_config):
        self.config = consul_config
        self.base_url = '{0}://{1}:{2}/{3}/kv'.format(self.config['scheme'], self.config['host'], self.config['port'], self.config['version'])
        logging.debug('Creating Consul session with local agent using token: %s.' % self.config['acl_token'])
        self.last_known_index = 0
        self.session = consulate.Consul(token=self.config['acl_token'])
        self._validate_session()

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _api_request(self, request_url):
        return requests.get(request_url, headers={'X-Consul-Token':self.config['acl_token']})

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _find_keys(self, key_prefix):
        return self.session.kv.find(key_prefix)

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=60000)
    def _get_modify_index(self, key_prefix):
        try:
            logging.debug('Retrieving latest Consul key-value store modify index for key prefix \'{0}\''.format(key_prefix))
            response = self._api_request('{0}/{1}?index'.format(self.base_url, key_prefix))
            modify_index = response.headers.get('X-Consul-Index')
            logging.debug('Retrieved X-Consul-Index: {0}'.format(modify_index))
            return modify_index
        except requests.exceptions.ConnectionError as e:
            logging.error('Request to Consul agent has failed.')
            logging.exception(e)
            raise ConsulError('Index query on Consul key-value store has failed.')

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _get_value(self, key):
        return self.session.kv[key]

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _key_exists(self, key):
        return key in self.session.kv

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _register(self, service):
        return self.session.agent.service.register(
            service.name,
            service_id=service.id,
            address=service.address,
            port=service.port,
            tags=service.tags)

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _registered_services(self):
        return self.session.agent.services()

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _unregister(self, service):
        return self.session.agent.service.deregister(service.id)

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _validate_session(self):
        try:
            self.session.status.leader()
        except requests.exceptions.ConnectionError as e:
            message = 'Failed to establish connection with Consul agent. Check that Consul agent is running.'
            logging.error(message)
            logging.exception(e)
            raise ConsulError(message)

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _write_json_value(self, key, value):
        self.session.kv[key] = json.dumps(value)
        return True

    def find_keys(self, key_prefix):
        try:
            return self._find_keys(key_prefix)
        except requests.exceptions.ConnectionError as e:
            logging.error('Failed to search for keys with prefix \'%s\' from Consul key-value store . Check that Consul agent is running.' % key_prefix)
            logging.exception(e)
            return []

    def get_json_value(self, key):
        if self.key_exists(key):
            try:
                value = self._get_value(key)
                return json.loads(value)
            except ValueError as e:
                raise ValueError('Failed to parse value as JSON. Value: {0}\nInternal error: {1}'.format(value, str(e)))
            except requests.exceptions.ConnectionError as e:
                message = 'Failed to load value from Consul key-value store. Check that Consul agent is running.'
                logging.error(message)
                logging.exception(e)
                raise ConsulError(message)
        else:
            raise Exception('Consul key-value store does not contain a value for key \'key\'.')

    def key_exists(self, key):
        try:
            return self._key_exists(key)
        except requests.exceptions.ConnectionError as e:
            logging.error('Failed to check that key \'%s\' exists in Consul key-value store . Check that Consul agent is running.' % key)
            logging.exception(e)
            return False

    def register(self, service):
        try:
            return self._register(service)
        except requests.exceptions.ConnectionError as e:
            logging.error('Failed to register service with Consul. Check that Consul agent is running.')
            logging.exception(e)
            return False

    def registered_services(self):
        try:
            services = self._registered_services()
            if len(services) != 1:
                raise ValueError('Unexpected Consul catalog format.')
            return services[0]
        except requests.exceptions.ConnectionError as e:
            message = 'Failed to retrieve registered services from Consul. Check that Consul agent is running.'
            logging.error(message)
            logging.exception(e)
            raise ConsulError(message)

    def unregister(self, service):
        try:
            return self._unregister(service)
        except requests.exceptions.ConnectionError as e:
            logging.error('Failed to unregister service with Consul. Check that Consul agent is running.')
            logging.exception(e)
            return False

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=60000)
    def wait_for_change(self, key_prefix):
        try:
            modify_index = self._get_modify_index(key_prefix)
            if modify_index is None:
                self.last_known_index = modify_index
                raise ConsulError('Modify index is invalid.')
            if self.last_known_index is None:
                logging.info('There may be changes that have not been processed yet, skipping blocking query.')
                self.last_known_index = modify_index
                return
            self.last_known_index = modify_index
            logging.debug('Blocking query to Consul API to wait for changes in the \'{0}\' key space...'.format(key_prefix))
            # TODO: Timeout by default is 5 minutes. This can be changed by adding wait=10s or wait=10m to the query string
            self._api_request('{0}/{1}?index={2}'.format(self.base_url, key_prefix, self.last_known_index))
        except ConsulError as e:
            logging.exception(e)
            raise
        except:
            logging.error('Request to Consul agent has failed.')
            logging.exception(sys.exc_info()[1])
            raise ConsulError('Blocking query to wait for changes on Consul key-value store has failed.')

    def write_json_value(self, key, value):
        try:
            return self._write_json_value(key, value)
        except requests.exceptions.ConnectionError as e:
            message = 'Failed to set value in Consul key-value store. Check that Consul agent is running.'
            logging.error(message)
            logging.exception(e)
            raise ConsulError(message)
