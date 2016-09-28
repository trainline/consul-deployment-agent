# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import key_naming_convention
import logging
from consul_session import ConsulError
from server_role import ServerRole
from service import Service

class ConsulDataLoader:
    def __init__(self, consul_session):
        self._consul_session = consul_session

    def load_server_role(self, environment):
        server_role = ServerRole(environment.server_role)
        services_key = key_naming_convention.get_server_role_services_key(environment)
        for key in self._consul_session.find_keys(services_key):
            try:
                service_target_state = self._consul_session.get_json_value(key)
                service_name = service_target_state.get('Name')
                service_version = service_target_state.get('Version')
                deployment_id = service_target_state.get('DeploymentId')
                deployment_slice = service_target_state.get('Slice','none')

                service_definition_key = key_naming_convention.get_service_definition_key(environment, service_name, service_version)
                service_installation_key = key_naming_convention.get_service_installation_key(environment, service_name, service_version)
                service_definition = self._consul_session.get_json_value(service_definition_key).get('Service', {})
                service_definition['Address'] = environment.ip_address
                service_installation = self._consul_session.get_json_value(service_installation_key)

                service = Service(service_definition, service_installation)
                service.deployment_id = deployment_id
                service.slice = deployment_slice
                service.tag('deployment_id:', deployment_id)
                service.tag('server_role:', environment.server_role)
                service.tag('slice:', deployment_slice)
                server_role.services[deployment_id] = service
            except (ConsulError, ValueError) as e:
                logging.exception(e)
                logging.warning('Failed to read service from Consul, will ignore. [name: %s version: %s deployment_id: %s]', service_name, service_version, deployment_id)
        return server_role

    def load_service_catalog(self):
        registered_services = self._consul_session.registered_services()
        services = []
        for name, definition in registered_services.iteritems():
            for tag in definition['Tags']:
                if tag.startswith('deployment_id'):
                    services.append(Service(definition))
        return services
