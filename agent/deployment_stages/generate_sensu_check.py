# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

def generate_sensu_check(check_name=None,
                         command=None,
                         handlers=['default'],
                         interval=120,
                         ocurrences=5,
                         refresh=300,
                         subscribers=['sensu-base'],
                         standalone=True,
                         timeout=120,
                         aggregate=False,
                         alert_after=600,
                         realert_every=30,
                         runbook='Needs information',
                         sla='No SLA defined',
                         team=None,
                         notification_email=None,
                         ticket=False,
                         project=False,
                         slack=False,
                         page=False,
                         tip='Fill me up with information',
                         tags=[],
                         **kwargs):
    """ Generates a valid json for a sensu check """
    # Checks validity of input
    if check_name is None:
        raise SyntaxError('Cannot create sensu check without a name')
    if command is None:
        raise SyntaxError('Need a valid command to create sensu check')
    if team is None:
        raise SyntaxError('Need to specify a valid team to assign events from this sensu check')
    content = {'checks':{check_name:{'command': command,
                                     'handlers': handlers,
                                     'interval': interval,
                                     'ocurrences': ocurrences,
                                     'refresh': refresh,
                                     'subscribers': subscribers,
                                     'standalone': standalone,
                                     'timeout': timeout,
                                     'aggregate': aggregate,
                                     'alert_after': alert_after,
                                     'realert_every': realert_every,
                                     'runbook': runbook,
                                     'sla': sla,
                                     'team': team,
                                     'notification_email': notification_email,
                                     'ticket': ticket,
                                     'project': project,
                                     'slack': slack,
                                     'page': page,
                                     'tip': tip,
                                     'tags': tags}}}
    for key, value in kwargs.iteritems():
        content.update({key: value})
    return json_encode(content)