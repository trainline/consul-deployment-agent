# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.
from common import *
from generate_sensu_check import generate_sensu_check
import json
import re

def create_service_check_filename(service_id, check_id):
    return service_id + '-' + check_id

class DeregisterOldSensuHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DeregisterOldSensuHealthChecks')
    def _run(self, deployment):
        if deployment.last_id is None:
            deployment.logger.info('Skipping {0} stage as there is no previous deployment.'.format(self.name))
        else:
            deployment.logger.info('Deregistering Sensu healthchecks from previous deployment.')
            previous_appspec = get_previous_deployment_appspec(deployment)
            if previous_appspec is None:
                deployment.logger.warning('Previous deployment directory not found, id: {0}'.format(deployment.last_id))
            else:
                (healthchecks, scripts_base_dir) = find_healthchecks('sensu', deployment.last_archive_dir, previous_appspec, deployment.logger)
                if healthchecks is None:
                    return
                for check_id, check in healthchecks.iteritems():
                    service_check_filename = create_service_check_filename(deployment.service.id, check_id)
                    definition_absolute_path = os.path.join(deployment.sensu['sensu_check_path'], service_check_filename)
                    if os.path.exists(definition_absolute_path):
                      os.remove(definition_absolute_path)

class RegisterSensuHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='RegisterSensuHealthChecks')
    def _run(self, deployment):
        def validate_checks(healthchecks, scripts_base_dir):
            for check_id, check in healthchecks.iteritems():
                validate_check(check_id, check)
            ids_list = [id.lower() for id in healthchecks.keys()]
            if len(ids_list) != len(set(ids_list)):
                raise DeploymentError('Sensu health checks require unique ids (case insensitive)')

            names_list = [tmp['name'] for tmp in healthchecks.values()]
            if len(names_list) != len(set(names_list)):
                raise DeploymentError('Sensu health checks require unique names (case insensitive)')

            for check_id, check in healthchecks.iteritems():
                if 'local_script' in check:
                    if check['local_script'].startswith('/'):
                        check['local_script'] = check['local_script'][1:]
                        
                    file_path = os.path.join(deployment.archive_dir, scripts_base_dir, check['local_script'])
                    if not os.path.exists(file_path):
                        raise DeploymentError('Couldn\'t find Sensu health check script in package with path: {0}'.format(os.path.join(scripts_base_dir, check['local_script'])))
                elif 'server_script' in check:
                    file_path = find_server_script(deployment.sensu['healthcheck_search_paths'], check['server_script'])
                    if file_path == None:
                        raise DeploymentError('Couldn\'t find server Sensu health check script: {0}\nPaths searched: {1}'.format(check['server_script'], deployment.sensu['healthcheck_search_paths']))

        def validate_check(check_id, check):
            required_fields = ['name', 'interval']
            for field in required_fields:
                if not field in check:
                    raise DeploymentError('Health check \'{0}\' is missing field \'{1}\''.format(check_id, field))
            if not re.match(r'^[\w\.-]+$', check['name']):
                raise DeploymentError('Health check name \'{0}\' doesn\'t match required Sensu name expression {1}'.format(check['name'], '/^[\w\.-]+$/'))
            if 'local_script' in check and 'server_script' in check:
                raise DeploymentError('Failed to register health check \'{0}\', you can use either \'local_script\' or \'server_script\', but not both.'.format(check_id))
            if not ('local_script' in check or 'server_script' in check):
                raise DeploymentError('Failed to register health check \'{0}\', you need at least one of: \'local_script\' or \'server_script\''.format(check_id))
            
        deployment.logger.info('Registering Sensu healthchecks.')
        (healthchecks, scripts_base_dir) = find_healthchecks('sensu', deployment.archive_dir, deployment.appspec, deployment.logger)
        if healthchecks is None:
            return

        validate_checks(healthchecks, scripts_base_dir)
        for check_id, check in healthchecks.iteritems():

            if 'local_script' in check:
                script_absolute_path = os.path.join(deployment.archive_dir, scripts_base_dir, check['local_script'])

                # Add execution permission to file
                st = os.stat(script_absolute_path)
                os.chmod(script_absolute_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            elif 'server_script' in check:
                script_absolute_path = find_server_script(deployment.sensu['healthcheck_search_paths'], check['server_script'])
            else:
                raise DeploymentError('That should never happen - neither \'local_script\' nor \'server_script\' defined in health check')
            
            deployment.logger.debug('Healthcheck {0} full path: {1}'.format(check_id, script_absolute_path))
            is_success = create_and_copy_check(deployment, script_absolute_path, check_id, check)

            if not is_success:
                raise DeploymentError('Failed to register Sensu health check \'{0}\''.format(check_id))

def find_server_script(paths, server_script):
    for path in paths:
        script_path = os.path.join(path, server_script)
        if os.path.exists(script_path):
            return script_path
        if os.path.exists(script_path + '.json'):
            return script_path + '.json'
    return None

def create_check_definition(deployment, script_path, check_id, check):
    if 'team' in check:
        team = check['team']
    else:
        team = deployment.cluster
    team = team.lower()
    deployment.logger.debug('Setting team of Sensu check \'{0}\' to: \'{1}\''.format(check_id, team))

    return generate_sensu_check(check_name=check['name'],
                                 command=script_path,
                                 interval=check.get('interval'),
                                 alert_after=check.get('alert_after', 600),
                                 realert_every=check.get('realert_every', 30),
                                 notification_email=check.get('notification_email', False),
                                 team=team)

def create_and_copy_check(deployment, script_path, check_id, check):
    check_definition = create_check_definition(deployment, script_path, check_id, check)
    service_check_filename = create_service_check_filename(deployment.service.id, check_id)
    definition_absolute_path = os.path.join(deployment.sensu['sensu_check_path'], service_check_filename)
    
    with open(definition_absolute_path, 'w') as check_definition_file_descriptor:
      check_definition_file_descriptor.write(json.dumps(check_definition))
    deployment.logger.info('Copied Sensu health check \'{0}\' to checks directory \'{1}\''.format(check_id, definition_absolute_path))
    return True




