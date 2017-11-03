# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import shutil
from os import stat
from agent.find_deployment import find_deployment_dirs
from agent.retention_policy import get_directories_to_delete
from .common import DeploymentStage

class DeletePreviousDeploymentFiles(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DeletePreviousDeploymentFiles')
    def _run(self, deployment):
        all_deployment_dirs = find_deployment_dirs(deployment.base_dir, deployment.service.id)
        # Protect the current and previous deployment directories
        directories_to_delete = get_directories_to_delete(deployment, [(d, stat(d)) for d in all_deployment_dirs], retain=2)
        for deployment_dir in directories_to_delete:
            try:
                deployment.logger.info('Deleting {0}.'.format(deployment_dir))
                shutil.rmtree(deployment_dir)
            except Exception:
                deployment.logger.exception('Failed to delete {0}'.format(deployment_dir))


