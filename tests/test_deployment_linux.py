# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from agent.deployment import Deployment

@unittest.skip("Comment out to run manually")
class LinuxDeploymentTest(unittest.TestCase):
    def test_deployment_linux(self):
        config = {
            'service_id': 'simple-nodejs-app',
            'deployment_id':'5f696f79-ad1b-435e-9832-b95d00bc4853',
            'package_path':'/home/jeanml/git/consul-deployment-agent/tests/data/linux-package.zip',
            'timeout':'60'
        }
        deployment = Deployment(config)
        deployment.run()
