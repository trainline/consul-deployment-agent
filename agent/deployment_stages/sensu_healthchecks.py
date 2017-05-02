# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See
# LICENSE.txt in the project root for license information.


from envmgr_healthchecks.health_checks.sensu_heath_check import SensuHealthCheck
from .common import DeploymentStage


class DeregisterOldSensuHealthChecks(DeploymentStage):
    """
    CDA Deployment Stage _run health check wrapper for deregistering.
    """

    def __init__(self):
        DeploymentStage.__init__(self, name='DeregisterOldSensuHealthChecks')

    def _run(self, deployment):
        health_check = build_health_check(self.name, deployment)
        health_check.deregister()


class RegisterSensuHealthChecks(DeploymentStage):
    """
    CDA Deployment Stage _run health check wrapper for registering.
    """

    def __init__(self):
        DeploymentStage.__init__(self, name='RegisterSensuHealthChecks')

    def _run(self, deployment):
        health_check = build_health_check(self.name, deployment)
        health_check.register()


def build_health_check(name, deployment):
    """
    Take the required values from a health check registration for
    Sensu Health Checks and pass them on to the contructor.
    """
    health_check = SensuHealthCheck(
        name=name,
        platform=getattr(deployment, 'platform', None),
        instance_tags=getattr(deployment, 'instance_tags', None),
        logger=getattr(deployment, 'logger', None),
        sensu=getattr(deployment, 'sensu', None),
        service_id=getattr(
            getattr(deployment, 'service', None), 'id', None),
        service_slice=getattr(
            getattr(deployment, 'service', None), 'slice', None),
        last_id=getattr(deployment, 'last_id', None),
        last_archive_dir=getattr(deployment, 'last_archive_dir', None),
        archive_dir=getattr(deployment, 'archive_dir', None),
        appspec=getattr(deployment, 'appspec', None)
    )
    return health_check
