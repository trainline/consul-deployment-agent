# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

def get_deployment_key(deployment_id):
    if deployment_id is None:
        raise ValueError('deployment_id must be specified.')
    return 'deployments/{0}'.format(deployment_id)

def get_instance_deployment_key(environment, deployment_id):
    return '{0}/nodes/{1}'.format(get_deployment_key(deployment_id), environment.instance_id)

def get_server_role_key(environment):
    if environment is None:
        raise ValueError('environment must be specified.')
    return 'environments/{0}/roles/{1}'.format(environment.environment_name, environment.server_role)

def get_server_role_config_key(environment):
    return '%s/configuration' % get_server_role_key(environment)

def get_server_role_services_key(environment):
    return '%s/services' % get_server_role_key(environment)

def get_service_key(environment, name, version):
    if environment is None:
        raise ValueError('environment must be specified.')
    if name is None:
        raise ValueError('name must be specified.')
    if version is None:
        raise ValueError('version must be specified.')
    return 'environments/{0}/services/{1}/{2}'.format(environment.environment_name, name, version)

def get_service_definition_key(environment, name, version):
    return '%s/definition' % get_service_key(environment, name, version)

def get_service_installation_key(environment, name, version):
    return '%s/installation' % get_service_key(environment, name, version)
