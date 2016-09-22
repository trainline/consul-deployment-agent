# Copyright (c) Trainline Limited. All rights reserved. See LICENSE.txt in the project root for license information.

import json, logging

class ServerRole:
    def __init__(self, id):
        self.id = id
        self.quarantine = []
        self.services = {}

    def __str__(self):
        return json.dumps(
            {'id':self.id,
             'services':[str(s) for s in self.services.values()],
             'quarantine':self.quarantine})

    def find_missing_service(self, registered_services):
        for deployment_id, service in self.services.iteritems():
            installed_service = next((s for s in registered_services if s.deployment_id == deployment_id), None)
            if installed_service is None:
                installed_service = next((s for s in registered_services if s.id == service.id), None)
                if installed_service is None:
                    missing_service_info = (service, {'deployment_id':deployment_id, 'last_deployment_id':None})
                else:
                    missing_service_info = (service, {'deployment_id':deployment_id, 'last_deployment_id':installed_service.deployment_id})
                if deployment_id not in self.quarantine:
                    return missing_service_info
                else:
                    logging.warn('Following service deployment is quarantined, skipping deployment.')
                    logging.warn(service)
        logging.info('No missing service.')
        return None

    def quarantine_deployment(self, deployment_id):
        logging.info('Quarantining deployment with ID: %s' % deployment_id)
        self.quarantine.append(deployment_id)
