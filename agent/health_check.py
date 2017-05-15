# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import os

from agent.deployment_stages.common import wrap_script_command
from agent.healthcheck_utils import HealthcheckTypes, HealthcheckUtils

class HealthCheck(object):
    @staticmethod
    def create(data, deployment, slice, logger):
        check_type = HealthcheckUtils.get_type(data)
        if check_type == HealthcheckTypes.HTTP:
            return HttpCheck(data, deployment, slice, logger)
        elif check_type == HealthcheckTypes.SCRIPT:
            return ScriptCheck(data, deployment, slice, logger)
        elif check_type == HealthcheckTypes.PLUGIN:
            return PluginCheck(data, deployment, slice, logger)
        else:
            return HealthCheck(data, deployment, slice, logger)

    def __init__(self, data, deployment, slice, logger):
        self.name = HealthcheckUtils.get_unique_name(data, deployment.service)
        self.data = data
        self.deployment = deployment
        self.slice = slice
        self.logger = logger
        self.type = HealthcheckTypes.UNKNOWN

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
            'tip': self.data.get('tip', 'Fill me up with information')
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
        return 'undef'

    def get_override_notification_email(self):
        override_notification_email = self.data.get('override_notification_email', None)
        if override_notification_email is None:
            if self.data.get('notification_email') is not None:
                self.logger.warning('\'notification_email\' property is deprecated, please use \'override_notification_email\' instead')
                override_notification_email = self.data.get('notification_email', None)
        if override_notification_email is not None:
            return ','.join(override_notification_email)
        return 'undef'

    def get_override_notification_settings(self):
        override_notification_settings = self.data.get('override_notification_settings', None)
        if override_notification_settings is None:
            if self.data.get('team', None) is not None:
                self.logger.warning('\'team\' property is deprecated, please use \'override_notification_settings\' instead')
                override_notification_settings = self.data.get('team', None)
        if override_notification_settings is None:
            override_notification_settings = self.deployment.cluster.lower()
        return override_notification_settings


class HttpCheck(HealthCheck):
    PLUGIN_FILE = 'ttl-check-http.bat'
    
    def __init__(self, *args, **kwargs):
        super(HttpCheck, self).__init__(*args, **kwargs)
        self.type = HealthcheckTypes.HTTP
        self.url = HealthcheckUtils.get_http_url(self.data, self.deployment.service)

    def get_command(self):
        if self.deployment.platform == 'linux':
            return 'HTTP checks are not supported on linux, please implement your own'
        http_check_path = self.find_sensu_plugin(self.deployment, HttpCheck.PLUGIN_FILE)
        if http_check_path is None:
            raise Exception('Could not find HTTP plugin')
        else:
            return '{0} {1}'.format(http_check_path, self.url)


class ScriptCheck(HealthCheck):
    def __init__(self, *args, **kwargs):
        super(ScriptCheck, self).__init__(*args, **kwargs)
        self.type = HealthcheckTypes.SCRIPT
        self.script_path = self.data.get('script')
        self.script_args = self.data.get('script_arguments', '')

    def get_command(self):
        command = wrap_script_command(self.script_path, self.deployment.platform)
        script_args_and_slice = ' '.join(filter(None, (self.script_args, self.slice)))
        return '{0} {1}'.format(command, script_args_and_slice).rstrip()


class PluginCheck(HealthCheck):
    def __init__(self, *args, **kwargs):
        super(PluginCheck, self).__init__(*args, **kwargs)
        self.type = HealthcheckTypes.SCRIPT
        self.plugin_name = self.data.get('plugin')
        self.script_args = self.data.get('plugin_arguments', '')

    def get_command(self):
        command = wrap_script_command(self.plugin_name, self.deployment.platform)
        return '{0} {1}'.format(command, self.script_args).rstrip()

