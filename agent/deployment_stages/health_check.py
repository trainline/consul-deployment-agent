# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See
# LICENSE.txt in the project root for license information.

import os
import re
import stat

from jsonschema import Draft4Validator
from deployment_stages.common import wrap_script_command, script_is_file
from .healthcheck_utils import HealthcheckTypes, HealthcheckUtils
from .schemas import SensuHealthCheckSchema


class HealthCheck(object):
    @staticmethod
    def create(data, deployment):
        check_type = HealthcheckUtils.get_type(data)
        if check_type == HealthcheckTypes.HTTP:
            return HttpCheck(data, deployment)
        elif check_type == HealthcheckTypes.SCRIPT:
            return ScriptCheck(data, deployment)
        elif check_type == HealthcheckTypes.PLUGIN:
            return PluginCheck(data, deployment)
        else:
            return HealthCheck(data, deployment)

    def __init__(self, data, deployment):
        self.name = HealthcheckUtils.get_unique_name(data, deployment.service)
        self.data = data
        self.deployment = deployment
        slice = deployment.service.slice
        self.slice = None if slice is not None and slice.lower() == 'none' else slice
        self.logger = deployment.logger
        self.type = HealthcheckTypes.UNKNOWN

    def validate(self):
        valid_schema = self._validate(Draft4Validator(
            SensuHealthCheckSchema).is_valid(self.data), 'schema is not valid')
        valid_name = self._validate(
            bool(re.match(r'^[\w\.-]+$', self.data.get('name'))), 'name is not valid')
        valid_type = self._validate(
            self.type != HealthcheckTypes.UNKNOWN, 'unknown check type')
        is_standalone = self.data.get('standalone')
        is_aggregate = self.data.get('aggregate')
        valid_standalone = self._validate((not is_standalone and not is_aggregate) or (is_standalone != is_aggregate),
                                          'only of standalone and aggregate can be True')
        return valid_type and valid_schema and valid_name and valid_standalone

    def _validate(self, predicate, description):
        if predicate is not True:
            self.logger.warn('Invalid sensu check: {0}'.format(description))
        return predicate

    def get_definition(self):
        return {
            'aggregate': self.data.get('aggregate', False),
            'alert_after': self.data.get('alert_after', 600),
            'command': self.get_command(),
            'handlers': ['default'],
            'interval': self.data.get('interval'),
            'notification_email': self.get_override_notification_email(),
            'occurrences': self.data.get('occurrences', 5),
            'page': self.data.get('paging_enabled', False),
            'project': self.data.get('project', False),
            'realert_every': self.data.get('realert_every', 30),
            'runbook': self.data.get('runbook', 'Please provide useful information to resolve alert'),
            'sla': self.data.get('sla', 'No SLA defined'),
            'slack_channel': self.get_override_chat_channel(),
            'standalone': self.data.get('standalone', True),
            'subscribers': ['sensu-base'],
            'tags': [],
            'team': self.get_override_notification_settings(),
            'ticket': self.data.get('ticketing_enabled', False),
            'timeout': self.data.get('timeout', 120),
            'tip': self.data.get('tip', 'Fill me up with information'),
            'file': self.data.get('file', None)
        }

    def find_sensu_plugin(self, deployment, script_filename):
        plugin_paths = self.deployment.sensu['healthcheck_search_paths']
        for plugin_path in plugin_paths:
            script_filepath = os.path.join(plugin_path, script_filename)
            if os.path.exists(script_filepath):
                return '{0}'.format(script_filepath)
        return None

    def get_override_chat_channel(self):
        override_chat_channel = self.data.get('override_chat_channel', None)
        if override_chat_channel is not None:
            return ','.join(override_chat_channel)
        return 'undefined'

    def get_override_notification_email(self):
        override_notification_email = self.data.get(
            'override_notification_email', None)
        if override_notification_email is None:
            if self.data.get('notification_email') is not None:
                self.logger.warning(
                    '\'notification_email\' property is deprecated, please use \'override_notification_email\' instead')
                override_notification_email = self.data.get(
                    'notification_email', None)
        if override_notification_email is not None:
            return ','.join(override_notification_email)
        return 'undef'

    def get_override_notification_settings(self):
        override_notification_settings = self.data.get(
            'override_notification_settings', None)
        if override_notification_settings is None:
            if self.data.get('team', None) is not None:
                self.logger.warning(
                    '\'team\' property is deprecated, please use \'override_notification_settings\' instead')
                override_notification_settings = self.data.get('team', None)
        if override_notification_settings is None:
            override_notification_settings = self.deployment.cluster.lower()
        return override_notification_settings


