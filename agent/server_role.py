# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import json, logging

class ServerRole:
    def __init__(self, id):
        self.actions = []
        self.id = id
        self.quarantine = []

    def __str__(self):
        return json.dumps(
            {'id': self.id,
             'actions': [str(s) for s in self.actions],
             'quarantine': self.quarantine })

    def find_action_to_execute(self, registered_services):
        for action in self.actions:
            if action.deployment_id in self.quarantine:
                logging.warn('Following deployment action is quarantined, skipping deployment.\n{0}'.format(action))
                continue
            deployment_id = next((s.deployment_id for s in registered_services if s.deployment_id == deployment_id), None)
            if deployment_id is None:
                # Deployment action has not been applied to this instance or was unsuccessful
                installed_service = next((s for s in registered_services if s.id == action.service.id), None)
                if installed_service is None:
                    # There is no existing deployment of the service on this instance, no need to specify last_deployment_id
                    return (action, {'last_deployment_id': None})
                else:
                    # There is an existing deployment of the service on this instance, need to specify last_deployment_id
                    return (action, {'last_deployment_id': installed_service.deployment_id})
        return None

    def quarantine_action(self, deployment_id):
        logging.info('Quarantining deployment with ID: %s' % deployment_id)
        self.quarantine.append(deployment_id)