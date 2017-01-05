# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

from common import *

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