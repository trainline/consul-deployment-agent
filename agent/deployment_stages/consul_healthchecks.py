# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.
from common import *

def create_service_check_id(service_id, check_id):
    return service_id + ':' + check_id

class DeregisterOldConsulHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DeregisterOldConsulHealthChecks')
    def _run(self, deployment):
        if deployment.last_id is None:
            deployment.logger.info('Skipping {0} stage as there is no previous deployment.'.format(self.name))
        else:
            deployment.logger.info('Deregistering Consul healthchecks from previous deployment.')
            previous_appspec = get_previous_deployment_appspec(deployment)
            if previous_appspec is None:
                deployment.logger.warning('Previous deployment directory not found, id: {0}'.format(deployment.last_id))
            else:
                (healthchecks, scripts_base_dir) = find_healthchecks('consul', deployment.last_archive_dir, previous_appspec, deployment.logger)
                if healthchecks is None:
                    return
                for check_id, check in healthchecks.iteritems():
                    service_check_id = create_service_check_id(deployment.service.id, check_id)
                    deployment.consul_api.deregister_check(service_check_id)

class RegisterConsulHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='RegisterConsulHealthChecks')
    def _run(self, deployment):
        def validate_checks(healthchecks, scripts_base_dir):
            ids_list = [id.lower() for id in healthchecks.keys()]
            if len(ids_list) != len(set(ids_list)):
                raise DeploymentError('Consul health checks require unique ids (case insensitive)')

            names_list = [tmp['name'] for tmp in healthchecks.values()]
            if len(names_list) != len(set(names_list)):
                raise DeploymentError('Consul health checks require unique names (case insensitive)')

            for check_id, check in healthchecks.iteritems():
                validate_check(check_id, check)
                if check['type'] == 'script':
                    if check['script'].startswith('/'):
                        check['script'] = check['script'][1:]
                        
                    file_path = os.path.join(deployment.archive_dir, scripts_base_dir, check['script'])
                    if not os.path.exists(file_path):
                        raise DeploymentError('Couldn\'t find health check script in package with path: {0}'.format(os.path.join(scripts_base_dir, check['script'])))

        def validate_check(check_id, check):
            if not 'type' in check or (check['type'] != 'script' and check['type'] != 'http'):
                raise DeploymentError('Failed to register health check \'{0}\', only \'script\' and \'http\' check types are supported, found {1} .'.format(check_id, check['type']))
            if check['type'] == 'script':
                required_fields = ['name', 'script', 'interval']
            elif check['type'] == 'http':
                required_fields = ['name', 'http', 'interval']
            for field in required_fields:
                if not field in check:
                    raise DeploymentError('Health check \'{0}\' is missing field \'{1}\''.format(check_id, field))

        deployment.logger.info('Registering Consul healthchecks.')
        (healthchecks, scripts_base_dir) = find_healthchecks('consul', deployment.archive_dir, deployment.appspec, deployment.logger)
        if healthchecks is None:
            return

        validate_checks(healthchecks, scripts_base_dir)
        for check_id, check in healthchecks.iteritems():
            service_check_id = create_service_check_id(deployment.service.id, check_id)

            if check['type'] == 'script':
                file_path = os.path.join(deployment.archive_dir, scripts_base_dir, check['script'])

                # Add execution permission to file
                st = os.stat(file_path)
                os.chmod(file_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

                deployment.logger.debug('Healthcheck {0} full path: {1}'.format(check_id, file_path))
                is_success = deployment.consul_api.register_script_check(deployment.service.id, service_check_id, check['name'], file_path, check['interval'])
            elif check['type'] == 'http':
                is_success = deployment.consul_api.register_http_check(deployment.service.id, service_check_id, check['name'], check['http'], check['interval'])
            else:
                is_success = False

            if is_success:
                deployment.logger.info('Successfuly registered health check \'{0}\''.format(check_id))
            else:
                raise DeploymentError('Failed to register health check \'{0}\''.format(check_id))
