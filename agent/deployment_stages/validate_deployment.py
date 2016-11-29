# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.
from common import *

class ValidateDeployment(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='ValidateDeployment')
    def _run(self, deployment):
        if deployment.number_of_attempts < deployment.max_number_of_attempts:
            deployment.number_of_attempts += 1
        else:
            raise DeploymentError('Maximum number of attempts ({0}) has been reached.'.format(deployment.max_number_of_attempts))
