# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.
from common import *

class DeregisterOldSensuHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DeregisterOldSensuHealthChecks')
    def _run(self, deployment):
        raise 'not implemented'

class RegisterSensuHealthChecks(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='RegisterSensuHealthChecks')
    def _run(self, deployment):
        raise 'not implemented'
