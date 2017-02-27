# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import distutils.core, os
from .common import DeploymentStage

class CopyFiles(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='CopyFiles')
    def _run(self, deployment):
        def clean_up(files, logger):
            for file in files:
                if os.path.isdir(file['destination']):
                    deployment.logger.debug('Destination {0} already exists, cleaning up first.'.format(file['destination']))
                    distutils.dir_util.remove_tree(file['destination'])
        def copy_files(files, logger):
            for file in deployment.appspec.get('files', []):
                if file['source'].startswith('/'):
                    source = os.path.join(deployment.archive_dir, file['source'][1:])
                else:
                    source = os.path.join(deployment.archive_dir, file['source'])
                if os.path.isdir(source):
                    deployment.logger.debug('Moving content of {0} directory recursively to {1}.'.format(source, file['destination']))
                    distutils.dir_util.copy_tree(source, file['destination'])
                else:
                    if not os.path.isdir(file['destination']):
                        deployment.logger.debug('Creating missing directory {0}.'.format(file['destination']))
                        distutils.dir_util.mkpath(file['destination'])
                    deployment.logger.debug('Moving file {0} to {1}.'.format(source, file['destination']))
                    distutils.file_util.copy_file(source, file['destination'])
        if 'files' not in deployment.appspec:
            deployment.logger.info('Skipping CopyFiles stage as there are no file operations defined in appspec.yml.')
            return
        clean_up(deployment.appspec.get('files', []), deployment.logger)
        copy_files(deployment.appspec.get('files', []), deployment.logger)
        