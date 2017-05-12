# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import json
import logging

class Service(object):
    def __init__(self, definition, installation_info={}):
        logging.debug('Service Definition is {0}'.format(definition))

        self.address = definition.get('Address')
        self.installation = {
            'timeout': installation_info.get('InstallationTimeout', 60) * 60,
            'package_bucket': installation_info.get('PackageBucket'),
            'package_key': installation_info.get('PackageKey')
        }
        self.id = definition.get('ID')
        self.name = self.id
        self.tags = definition.get('Tags', [])
        self.deployment_id = self._extract_tag_with_prefix('deployment_id:')
        self.slice = self._extract_tag_with_prefix('slice:')
        self.port = 0
        self.portsConfig = definition.get('Ports', {'blue':0, 'green':0})
        self.version = self._extract_tag_with_prefix('version:')
        self._validate()

    def __eq__(self, other):
        return self.id == other.id and self.deployment_id == other.deployment_id

    def __str__(self):
        return json.dumps(
            {'id': self.id, 'name': self.name, 'port': self.port,
             'slice': self.slice, 'version': self.version, 'tags': self.tags})

    def _get_port(self, port_config, slice):
        logging.debug('Getting {0} port from {1}'.format(slice, port_config))

        if port_config is None:
            return 0
        if slice is None or slice.lower() == 'none':
            return 0
        return port_config.get(slice.lower(), 0)

    def _extract_tag_with_prefix(self, prefix):
        tag = next((tag for tag in self.tags if tag.startswith(prefix)), None)
        if tag is not None:
            return tag[len(prefix):]
        return None

    def _validate(self):
        if self.address is None:
            raise ValueError('Service address must be specified.')
        if self.id is None:
            raise ValueError('Service ID must be specified.')
        if self.name is None:
            raise ValueError('Service name must be specified.')

    def tag(self, prefix, value):
        self.tags = [tag for tag in self.tags if not tag.startswith(prefix)]
        self.tags.append('{0}{1}'.format(prefix, value))
