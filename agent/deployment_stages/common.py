# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import os, sys, yaml
from deployment_scripts import PowershellScript, ShellScript

class DeploymentError(RuntimeError):
    pass

class DeploymentStage():
    def __init__(self, name):
        self.name = name
    def _run(self, deployment):
        assert 0, '_run not implemented'
    def run(self, deployment):
        is_success = False
        deployment.logger.debug('Start {0} stage execution.'.format(self.name))
        try:
            self._run(deployment)
            is_success = True
        except:
            deployment.logger.exception(sys.exc_info()[1])
        deployment.logger.debug('End {0} stage execution.'.format(self.name))
        return is_success

class LifecycleHookExecutionStage(DeploymentStage):
    def __init__(self, name, lifecycle_event):
        DeploymentStage.__init__(self, name=name)
        self.lifecycle_event = lifecycle_event
    def _init_script(self, hook_definition, filepath, env, platform, default_timeout):
        if platform == 'linux':
            self.script = ShellScript(filepath, env, hook_definition.get('runas'), hook_definition.get('timeout', default_timeout))
        else:
            self.script = PowershellScript(filepath, env, hook_definition.get('runas'), hook_definition.get('timeout', default_timeout))
    def _run(self, deployment):
        hook_definition = deployment.appspec['hooks'].get(self.lifecycle_event)
        if hook_definition is None:
            deployment.logger.info('Skipping {0} stage as there is no hook defined.'.format(self.lifecycle_event))
            return
        location = hook_definition[0]['location']
        if location.startswith('/'):
            location = location[1:]
        filepath = os.path.join(deployment.archive_dir, location)
        env = {'APPLICATION_ID':str(deployment.service.id),
            'DEPLOYMENT_BASE_DIR':str(deployment.archive_dir),
            'DEPLOYMENT_ID':str(deployment.id),
            'LIFECYCLE_EVENT':str(self.lifecycle_event)}
        self._init_script(hook_definition[0], filepath, env, deployment.platform, deployment.timeout)
        self._run_script(deployment.logger)
    def _run_script(self, logger):
        return_code, stdout = self.script.execute(logger)
        logger.debug('Return code: {0}'.format(return_code))
        logger.debug("Standard output: {0}\n".format(stdout))
        if return_code == 0:
            logger.info('Lifecycle hook {0} script execution succeeded.'.format(self.lifecycle_event))
        else:
            raise DeploymentError('Lifecycle hook {0} script execution failed. See script output.'.format(self.lifecycle_event))

class BeforeInstall(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='BeforeInstall', lifecycle_event='BeforeInstall')

class AfterInstall(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='AfterInstall', lifecycle_event='AfterInstall')

class StartApplication(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='StartApplication', lifecycle_event='ApplicationStart')

class ValidateService(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='ValidateService', lifecycle_event='ValidateService')

def find_absolute_path(archive_dir, location):
    if location.startswith('/'):
        location = location[1:]
    return os.path.join(archive_dir, location)

def get_previous_deployment_appspec(deployment):
    appspec_filepath = os.path.join(deployment.last_archive_dir, 'appspec.yml')
    deployment.logger.debug('Loading existing deployment appspec file from {0}.' .format(appspec_filepath))
    if os.path.exists(appspec_filepath):
        appspec_stream = file(appspec_filepath, 'r')
        return yaml.load(appspec_stream)
    else:
        return None

def find_healthchecks(check_type, archive_dir, appspec, logger):
    relative_path = os.path.join('healthchecks', check_type, 'healthchecks.yml')
    absolute_filepath = os.path.join(archive_dir, relative_path)
    scripts_base_dir = None

    if os.path.exists(absolute_filepath):
        logger.debug('Found {0}'.format(relative_path))
        scripts_base_dir = os.path.join('healthchecks', check_type)
        healthchecks_stream = file(absolute_filepath, 'r')
        healthchecks_object = yaml.load(healthchecks_stream)
        if type(healthchecks_object) is not dict:
            logger.error('{0} doesn\'t contain valid definition of healthchecks'.format(relative_path))
            healthchecks = None
        else:
            healthchecks = healthchecks_object.get('{0}_healthchecks'.format(check_type))
    else:
        scripts_base_dir = ''
        logger.debug('No {0} found, attempting to find specification in appspec.yml'.format(relative_path))
        healthchecks = appspec.get('{0}_healthchecks'.format(check_type))

    if healthchecks is None:
        logger.info('No health checks found.')
    return ( healthchecks, scripts_base_dir )
