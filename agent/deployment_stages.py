# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import dir_utils, distutils.core, os, sys, yaml, zipfile, stat
from deployment_scripts import PowershellScript, ShellScript

def find_absolute_path(archive_dir, location):
    if location.startswith('/'):
        location = location[1:]
    return os.path.join(archive_dir, location)

def get_previous_deployment_appspec(deployment):
    appspec_filepath = os.path.join(deployment.last_archive_dir, 'appspec.yml')
    deployment.logger.debug('Loading existing deployment appspec file from {0}.' .format(appspec_filepath))
    appspec_stream = file(appspec_filepath, 'r')
    return yaml.load(appspec_stream)

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
        return_code, stdout, stderr = self.script.execute(logger)
        logger.debug('Return code: {0}'.format(return_code))
        logger.debug('Standard output : {0}'.format(stdout))
        logger.debug('Standard error : {0}'.format(stderr))
        if return_code == 0:
            logger.info('Lifecycle hook {0} script execution succeeded.'.format(self.lifecycle_event))
        else:
            raise DeploymentError('Lifecycle hook {0} script execution failed. See script output.'.format(self.lifecycle_event))

class ValidateDeployment(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='ValidateDeployment')
    def _run(self, deployment):
        if deployment.number_of_attempts < deployment.max_number_of_attempts:
            deployment.number_of_attempts += 1
        else:
            raise DeploymentError('Maximum number of attempts ({0}) has been reached.'.format(deployment.max_number_of_attempts))

class StopApplication(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='StopApplication', lifecycle_event='ApplicationStop')
    def _run(self, deployment):
        if deployment.last_id is None:
            deployment.logger.info('Skipping {0} stage as there is no previous deployment.'.format(self.name))
        else:
            appspec = get_previous_deployment_appspec(deployment)
            hook_definition = appspec['hooks'].get(self.lifecycle_event)
            if hook_definition is None:
                deployment.logger.info('Skipping {0} stage as there is no hook defined.'.format(self.name))
                return
            location = hook_definition[0]['location']
            if location.startswith('/'):
                location = location[1:]
            script_filepath = os.path.join(deployment.last_archive_dir, location)
            env = {'APPLICATION_ID':str(deployment.service.id),
                'DEPLOYMENT_BASE_DIR':str(deployment.last_archive_dir),
                'DEPLOYMENT_ID':str(deployment.last_id),
                'LIFECYCLE_EVENT':str(self.lifecycle_event)}
            self._init_script(hook_definition[0], script_filepath, env, appspec['os'].lower(), deployment.timeout)
            self._run_script(deployment.logger)

