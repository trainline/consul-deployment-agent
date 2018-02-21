# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import datetime, json, key_naming_convention, logging, os, sys
from consul_api import ConsulError
from deployment_stages import CheckDiskSpace, ValidateDeployment, StopApplication, DownloadBundleFromS3, ValidateBundle, BeforeInstall, \
    CopyFiles, ApplyPermissions, AfterInstall, StartApplication, ValidateService, RegisterWithConsul, \
    DeregisterOldConsulHealthChecks, RegisterConsulHealthChecks, DeregisterOldSensuHealthChecks, \
    RegisterSensuHealthChecks, DeletePreviousDeploymentFiles
from s3_file_manager import S3FileManager
from version import semantic_version
from find_deployment import find_deployment_dir_win


class Deployment(object):
    def __init__(self, config={}, consul_api=None, aws_config={}):
        if config is None:
            raise ValueError('config must be specified.')
        if consul_api is None:
            raise ValueError('consul_api must be specified.')

        print('DEPLOYMENT: {0}'.format(config))

        self._validate_config(config)
        self._aws_config = aws_config
        self.consul_api = consul_api
        self._cause = config.get('cause')
        self._environment = config.get('environment')
        self.cluster = self._environment.cluster
        self.instance_tags = self._environment.instance_tags
        self.id = config.get('deployment_id')
        self.last_id = config.get('last_deployment_id')
        self.max_number_of_attempts = config.get('max_number_of_attempts', 1)
        self.platform = config.get('platform')
        self.sensu = config.get('sensu')
        self.s3_file_manager = S3FileManager(self._aws_config)
        self.service = config.get('service')
        self.timeout = self.service.installation['timeout']
        self._is_success = self.logger = self._log_filename = self._log_filepath = self._report = self._report_key = None
        self.number_of_attempts = 0
        if self.platform == 'linux':
            base_dir = '/opt/consul-deployment-agent/deployments'
            self.base_dir = base_dir
            self.dir = os.path.join(base_dir, self.service.id, self.id)
            if self.last_id is not None:
                self.last_dir = os.path.join(base_dir, self.service.id, self.last_id)
                self.last_archive_dir = os.path.join(self.last_dir, 'archive')
        else:
            base_dir = 'C:\TLDeploy'
            self.base_dir = base_dir
            self.dir = os.path.join(base_dir, self.service.id, self.id)
            if self.last_id is not None:
                self.last_dir = find_deployment_dir_win(self.base_dir, self.service.id, self.last_id)
                if self.last_dir is None:
                    self.last_id = None
                else:
                    self.last_archive_dir = os.path.join(self.last_dir, 'archive')
        self.archive_dir = os.path.join(self.dir, 'archive')

    def __str__(self):
        return json.dumps(
            {'id': self.id,
             'service_id': self.service.id,
             'dir': self.dir,
             'last_id': self.last_id,
             'number_of_attempts': self.number_of_attempts,
             'max_number_of_attempts': self.max_number_of_attempts,
             'timeout': self.timeout})

    def _initialise_log(self):
        try:
            self._log_filename = 'deployment-{0}-{1}.log'.format(self._environment.instance_id, self.id)
            self._log_filepath = '{0}/logs/{1}'.format(self.dir, self._log_filename)
            logging.debug('Initialising deployment log file at {0}.'.format(self._log_filepath))
            log_directory = os.path.dirname(self._log_filepath)
            if not os.path.isdir(log_directory):
                logging.debug('Creating log directory {0}.'.format(log_directory))
                os.makedirs(log_directory)
            self.logger = logging.getLogger(self.id)
            fh = logging.FileHandler(self._log_filepath)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
            self.logger.addHandler(fh)
        except:
            logging.error('Failed to initialise deployment log file.')
            logging.exception(sys.exc_info()[1])

    def _finalise_log(self):
        def is_log_shipping_configured(aws_config):
            if 'deployment_logs' not in aws_config or aws_config['deployment_logs']['bucket_name'] is None or \
                    aws_config['deployment_logs']['key_prefix'] is None:
                return False
            return True

        logging.debug('Finalising deployment logs.')
        for handler in self.logger.handlers[:]:
            try:
                handler.close()
                self.logger.removeHandler(handler)
            except IOError as error:
                logging.exception(error)
        if is_log_shipping_configured(self._aws_config):
            if os.path.isfile(self._log_filepath):
                bucket_name = self._aws_config['deployment_logs']['bucket_name']
                key_prefix = self._aws_config['deployment_logs']['key_prefix']
                key = '{0}/{1}/{2}/{3}'.format(key_prefix, self._environment.environment_name, self.service.id,
                                               self._log_filename)
                logging.debug(
                    'Uploading deployment logs to S3 bucket \'{0}\' with key \'{1}\'.'.format(bucket_name, key))
                logfile_url = self.s3_file_manager.upload_file(bucket_name, key, self._log_filepath)
                if logfile_url:
                    logging.debug('Deployment logs uploaded to S3. URL: {0}.'.format(logfile_url))
                    self._update_report({'log': logfile_url})
                else:
                    logging.debug('Deployment logs failed to upload to S3.')
            else:
                logging.error('No known deployment log file, skipping log shipping.')
        else:
            logging.debug('Deployment logs shipping is not configured, skipping log shipping.')

    def _initialise_report(self):
        logging.debug('Initialising deployment report for Consul.')
        self._report_key = key_naming_convention.get_instance_deployment_key(self._environment, self.id)
        existing_report = {}
        if self.consul_api.key_exists(self._report_key):
            logging.debug('Loading existing report from Consul.')
            existing_report = self.consul_api.get_value(self._report_key)
            self.number_of_attempts = existing_report.get('NumberOfAttempts', 0)
        logging.debug('Creating deployment report.')
        self._update_report({
            'cause': self._cause,
            'end_time': '',
            'last_completed_stage': '',
            'log': '',
            'number_of_attempts': self.number_of_attempts,
            'start_time': datetime.datetime.utcnow().isoformat(),
            'status': 'In Progress'
        }, write_to_consul=True)

    def _finalise_report(self):
        logging.debug('Finalising deployment report for Consul.')
        updates = {'end_time': datetime.datetime.utcnow().isoformat(), 'number_of_attempts': self.number_of_attempts}
        if self._is_success is None:
            updates['status'] = 'In Progress'
        elif self._is_success:
            updates['status'] = 'Success'
            updates['last_completed_stage'] = 'Complete'
        else:
            updates['status'] = 'Failed'
        self._update_report(updates, write_to_consul=True)

    def _update_report(self, updates={}, write_to_consul=False):
        def update_if_specified(report, key, value):
            if value is not None:
                report[key] = value

        logging.debug('Updating report with: %s' % updates)
        if self._report is None:
            self._report = {}
        update_if_specified(self._report, 'Cause', updates.get('cause'))
        update_if_specified(self._report, 'EndTime', updates.get('end_time'))
        update_if_specified(self._report, 'LastCompletedStage', updates.get('last_completed_stage'))
        update_if_specified(self._report, 'Log', updates.get('log'))
        update_if_specified(self._report, 'NumberOfAttempts', updates.get('number_of_attempts'))
        update_if_specified(self._report, 'StartTime', updates.get('start_time'))
        update_if_specified(self._report, 'Status', updates.get('status'))
        logging.debug('Report updated: %s' % self._report)
        if write_to_consul:
            try:
                logging.debug('Writing report to Consul.')
                self.consul_api.write_value(self._report_key, self._report)
            except ConsulError as error:
                logging.error('Failed to write deployment report to Consul.')
                logging.exception(error)

    def _validate_config(self, config):
        def check_not_none(property_name, dictionary):
            if dictionary.get(property_name) is None:
                raise ValueError('%s must be specified.' % property_name)

        check_not_none('cause', config)
        check_not_none('deployment_id', config)
        check_not_none('environment', config)
        check_not_none('platform', config)
        check_not_none('service', config)
        check_not_none('sensu', config)

    def run(self):
        try:
            self._initialise_report()
            self._initialise_log()
            self.logger.info('consul-deployment-agent version: {0}'.format(semantic_version))
            self.logger.info('Installing service: {0}'.format(self.service))
            self.logger.info('Configuration: {0}'.format(self))
            self.logger.info('Attempt number: {0}'.format(self.number_of_attempts + 1))
            stages = [CheckDiskSpace(), ValidateDeployment(), DeregisterOldConsulHealthChecks(),
                      DeregisterOldSensuHealthChecks(), StopApplication(), DownloadBundleFromS3(), ValidateBundle(),
                      BeforeInstall(),
                      CopyFiles(), ApplyPermissions(), AfterInstall(), StartApplication(), ValidateService(),
                      RegisterWithConsul(), RegisterConsulHealthChecks(), RegisterSensuHealthChecks(),
                      DeletePreviousDeploymentFiles()]
            for stage in stages:
                success = stage.run(self)
                self._update_report({'last_completed_stage': stage.name})
                if not success:
                    self.logger.error('Deployment has failed.')
                    self._is_success = False
                    break
            if self._is_success is None:
                self._is_success = True
            self._finalise_log()
            self._finalise_report()
            return {'id': self.id, 'is_success': self._is_success}
        finally:
            logging.exception(sys.exc_info()[1])
            self.logger.error('Deployment has failed.')
            self._finalise_log()
            self._finalise_report()
            self._is_success = False
            return {'id': self.id, 'is_success': self._is_success}
