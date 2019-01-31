# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import os
import shutil
import yaml
from .common import DeploymentStage


class ProvideDefaultsForBundle(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='ProvideDefaultsForBundle')

    def _run(self, deployment):
        deployment.logger.debug(
            'Checking whether bundle requires default code deploy scripts')
        if not os.path.exists(deployment.archive_dir):
            os.makedirs(deployment.archive_dir)
        appspec_stream = file(os.path.join(
            deployment.archive_dir, 'appspec.yml'), 'r')
        deployment.appspec = yaml.load(appspec_stream)
        self._provide_defaults_if_no_hooks(deployment)

    def _provide_defaults_if_no_hooks(self, deployment):
        if not deployment.appspec.get('hooks'):
            skel = 'skel'
            app_spec_os = deployment.appspec.get('os')
            deployment.logger.info('No hooks found in deployment. Proceeding to complete deployment with default settings.')
            skel_dir = os.path.join(deployment.skel_dir, skel, app_spec_os)

            shutil.copy(os.path.join(skel_dir, 'appspec.yml'),
                        deployment.archive_dir)

            shutil.copy(os.path.join(skel_dir, 'certificate.pfx'),
                        deployment.archive_dir)

            if not os.path.exists(os.path.join(deployment.archive_dir, 'code-deploy')):
                os.makedirs(os.path.join(
                    deployment.archive_dir, 'code-deploy'))

            skel_code_deploy = os.path.join(skel_dir, 'code-deploy')
            skel_code_deploy_scripts = os.listdir(skel_code_deploy)
            for f in skel_code_deploy_scripts:
                shutil.copy(os.path.join(skel_code_deploy, f), os.path.join(
                    deployment.archive_dir, 'code-deploy'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'healthchecks')):
                os.makedirs(os.path.join(
                    deployment.archive_dir, 'healthchecks'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'healthchecks', 'sensu')):
                os.makedirs(os.path.join(
                    deployment.archive_dir, 'healthchecks', 'sensu'))

            skel_sensu = os.path.join(skel_dir, 'healthchecks', 'sensu')
            skel_sensu_health_checks = os.listdir(skel_sensu)
            for f in skel_sensu_health_checks:
                shutil.copy(os.path.join(skel_sensu, f), os.path.join(
                    deployment.archive_dir, 'healthchecks', 'sensu'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'healthchecks', 'consul')):
                os.makedirs(os.path.join(
                    deployment.archive_dir, 'healthchecks', 'consul'))

            skel_consul = os.path.join(skel_dir, 'healthchecks', 'consul')
            skel_consul_health_checks = os.listdir(skel_consul)
            for f in skel_consul_health_checks:
                shutil.copy(os.path.join(skel_consul, f), os.path.join(
                    deployment.archive_dir, 'healthchecks', 'consul'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'misc')):
                os.makedirs(os.path.join(deployment.archive_dir, 'misc'))

            skel_misc = os.path.join(skel_dir, 'misc')
            skel_misc_files = os.listdir(skel_misc)
            for f in skel_misc_files:
                shutil.copy(os.path.join(skel_misc, f), os.path.join(
                    deployment.archive_dir, 'misc'))
