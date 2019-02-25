# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import os, zipfile
from .common import DeploymentError, DeploymentStage

class DownloadBundleFromS3(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='DownloadBundleFromS3')
    def _run(self, deployment):
        deployment.logger.debug('Creating {0} directory for bundle.'.format(deployment.archive_dir))
        if not os.path.exists(deployment.archive_dir):
            os.makedirs(deployment.archive_dir)

        package_bucket = deployment.service.installation['package_bucket']
        package_key = deployment.service.installation['package_key']
        bundle_filepath = os.path.join(deployment.dir, 'bundle.zip')
        deployment.logger.debug('Downloading bundle from S3 bucket \'{0}\' with key \'{1}\' to {2}.'.format(package_bucket, package_key, bundle_filepath))
        if not deployment.s3_file_manager.download_file(package_bucket, package_key, bundle_filepath):
            raise DeploymentError('Failed to download bundle from S3 bucket \'{0}\' with key \'{1}\' to {2}.'.format(package_bucket, package_key, bundle_filepath))

        deployment.logger.debug('Extracting {0} to {1}.'.format(bundle_filepath, deployment.archive_dir))
        bundle_fh = open(bundle_filepath, 'rb')
        z = zipfile.ZipFile(bundle_fh)
        for name in z.namelist():
            z.extract(name, deployment.archive_dir)
        bundle_fh.close()
        deployment.logger.info('Bundle downloaded and extracted to {0}.'.format(deployment.archive_dir))

        package_config_key = 'CONFIGURATION/{0}.config'.format(deployment.id)
        package_config_path = os.path.join(deployment.archive_dir, 'configuration.env')
        if deployment.s3_file_manager.download_file(package_bucket, package_config_key, package_config_path):
            deployment.logger.info('Found configuration, downloaded from {0}/{1} to {2}'.format(package_bucket, package_config_key, package_config_path))
