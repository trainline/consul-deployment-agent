# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import os, zipfile, shutil
from .common import DeploymentError, DeploymentStage

class ProvideDefaultsForBundle(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='ProvideDefaultsForBundle')
    def _run(self, deployment):
        deployment.logger.debug('Checking whether bundle requires default code deploy scripts')
        if not os.path.exists(deployment.archive_dir):
            os.makedirs(deployment.archive_dir)
        appspec_stream = file(os.path.join(deployment.archive_dir, 'appspec.yml'), 'r')
        if deployment.appspec.get('hooks', {}) is None:
            # Move the skeleton appspec file to the deployment
            shutil.copy(os.path.join('skel', deployment.appspec.get('os'), 'appspec.yml'), deployment.archive_dir)
            # Move the code deploy files to the archive dir
            if not os.path.exists(os.path.join(deployment.archive_dir, 'code-deploy')):
                os.makedirs(os.path.join(deployment.archive_dir, 'code-deploy'))
            
            code_deploy_scripts = os.listdir(os.path.join('skel', deployment.appspec.get('os'), 'code-deploy'))
            for f in code_deploy_scripts:
                shutil.copy(f, os.path.join(deployment.archive_dir, 'code-deploy'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'healthchecks')):
                os.makedirs(os.path.join(deployment.archive_dir, 'healthchecks'))
            
            if not os.path.exists(os.path.join(deployment.archive_dir, 'healthchecks', 'sensu')):
                os.makedirs(os.path.join(deployment.archive_dir, 'healthchecks', 'sensu'))

            sensu_health_checks = os.listdir(os.path.join('skel', deployment.appspec.get('os'), 'healthchecks', 'sensu'))
            for f in sensu_health_checks:
                shutil.copy(f, os.path.join(deployment.archive_dir, 'healthchecks', 'sensu'))
           
            if not os.path.exists(os.path.join(deployment.archive_dir, 'healthchecks', 'consul')):
                os.makedirs(os.path.join(deployment.archive_dir, 'healthchecks', 'consul'))
            
            consul_health_checks = os.listdir(os.path.join('skel', deployment.appspec.get('os'), 'healthchecks', 'consul'))
            for f in consul_health_checks:
                shutil.copy(f, os.path.join(deployment.archive_dir, 'healthchecks', 'consul'))

            if not os.path.exists(os.path.join(deployment.archive_dir, 'misc')):
                os.makedirs(os.path.join(deployment.archive_dir, 'misc'))
            
            misc_files = os.listdir(os.path.join('skel', deployment.appspec.get('os'), 'misc'))
            for f in misc_files:
                shutil.copy(f, os.path.join(deployment.archive_dir, 'misc'))

