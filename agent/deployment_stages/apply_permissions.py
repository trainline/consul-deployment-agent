# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

from common import *

import dir_utils

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
                    