class DownloadBundleFromS3(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DownloadBundleFromS3')
    def _run(self, deployment):
        deployment.logger.debug('Creating {0} directory for bundle.'.format(deployment.archive_dir))
        if not os.path.exists(deployment.archive_dir):
            os.makedirs(deployment.archive_dir)

        package_bucket = deployment.service.installation['package_bucket']
        package_key = deployment.service.installation['package_key']
        bundle_filepath = os.path.join(deployment.dir, 'bundle.zip')
        deployment.logger.debug('Downloading bundle from S3 bucket \'{0}\' with key \'{1}\' to {2}.'.format(package_bucket, package_key, bundle_filepath))
        if not deployment.s3_file_manager.download_file(package_bucket, package_key, bundle_filepath):
            raise DeploymentError('Failed to download bundle from S3 bucket \'{0}\' with key \'{1}\' to {2}.'.format(package_bucket, package_key, bundle_filepath))

        deployment.logger.debug('Extracting {0} to {1}.'.format(bundle_filepath, deployment.archive_dir))
        bundle_fh = open(bundle_filepath, 'rb')
        z = zipfile.ZipFile(bundle_fh)
        for name in z.namelist():
            z.extract(name, deployment.archive_dir)
        bundle_fh.close()
        deployment.logger.info('Bundle downloaded and extracted to {0}.'.format(deployment.archive_dir))

class ValidateBundle(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='ValidateBundle')
    def _run(self, deployment):
        def validate_appspec(deployment):
            deployment.logger.debug('Validating appspec file OS.')
            os_type = deployment.appspec.get('os', None)
            if os_type is None or os_type != deployment.platform:
                raise DeploymentError('Invalid appspec.yml: \'os\' property not set to \'{0}\''.format(deployment.platform))
            for file in deployment.appspec.get('files', []):
                if 'source' not in file:
                    raise DeploymentError('Invalid appspec.yml: Contains file definition with missing source. File definition: {0}'.format(file))
                if 'destination' not in file:
                    raise DeploymentError('Invalid appspec.yml: Contains file definition with missing destination. File definition: {0}'.format(file))
            for permission in deployment.appspec.get('permissions', []):
                if 'object' not in permission:
                    raise DeploymentError('Invalid appspec.yml: Contains permission definition with missing object. Permission definition: {0}'.format(permission))
            for hook_name, definition in deployment.appspec.get('hooks', {}).iteritems():
                if 'location' not in definition[0] or not definition[0]['location']:
                    raise DeploymentError('Invalid appspec.yml: Contains hook \'{0}\' definition with missing location. Hook definition: {1}'.format(hook_name, definition))
                location = definition[0]['location']
                if location.startswith('/'):
                    location = location[1:]
                filepath = os.path.join(deployment.archive_dir, location)
                if not os.path.isfile(filepath):
                    raise DeploymentError('Invalid appspec.yml: Could not find deployment script \'{0}\' make certain it does exist'.format(definition[0]['location']))
        deployment.logger.debug('Loading appspec file from {0}.' .format(os.path.join(deployment.archive_dir, 'appspec.yml')))
        appspec_stream = file(os.path.join(deployment.archive_dir, 'appspec.yml'), 'r')
        deployment.appspec = yaml.load(appspec_stream)
        validate_appspec(deployment)

class BeforeInstall(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='BeforeInstall', lifecycle_event='BeforeInstall')

class CopyFiles(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='CopyFiles')
    def _run(self, deployment):
        def clean_up(files, logger):
            for file in files:
                if os.path.isdir(file['destination']):
                    deployment.logger.debug('Destination {0} already exists, cleaning up first.'.format(file['destination']))
                    distutils.dir_util.remove_tree(file['destination'])
        def copy_files(files, logger):
            for file in deployment.appspec.get('files', []):
                if file['source'].startswith('/'):
                    source = os.path.join(deployment.archive_dir, file['source'][1:])
                else:
                    source = os.path.join(deployment.archive_dir, file['source'])
                if os.path.isdir(source):
                    deployment.logger.debug('Moving content of {0} directory recursively to {1}.'.format(source, file['destination']))
                    distutils.dir_util.copy_tree(source, file['destination'])
                else:
                    if not os.path.isdir(file['destination']):
                        deployment.logger.debug('Creating missing directory {0}.'.format(file['destination']))
                        distutils.dir_util.mkpath(file['destination'])
                    deployment.logger.debug('Moving file {0} to {1}.'.format(source, file['destination']))
                    distutils.file_util.copy_file(source, file['destination'])
        if 'files' not in deployment.appspec:
            deployment.logger.info('Skipping CopyFiles stage as there are no file operations defined in appspec.yml.')
            return
        clean_up(deployment.appspec.get('files', []), deployment.logger)
        copy_files(deployment.appspec.get('files', []), deployment.logger)

class ApplyPermissions(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='ApplyPermissions')
    def _run(self, deployment):
        if deployment.platform != 'linux':
            deployment.logger.info('Skipping ApplyPermissions stage as it is not supported on \'{0}\' platform.'.format(deployment.platform))
        elif 'permissions' not in deployment.appspec:
            deployment.logger.info('Skipping ApplyPermissions stage as there are no permission operations defined in appspec.yml.')
        else:
            for permission in deployment.appspec.get('permissions', []):
                object = permission['object']
                if 'owner' in permission or 'group' in permission:
                    deployment.logger.debug('Changing ownership of {0} to user \'{1}\' and group \'{2}\'.'.format(object, permission.get('owner'), permission.get('group')))
                    dir_utils.change_ownership_recursive(object, permission.get('owner'), permission.get('group'))
                if 'mode' in permission:
                    deployment.logger.debug('Changing mode of {0} to {1}.'.format(object, permission['mode']))
                    dir_utils.change_mode_recursive(object, permission['mode'])

class AfterInstall(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='AfterInstall', lifecycle_event='AfterInstall')

class StartApplication(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='StartApplication', lifecycle_event='ApplicationStart')

class ValidateService(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='ValidateService', lifecycle_event='ValidateService')

class RegisterWithConsul(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='RegisterWithConsul')
    def _run(self, deployment):
        deployment.logger.info('Registering service in Consul catalogue.')
        is_success = deployment.consul_api.register_service(
            id=deployment.service.id,
            name=deployment.service.name,
            address=deployment.service.address,
            port=deployment.service.port,
            tags=deployment.service.tags
        )
        if is_success:
            deployment.logger.info('Service registered in Consul catalogue.')
        else:
            deployment.logger.warning('Failed to register service in Consul catalogue.')

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
                os.chmod(file_path, st.st_mode | stat.S_IEXEC)

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

class DeregisterOldSensuHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DeregisterOldSensuHealthChecks')
    def _run(self, deployment):
        raise 'not implemented'

class RegisterSensuHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='RegisterSensuHealthChecks')
    def _run(self, deployment):
        raise 'not implemented'

class DeletePreviousDeploymentFiles(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DeletePreviousDeploymentFiles')
    def _run(self, deployment):
        pass
        # if deployment.last_archive_dir == None:
        #     deployment.logger.info('Skipping {0} stage as there is no previous deployment.'.format(self.name))
        # if os.path.isdir(deployment.last_archive_dir):
        #     deployment.logger.info('Deleting directory of previous deployment {0}.'.format(deployment.last_archive_dir))
        #     distutils.dir_util.remove_tree(deployment.last_archive_dir)
