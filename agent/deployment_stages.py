# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import dir_utils, distutils.core, os, sys, yaml, zipfile
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
            appspec_filepath = os.path.join(deployment.last_archive_dir, 'appspec.yml')
            deployment.logger.debug('Loading existing deployment appspec file from {0}.' .format(appspec_filepath))
            appspec_stream = file(appspec_filepath, 'r')
            appspec = yaml.load(appspec_stream)
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
                if definition[0]['location'].startswith('/'):
                    location = definition[0]['location'][1:]
                else:
                    location = definition[0]['location']
                if not os.path.isfile(location):
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
