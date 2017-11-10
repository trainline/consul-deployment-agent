# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
import os
from os.path import join
import shutil
import tempfile
from agent.deployment_stages.delete_previous_deployment_files import DeletePreviousDeploymentFiles

class FakeLogger(object):
    def debug(self, *args):
        return
    def info(self, *args):
        return
    def warning(self, *args):
        return
    def error(self, *args):
        return
    def exception(self, *args):
        return

class Fake(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class TestDeletePreviousDeploymentFiles(unittest.TestCase):
    def test_it_deletes_the_expected_directories(self):
        tmpdir = tempfile.mkdtemp()
        service_id = 'A'
        try:
            deployment_dirs = [join(tmpdir, service_id, str(x)) for x in range(7)]
            for deployment_dir in deployment_dirs:
                os.makedirs(deployment_dir)
            fake_deployment = Fake(
                base_dir=tmpdir,
                dir=join(tmpdir, service_id, '2'),
                last_dir=join(tmpdir, service_id, '1'),
                logger=FakeLogger(),
                service=Fake(id=service_id))
            DeletePreviousDeploymentFiles().run(fake_deployment)
            remaining_dirs = os.listdir(os.path.join(tmpdir, service_id))
            self.assertEqual(len(remaining_dirs), 2, 'two deployments are retained')
            self.assertIn('1', remaining_dirs, 'previous deployment directory is retained')
            self.assertIn('2', remaining_dirs, 'current deployment directory is retained')
        finally:
            shutil.rmtree(tmpdir)
