# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See
# LICENSE.txt in the project root for license information.


from envmgr_healthchecks.health_checks.consul_health_check import ConsulHealthCheck
from .common import DeploymentStage


class DeregisterOldConsulHealthChecks(DeploymentStage):
    """
    CDA Deployment Stage _run health check wrapper for deregistering.
    """

    def __init__(self):
        DeploymentStage.__init__(self, name='DeregisterOldConsulHealthChecks')

    def _run(self, deployment):
        health_check = build_health_check(self.name, deployment)
        health_check.register()


class RegisterConsulHealthChecks(DeploymentStage):
    """
    CDA Deployment Stage _run health check wrapper for registering.
    """

    def __init__(self):
        DeploymentStage.__init__(self, name='RegisterConsulHealthChecks')

    def _run(self, deployment):
        health_check = build_health_check(self.name, deployment)
        health_check.deregister()


def build_health_check(name, deployment):
    """
    Take the required values from a health check registration for
    Consul Health Checks and pass them on to the contructor.
    """
    health_check = ConsulHealthCheck(
        name=name,
        logger=getattr(deployment, 'logger', None),
        archive_dir=getattr(deployment, 'archive_dir', None),
        appspec=getattr(deployment, 'appspec', None),
        service_slice=getattr(
            getattr(deployment, 'service', None), 'slice', None),
        service_id=getattr(getattr(deployment, 'service', None), 'id', None),
        api=getattr(deployment, 'consul_api', None),
        last_id=getattr(deployment, 'last_id', None),
        last_archive_dir=getattr(deployment, 'last_archive_dir', None)
    )
    return health_check
