# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

from common import *

class DeletePreviousDeploymentFiles(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DeletePreviousDeploymentFiles')
    def _run(self, deployment):
        if deployment.last_id is None:
            deployment.logger.info('Skipping {0} stage as there is no previous deployment.'.format(self.name))
        else:
            if os.path.isdir(deployment.last_archive_dir):
                deployment.logger.info('Deleting directory of previous deployment {0}.'.format(deployment.last_archive_dir))
                distutils.dir_util.remove_tree(deployment.last_archive_dir)
            else:
                deployment.logger.warning('The directory of last deployment doesn\'t exist {0}.'.format(deployment.last_archive_dir))
