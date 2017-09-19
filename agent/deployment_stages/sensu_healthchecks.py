# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import json, os, sys, subprocess
from .common import DeploymentError, DeploymentStage, find_healthchecks, get_previous_deployment_appspec
from .health_check import HealthCheck

def create_sensu_check_definition_filename(service_id, check_id, slice='none'):
    return '{0}-{1}-{2}.json'.format(service_id, check_id, slice)

class DeregisterOldSensuHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DeregisterOldSensuHealthChecks')
    def _run(self, deployment):
        if deployment.last_id is None:
            deployment.logger.info('Skipping {0} stage as there is no previous deployment.'.format(self.name))
            return
            
        deployment.logger.info('Deregistering Sensu healthchecks from previous deployment.')
        previous_appspec = get_previous_deployment_appspec(deployment)
        if previous_appspec is None:
            deployment.logger.warning('Previous deployment directory not found, id: {0}'.format(deployment.last_id))
            return
            
        (healthchecks, scripts_base_dir) = find_healthchecks('sensu', deployment.last_archive_dir, previous_appspec, deployment.logger)
        deployment.logger.debug('Sensu healthchecks to remove: {0}'.format(healthchecks))
        if healthchecks is None:
            deployment.logger.warning('No sensu checks will be removed')
            return
        
        for check_id, check in healthchecks.iteritems():
            deployment.logger.debug('Looking for sensu check: {0}'.format(check_id))
            check_definition_absolute_path = os.path.join(deployment.sensu['sensu_check_path'], create_sensu_check_definition_filename(deployment.service.id, check_id, deployment.service.slice))
            if os.path.exists(check_definition_absolute_path):
                deployment.logger.info('Removing healthcheck: {0}'.format(check_definition_absolute_path))
                os.remove(check_definition_absolute_path)
            else:
                deployment.logger.warning('Could not find file: {0}'.format(check_definition_absolute_path))
        
        if deployment.platform == 'linux':
            command = ['systemctl', 'restart', 'sensu-client']
            subprocess.call(command, shell=False)

class RegisterSensuHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='RegisterSensuHealthChecks')

    def _run(self, deployment):
        deployment.logger.info('Registering Sensu checks.')
        (sensu_checks, scripts_base_dir) = find_healthchecks('sensu', deployment.archive_dir, deployment.appspec, deployment.logger)
        if sensu_checks is None:
            deployment.logger.info('No Sensu checks to register.')
            return

        RegisterSensuHealthChecks.validate_unique_ids(sensu_checks)
        RegisterSensuHealthChecks.validate_unique_names(sensu_checks)
        
        for check_id, check_data in sensu_checks.iteritems():
            check = HealthCheck.create(check_data, deployment)
            if check.validate():
                RegisterSensuHealthChecks.register_check(check_id, check, deployment)
            else:
                deployment.logger.warn('Sensu check "{0}" is invalid and will not be registered'.format(check_id))

        if deployment.platform == 'linux':
            command = ['systemctl', 'restart', 'sensu-client']
            subprocess.call(command, shell=False)

    @staticmethod
    def find_sensu_plugin(plugin_paths, script_filename):
        for plugin_path in plugin_paths:
            script_filepath = os.path.join(plugin_path, script_filename)
            if os.path.exists(script_filepath):
                return '{0}'.format(script_filepath)
        return None

    @staticmethod
    def generate_check_definition(check, deployment):
        instance_tags = deployment.instance_tags
        check_definition = { 'checks': { check.name: check.get_definition() } }
        custom_instance_tags = {k:v for k, v in instance_tags.iteritems() if not k.startswith('aws:')}
        for key, value in custom_instance_tags.iteritems():
            check_definition['checks'][check.name]['ttl_' + key.lower()] = value
        return check_definition

    @staticmethod
    def register_check(check_id, check, deployment):
        check_definition = RegisterSensuHealthChecks.generate_check_definition(check, deployment)
        check_definition_filename = create_sensu_check_definition_filename(deployment.service.id, check_id, deployment.service.slice)
        check_definition_absolute_path = os.path.join(deployment.sensu['sensu_check_path'], check_definition_filename)
        is_success = RegisterSensuHealthChecks.write_check_definition_file(check_definition, check_definition_absolute_path, deployment)
        if not is_success:
            raise DeploymentError('Failed to register Sensu check \'{0}\''.format(check_id))

    @staticmethod
    def validate_unique_ids(checks):
        check_ids = [check_id.lower() for check_id in checks.keys()]
        if len(check_ids) != len(set(check_ids)):
            raise DeploymentError('Sensu check definitions require unique ids (case insensitive)')

    @staticmethod
    def validate_unique_names(checks):
        check_names = [check['name'] for check in checks.values()]
        if len(check_names) != len(set(check_names)):
            raise DeploymentError('Sensu check definitions require unique names (case insensitive)')

    @staticmethod
    def write_check_definition_file(check_definition, check_definition_absolute_path, deployment):
        try:
            with open(check_definition_absolute_path, 'w') as check_definition_file:
                check_definition_file.write(json.dumps(check_definition, sort_keys=True, indent=4, separators=(',', ': ')))
            deployment.logger.info('Created Sensu check definition: {0}'.format(check_definition_absolute_path))
            return True
        except:
            deployment.logger.exception(sys.exc_info()[1])
            return False

