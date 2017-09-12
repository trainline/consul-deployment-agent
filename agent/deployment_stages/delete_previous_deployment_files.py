# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import os
import shutil
from traceback import format_exception
from .common import DeploymentStage

class DeletePreviousDeploymentFiles(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DeletePreviousDeploymentFiles')
    def _run(self, deployment):
        if deployment.last_id is None:
            deployment.logger.info('Skipping {0} stage as there is no previous deployment.'.format(self.name))
        else:
            if os.path.isdir(deployment.last_dir):
                def remove_failed(function, path, excinfo):
                    err_msg = ''.join(format_exception(*excinfo, limit = 1))
                    deployment.logger.warning('Failed to delete {0}. {1}'.format(path, err_msg))
                deployment.logger.info('Deleting directory of previous deployment {0}.'.format(deployment.last_dir))
                shutil.rmtree(deployment.last_dir)
            else:
                deployment.logger.warning('The directory of last deployment doesn\'t exist {0}.'.format(deployment.last_dir))
