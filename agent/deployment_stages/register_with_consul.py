# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

from common import *

class RegisterWithConsul(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='RegisterWithConsul')
    def _run(self, deployment):
        deployment.logger.info('Registering service in Consul catalogue.')
        is_success = deployment.consul_api.register_service(
            id=deployment.service.id,
            name=deployment.service.id,
            address=deployment.service.address,
            port=deployment.service.port,
            tags=deployment.service.tags
        )
        if is_success:
            deployment.logger.info('Service registered in Consul catalogue.')
        else:
            deployment.logger.warning('Failed to register service in Consul catalogue.')