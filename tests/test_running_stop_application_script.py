# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from agent.deployment import run_stages


class TestStopApplicationStageIsCalledInEventOfFailure(unittest.TestCase):
    def setUp(self):
        self.sut = run_stages
        self.stop_application = StopApplication()

    def test_stop_is_run_when_EARLIER_stage_fails(self):
        self.sut([GoesBang(), self.stop_application],
                 object(), Reporter().method, Logger())

        self.assertTrue(self.stop_application.verify())
        self.assertEquals(self.stop_application.executed_count, 1)

    def test_stop_is_run_when_LATER_stage_fails(self):
        self.stop_application = StopApplication(2)
        self.sut([Works(), self.stop_application, GoesBang()],
                 object(), Reporter().method, Logger())

        self.assertTrue(self.stop_application.verify())

    def test_when_nothing_fails_stop_stage_is_run(self):
        self.sut([Works(), Works(), Works(), self.stop_application, Works(), Works()],
                 object(), Reporter().method, Logger())

        self.assertTrue(self.stop_application.verify())
        self.assertEquals(self.stop_application.executed_count, 1)


###########
# HELPERS #
###########

class GoesBang():
    def __init__(self):
        self.name = "failing"

    def run(self, deployment):
        return False


class Works():
    def __init__(self):
        self.name = "working"

    def run(self, deployment):
        return True


class StopApplication():
    def __init__(self, execution_count_expectation=1):
        self.name = "StopApplication"
        self.has_run = False
        self.execution_count_expectation = execution_count_expectation
        self.executed_count = 0

    def run(self, deployment):
        self.executed_count = self.executed_count + 1
        self.has_run = True
        return True

    def verify(self):
        print self.has_run
        print self.executed_count
        if self.has_run == True and self.executed_count == self.execution_count_expectation:
            return True
        else:
            return False


class Logger():
    def error(self, string):
        pass

    def info(self, string):
        pass


class Reporter():
    def method(self, string):
        pass
