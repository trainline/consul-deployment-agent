# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import os

class HealthCheck():
    def __init__(self, id, name):
        self.id = id
        self.name = name
    def validate(self):
        assert 0, 'validate not implemented'

class HttpCheck(HealthCheck):
    def __init__(self, id, name, url, interval):
        HealthCheck.__init__(self, id=id, name=name)
        self.interval = interval
        self.url = url
    def validate(self):
        if not self.id:
            raise ValueError('ID cannot be None or empty.')
        if not self.name:
            raise ValueError('Name cannot be None or empty.')
        if not self.url:
            raise ValueError('URL cannot be None or empty.')
        if not self.interval:
            raise ValueError('Interval cannot be None or empty.')

class ScriptCheck(HealthCheck):
    def __init__(self, id, name, script_path, interval):
        HealthCheck.__init__(self, id=id, name=name)
        self.interval = interval
        self.script_path = script_path
    def validate(self):
        if not self.id:
            raise ValueError('ID cannot be None or empty.')
        if not self.name:
            raise ValueError('Name cannot be None or empty.')
        if not self.script_path:
            raise ValueError('Script path cannot be None or empty.')
        if not os.path.isfile(self.script_path):
            raise ValueError('Script cannot be found on the given location')
        if not self.interval:
            raise ValueError('Interval cannot be None or empty.')
