# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

from common import *

class StopApplication(LifecycleHookExecutionStage):
    def __init__(self):
        LifecycleHookExecutionStage.__init__(self, name='StopApplication', lifecycle_event='ApplicationStop')
    def _run(self, deployment):
        if deployment.last_id is None:
            deployment.logger.info('Skipping {0} stage as there is no previous deployment.'.format(self.name))
        else:
            appspec = get_previous_deployment_appspec(deployment)
            if appspec is None:
                deployment.logger.warning('Previous deployment directory not found, id: {0}'.format(deployment.last_id))
            else:
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