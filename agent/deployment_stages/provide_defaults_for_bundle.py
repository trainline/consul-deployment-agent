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

        archive_appspec_path = os.path.join(
            deployment.archive_dir, 'appspec.yml')

        if not os.path.isfile(archive_appspec_path):
            self._provide_defaults_if_no_hooks(deployment)

    def _provide_defaults_if_no_hooks(self, deployment):
        skel = 'skel'
        app_spec_os = deployment.platform

        deployment.logger.info(
            'No hooks found in deployment. Proceeding to complete deployment with default settings.')

        skel_dir = os.path.join(deployment.cda_dir, skel, app_spec_os)

        appspec_stream = file(os.path.join(skel_dir, 'appspec.yml'), 'r')

        deployment.appspec = yaml.load(appspec_stream)

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

        shutil.copytree(skel_dir, os.path.join(deployment.archive_dir, 'defaults'))

        if not os.path.exists(os.path.join(deployment.archive_dir, 'misc')):
            os.makedirs(os.path.join(deployment.archive_dir, 'misc'))

        skel_misc = os.path.join(skel_dir, 'misc')
        skel_misc_files = os.listdir(skel_misc)
        for f in skel_misc_files:
            shutil.copy(os.path.join(skel_misc, f), os.path.join(
                deployment.archive_dir, 'misc'))
