# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import key_naming_convention
import logging
from consul_api import ConsulError
from server_role import ServerRole
from actions import InstallAction, UninstallAction
from service import Service

class ConsulDataLoader:
    def __init__(self, consul_api):
        self._consul_api = consul_api

    def _load_service(self, environment, deployment_id, name, version):
        definition_key = key_naming_convention.get_service_definition_key(environment, name, version)
        installation_key = key_naming_convention.get_service_installation_key(environment, name, version)
        definition = self._consul_api.get_value(definition_key).get('Service', {})
        definition['Address'] = environment.ip_address
        installation = self._consul_api.get_value(installation_key)
        return Service(definition, installation)

    def load_server_role(self, environment):
        server_role = ServerRole(environment.server_role)
        services_key = key_naming_convention.get_server_role_services_key(environment)
        for key in self._consul_api.get_keys(services_key):
            try:
                definition = self._consul_api.get_value(key)
                name = definition.get('Name')
                version = definition.get('Version')
                deployment_id = definition.get('DeploymentId')
                deployment_slice = definition.get('Slice','none')
                deployment_action = definition.get('Action', 'Install')

                if deployment_action not in ['Install', 'Uninstall']:
                    logging.warning('Unknown deployment action \'{0}\', will ignore it.'.format(deployment_action))

                service = self._load_service(environment, deployment_id, name, version)

                # service.deployment_id = deployment_id
                # service.tag('deployment_id:', deployment_id)
                # service.tag('server_role:', environment.server_role)
                # service.tag('slice:', deployment_slice)
                # server_role.services[deployment_id] = service

                if deployment_action == 'Install':
                    server_role.actions.append(InstallAction(deployment_id, service))
                elif deployment_action == 'Uninstall':
                    server_role.actions.append(UninstallAction(deployment_id, service))

            except (ConsulError, ValueError) as e:
                logging.exception(e)
                logging.warning('Failed to read service from Consul, will ignore. [name: {0} version: {1} deployment_id: {2}]'.format(name, version, deployment_id))
        return server_role

    def load_service_catalogue(self):
        registered_services = self._consul_api.get_service_catalogue()
        services = []
        for name, definition in registered_services.iteritems():
            for tag in definition['Tags']:
                if tag.startswith('deployment_id'):
                    services.append(Service(definition))
        return services
