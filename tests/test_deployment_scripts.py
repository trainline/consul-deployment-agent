# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

from os import linesep, path
from platform import system
from string import rsplit
from unittest import TestCase
from mock import MagicMock
from agent.deployment_stages.deployment_scripts import PowershellScript, ShellScript

CREATE_SCRIPT = PowershellScript if system() == 'Windows' else ShellScript
SCRIPT_EXT = '.ps1' if system() == 'Windows' else '.sh'

def with_script_ext(filename):
    return filename + SCRIPT_EXT

def relative(filename):
    fullpath = path.join(path.dirname(__file__), filename)
    print(fullpath)
    return fullpath

def from_file(filename):
    return relative(with_script_ext(filename))

class TestDeploymentScripts(TestCase):

    def test_returns_partial_output_after_timeout(self):
        script = CREATE_SCRIPT(from_file('test_deployment_scripts'), timeout=2)
        logger = MagicMock()
        exit_code, stdout = script.execute(logger)
        self.assertNotEqual(exit_code, 0)
        self.assertEqual(stdout, 'Started' + linesep)

    def test_returns_full_output_after_completion(self):
        script = CREATE_SCRIPT(from_file('test_deployment_scripts'), timeout=5)
        logger = MagicMock()
        exit_code, stdout = script.execute(logger)
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, 'Started' + linesep + 'Finished' + linesep)

    def test_returns_big_output(self):
        script = CREATE_SCRIPT(from_file('test_deployment_scripts_big_output'), timeout=10)
        logger = MagicMock()
        result = script.execute(logger)
        _, stdout = result
        [_, last] = rsplit(stdout, maxsplit=1)
        self.assertEqual(last, 'Finished')

