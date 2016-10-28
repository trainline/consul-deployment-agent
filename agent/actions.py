import json

class Action(object):
    def __init__(self, deployment_id, service):
        self.deployment_id = deployment_id
        self.service = service
    def __str__(self):
        return json.dumps({ 'deployment_id': self.deployment_id, 'type': type(self).__name__, 'service': str(self.service) })

class InstallAction(Action):
    def __init__(self, deployment_id, service):
        Action.__init__(self, deployment_id, service)

class UninstallAction(Action):
    def __init__(self, deployment_id, service):
        Action.__init__(self, deployment_id, service)