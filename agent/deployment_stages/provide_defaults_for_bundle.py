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
            deployment.logger.info('Defaults directory: ' + deployment.base_dir)
            skel_dir = os.path.join(deployment.base_dir, skel, app_spec_os)

            deployment.logger.info('Skeleton Directory: ' + skel_dir)

            shutil.copy(os.path.join(skel_dir, 'appspec.yml'),
                        deployment.archive_dir)

            if not os.path.exists(os.path.join(deployment.archive_dir, 'code-deploy')):
                os.makedirs(os.path.join(
                    deployment.archive_dir, 'code-deploy'))

            code_deploy_scripts = os.listdir(
                os.path.join(skel_dir, 'code-deploy'))
            for f in code_deploy_scripts:
                shutil.copy(f, os.path.join(
                    deployment.archive_dir, 'code-deploy'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'healthchecks')):
                os.makedirs(os.path.join(
                    deployment.archive_dir, 'healthchecks'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'healthchecks', 'sensu')):
                os.makedirs(os.path.join(
                    deployment.archive_dir, 'healthchecks', 'sensu'))

            sensu_health_checks = os.listdir(os.path.join(
                skel_dir, 'healthchecks', 'sensu'))
            for f in sensu_health_checks:
                shutil.copy(f, os.path.join(
                    deployment.archive_dir, 'healthchecks', 'sensu'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'healthchecks', 'consul')):
                os.makedirs(os.path.join(
                    deployment.archive_dir, 'healthchecks', 'consul'))

            consul_health_checks = os.listdir(os.path.join(
                skel_dir, 'healthchecks', 'consul'))
            for f in consul_health_checks:
                shutil.copy(f, os.path.join(
                    deployment.archive_dir, 'healthchecks', 'consul'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'misc')):
                os.makedirs(os.path.join(deployment.archive_dir, 'misc'))

            misc_files = os.listdir(os.path.join(
                skel_dir, 'misc'))
            for f in misc_files:
                shutil.copy(f, os.path.join(deployment.archive_dir, 'misc'))