"""
HTTP(S) for checking the response status of a user provioded URL.
Checks are performed by a .bat file provided on each Windows instance
"""


class HttpCheck(HealthCheck):
    WINDOWS_PLUGIN_FILE = 'ttl-check-http.bat'
    LINUX_PLUGIN_FILE = 'check-http.rb'

    def __init__(self, *args, **kwargs):
        super(HttpCheck, self).__init__(*args, **kwargs)
        self.type = HealthcheckTypes.HTTP
        self.url = HealthcheckUtils.get_http_url(
            self.data, self.deployment.service)
        check_file = HttpCheck.LINUX_PLUGIN_FILE if self.deployment.platform == 'linux' else HttpCheck.WINDOWS_PLUGIN_FILE
        self.http_check_path = self.find_sensu_plugin(
            self.deployment, check_file)

    def get_command(self):
        if self.deployment.platform == 'linux':
            return '{0} -u {1}'.format(self.http_check_path, self.url)
        else:
            return '{0} {1}'.format(self.http_check_path, self.url)

    def validate(self):
        return super(HttpCheck, self).validate()


"""
Custom script check for user defined check logic.
Supported types are Python, Powershell or Batch
"""


class ScriptCheck(HealthCheck):
    ALLOWED_WIN_SCRIPTS = ['.py', '.ps1', '.bat']

    def __init__(self, *args, **kwargs):
        super(ScriptCheck, self).__init__(*args, **kwargs)
        self.type = HealthcheckTypes.SCRIPT
        script_path = self.data.get('script', '').lstrip('\/')
        script_path = os.path.join(
            self.deployment.archive_dir, 'healthchecks', 'sensu', script_path)
        self.script_path = script_path
        self.script_args = self.data.get('script_arguments', '')

    def get_command(self):
        if self.deployment.platform == 'linux':
            st = os.stat(self.script_path)
            os.chmod(self.script_path, st.st_mode |
                     stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        if script_is_file(self.data):
            return wrap_script_command(self.script_path, self.deployment.platform, [self.script_args, self.slice], file=True)
        else:
            return wrap_script_command(self.script_path, self.deployment.platform, [self.script_args, self.slice], file=None)

    def validate(self):
        basic_valid = super(ScriptCheck, self).validate()
        file_exists = self._validate(os.path.exists(
            self.script_path), 'cannot find script file')
        file_type_valid = True
        if self.deployment.platform != 'linux':
            (f_name, f_ext) = os.path.splitext(self.script_path)
            file_type_valid = self._validate(
                f_ext.lower() in ScriptCheck.ALLOWED_WIN_SCRIPTS, 'file type is not supported')
        return basic_valid and file_exists and file_type_valid


"""
Plugin checks specify a sensu plugin to use.
Available plugins are provided on each box at startup.
"""


class PluginCheck(HealthCheck):
    def __init__(self, *args, **kwargs):
        super(PluginCheck, self).__init__(*args, **kwargs)
        self.type = HealthcheckTypes.SCRIPT
        plugin_name = self.data.get('plugin')
        plugin_path = self.find_sensu_plugin(self.deployment, plugin_name)
        self.plugin_path = plugin_path
        self.plugin_args = self.data.get('plugin_arguments', '')

    def get_command(self):
        if script_is_file(self.data):
            return wrap_script_command(self.plugin_path, self.deployment.platform, [self.plugin_args], file=True)
        else:
            return wrap_script_command(self.plugin_path, self.deployment.platform, [self.plugin_args], file=None)

    def validate(self):
        basic_valid = super(PluginCheck, self).validate()
        return basic_valid and os.path.exists(self.plugin_path)
