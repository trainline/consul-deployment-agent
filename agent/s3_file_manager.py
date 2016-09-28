# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import logging, sys
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from retrying import retry

class S3FileManager:
    def __init__(self, config):
        if config is None:
            self._access_key_id = self._aws_secret_access_key = None
        else:
            self._access_key_id = config.get('access_key_id')
            self._aws_secret_access_key = config.get('aws_secret_access_key')
        self._s3_connection = None

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _download_file(self, bucket_name, key, output_path):
        if self._s3_connection is None:
            self._init_connection()
        s3_bucket = self._s3_connection.get_bucket(bucket_name)
        s3_key = s3_bucket.get_key(key)
        s3_key.get_contents_to_filename(output_path)

    def _init_connection(self):
        self._s3_connection = S3Connection(aws_access_key_id=self._access_key_id, aws_secret_access_key=self._aws_secret_access_key)

    @retry(wait_fixed=5000, stop_max_attempt_number=3)
    def _upload_file(self, bucket_name, key, filepath):
        if self._s3_connection is None:
            self._init_connection()
        s3_bucket = self._s3_connection.get_bucket(bucket_name)
        s3_key = Key(s3_bucket)
        s3_key.key = key
        s3_key.set_contents_from_filename(filepath)
        return s3_key.generate_url(expires_in=0, query_auth=False)

    def download_file(self, bucket_name, key, output_path):
        try:
            self._download_file(bucket_name, key, output_path)
            return True
        except:
            logging.error('Failed to download file from S3.')
            logging.exception(sys.exc_info()[1])
            return False

    def upload_file(self, bucket_name, key, filepath):
        try:
            return self._upload_file(bucket_name, key, filepath)
        except:
            logging.error('Failed to upload file to S3.')
            logging.exception(sys.exc_info()[1])
            return None
