# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from agent.deployment import Deployment

@unittest.skip("Comment out to run manually")
class WindowsDeploymentTest(unittest.TestCase):
    def test_deployment_windows(self):
        config = {
            'service_id': 'CustomerService-blue',
            'deployment_id':'9bde4c44-479b-4abf-9f4e-05e604762f80',
            'package_path':'C:\\git\\consul-deployment-agent\\tests\\data\\windows-package.zip',
            'timeout':'60'
        }
        deployment = Deployment(config)
        deployment.run()
