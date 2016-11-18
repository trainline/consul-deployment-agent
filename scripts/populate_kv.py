#!/usr/bin/env python
import imp, json, requests, uuid

consul_api = imp.load_source('consul_api', 'agent/consul_api.py')

api = consul_api.ConsulApi({'scheme':'http', 'host':'localhost', 'port':8500, 'version':'v1', 'acl_token':None})
print api.get_service_catalogue()


# api_base_url = 'http://localhost:8500/v1'
#
# def write_key(key, value):
#     request_url = '{0}/kv/{1}'.format(api_base_url, key)
#     print('URL: {0}'.format(request_url))
#     print('Content: {0}'.format(value))
#     response = requests.put(request_url, data=value)
#     print('Response status code: {0}'.format(response.status_code))
#     print('Response content: {0}'.format(response.text))
#
# def register_check(check):
#     request_url = '{0}/agent/check/register'.format(api_base_url)
#     print('URL: {0}'.format(request_url))
#     print('Content: {0}'.format(check))
#     response = requests.put(request_url, data=json.dumps(check))
#     print('Response status code: {0}'.format(response.status_code))
#     print('Response content: {0}'.format(response.text))
#
# def register_service(service):
#     request_url = '{0}/agent/service/register'.format(api_base_url)
#     print('URL: {0}'.format(request_url))
#     print('Content: {0}'.format(service))
#     response = requests.put(request_url, data=json.dumps(service))
#     print('Response status code: {0}'.format(response.status_code))
#     print('Response content: {0}'.format(response.text))


# register_service({
#     'ID':'service_id',
#     'Patate':'Poil',
#     'Name':'service_name',
#     'Address':'127.0.0.1',
#     'Port':80,
#     'Tags':['tag'],
#     'EnableTagOverride':False })
#
# register_check({
#     'ID':'check1',
#     'Name':'health check 1',
#     'Notes':'some crap notes',
#     'HTTP':'http://localhost:80/ping',
#     'Interval':'30s',
#     'ServiceID': 'service_id'})

# write_key('environments/local/roles/test/services/DotNetCoreTest/blue',
#     json.dumps({
#         'Name': 'DotNetCoreTest',
#         'Version': '0.1.0',
#         'Slice': 'blue',
#         'DeploymentId': str(uuid.uuid4()),
#         'InstanceIds': []
#     }))
# write_key('environments/local/services/DotNetCoreTest/0.1.0/definition',
#     json.dumps({
#         'Service': {
#             'Name': 'local-DotNetCoreTest-blue',
#             'ID': 'local-DotNetCoreTest-blue',
#             'Address': '',
#             'Port': 0,
#             'Tags': [
#                 'environment_type:Cluster',
#                 'environment:local',
#                 'owning_cluster:DietCode',
#                 'version:0.1.0'
#             ]
#         }
#     }))
# write_key('environments/local/services/DotNetCoreTest/0.1.0/installation',
#     json.dumps({
#         'PackageBucket': 'tl-deployment-sandbox',
#         'PackageKey': 'local/DotNetCoreTest/Trainline.DotNetCoreTest-0.1.0.zip',
#         'InstallationTimeout': 20
#     }))
