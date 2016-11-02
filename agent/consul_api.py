import base64, json, logging, requests
from retrying import retry

class ConsulError(RuntimeError):
    pass

def handle_connection_error(func):
    def handle_error(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logging.exception(e)
            raise ConsulError('Failed to establish connection with Consul HTTP API. Check that Consul agent is running.')
    return handle_error

def retry_if_connection_error(exception):
    return isinstance(exception, requests.exceptions.ConnectionError)

class ConsulApi:
    def __init__(self, consul_config):
        self._config = consul_config
        self._base_url = '{0}://{1}:{2}/{3}'.format(self._config['scheme'], self._config['host'], self._config['port'], self._config['version'])
        self._last_known_modify_index = 0

    @handle_connection_error
    @retry(retry_on_exception=retry_if_connection_error, wait_exponential_multiplier=1000, wait_exponential_max=60000)
    def _api_get(self, relative_url):
        url = '{0}/{1}'.format(self._base_url, relative_url)
        logging.debug('Consul HTTP API request: {0}'.format(url))
        response = requests.get(url, headers={'X-Consul-Token':self._config['acl_token']})
        logging.debug('Response status code: {0}'.format(response.status_code))
        logging.debug('Response content: {0}'.format(response.text))
        if response.status_code == 500:
            raise ConsulError('Consul HTTP API internal error. Response content: {0}'.format(reponse.text))
        return response

    @handle_connection_error
    @retry(retry_on_exception=retry_if_connection_error, wait_exponential_multiplier=1000, wait_exponential_max=60000)
    def _api_put(self, relative_url, content):
        url = '{0}/{1}'.format(self._base_url, relative_url)
        logging.debug('Consul HTTP API request URL: {0}'.format(url))
        logging.debug('Consul HTTP API request content: {0}'.format(content))
        response = requests.put(url, data=content, headers={'X-Consul-Token':self._config['acl_token']})
        logging.debug('Response status code: {0}'.format(response.status_code))
        logging.debug('Response content: {0}'.format(response.text))
        if response.status_code == 500:
            raise ConsulError('Consul HTTP API internal error. Response content: {0}'.format(reponse.text))
        return response

    @retry(wait_fixed=5000, stop_max_attempt_number=12)
    def _get_modify_index(self, key):
        logging.debug('Retrieving Consul key-value store modify index for key: {0}'.format(key))
        response = self._api_get('kv/{0}?index'.format(key))
        modify_index = response.headers.get('X-Consul-Index')
        logging.debug('Consul key-value store modify index for key \'{0}\': {1}'.format(key, modify_index))
        return modify_index

    def check_connectivity(self):
        logging.info('Checking Consul HTTP API connectivity')
        self._api_get('agent/self')
        logging.info('Consul HTTP API connectivity OK ')

    def get_keys(self, key_prefix):
        def decode():
            return response.json()
        def not_found():
            logging.warning('Consul key-value store does not contain key prefix \'{0}\''.format(key_prefix))
            return []
        response = self._api_get('kv/{0}?keys'.format(key_prefix))
        cases = { 200: decode, 404: not_found }
        return cases[response.status_code]()

    def get_service_catalogue(self):
        response = self._api_get('agent/services')
        return response.json()

    def get_value(self, key):
        def decode():
            values = response.json()
            for value in values:
                value['Value'] = json.loads(base64.b64decode(value['Value']))
            return values[0].get('Value')
        def not_found():
            logging.warning('Consul key-value store does not contain a value for key \'{0}\''.format(key))
            return None
        response = self._api_get('kv/{0}'.format(key))
        cases = { 200: decode, 404: not_found }
        return cases[response.status_code]()

    def key_exists(self, key):
        return self.get_value(key) is not None

    def register_http_check(self, id, name, url, interval):
        response = self._api_put('agent/check/register', json.dumps({ 'ID': id, 'Name': name, 'HTTP': url, 'Interval': interval }))
        return response.status_code == 200

    def register_script_check(self, id, name, script_path, interval):
        response = self._api_put('agent/check/register', json.dumps({ 'ID': id, 'Name': name, 'Script': script_path, 'Interval': interval }))
        return response.status_code == 200

    def register_service(self, id, name, address, port, tags):
        response = self._api_put('agent/service/register', json.dumps({ 'ID': id, 'Name': name, 'Address': address, 'Port': port, 'Tags': tags }))
        return response.status_code == 200

    def wait_for_change(self, key_prefix):
        modify_index = self._get_modify_index(key_prefix)
        if modify_index is None:
            self._last_known_modify_index = modify_index
            #raise ConsulError('Modify index is invalid.')
        if self._last_known_modify_index is None:
            logging.info('There may be changes that have not been processed yet, skipping blocking query.')
            self._last_known_modify_index = modify_index
            return
        self._last_known_modify_index = modify_index
        logging.debug('Blocking query to Consul HTTP API to wait for changes in the \'{0}\' key space...'.format(key_prefix))
        # TODO: Timeout by default is 5 minutes. This can be changed by adding wait=10s or wait=10m to the query string
        self._api_get('kv/{0}?index={1}'.format(key_prefix, self._last_known_modify_index))

    def write_value(self, key, value):
        modify_index = self._get_modify_index(key)
        response = self._api_put('kv/{0}?cas={1}'.format(key, modify_index), json.dumps(value))
        return response.text == 'true'
