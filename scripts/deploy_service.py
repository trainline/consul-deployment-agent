#!/usr/bin/env python

import argparse
import consulate
import json
import sys
import uuid

class Options(object):
    pass

options = Options()

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', required=True, help='service name')
parser.add_argument('-p', '--port', required=True, help='port number')
parser.add_argument('-v', '--version', required=True, help='version to deploy')
parser.add_argument('-r', '--role', default='test', help='server role name')
parser.add_argument('-e', '--environment', default='local', help='environment name')
parser.add_argument('-t', '--environmenttype', required=True, help='environment type')
parser.add_argument('-c', '--cluster', required=True, help='owning cluster')
parser.add_argument('-s', '--slice', help='slice')
parser.add_argument('-d', '--deploymentid', help='deployment unique identifier')
parser.add_argument('-b', '--bucket', required=True, help='AWS S3 bucket for deployment package')
parser.add_argument('-k', '--key', required=True, help='AWS S3 key for deployment package')

args = parser.parse_args(namespace=options)

if args.deploymentid is None:
    args.deploymentid = str(uuid.uuid4())

if args.slice is None:
    service_id = args.name
    args.slice = 'none'
else:
    service_id = '{0}-{1}'.format(args.name, args.slice)

print('[Initiating deployment]')
print('  Service: %s' % args.name)
print('  Port: %s' % args.port)
print('  Version: %s' % args.version)
print('  Role: %s' % args.role)
print('  Environment: %s' % args.environment)
print('  EnvironmentType: %s' % args.environmenttype)
print('  OwningCluster: %s' % args.cluster)
print('  Slice: %s' % args.slice)
print('  DeploymentId: %s' % args.deploymentid)
print('  ServiceId: %s' % service_id)
print('  PackageBucket: %s' % args.bucket)
print('  PackageKey: %s' % args.key)

consul_session = consulate.Consul()

service_key = 'environments/{0}/services/{1}/{2}'.format(args.environment, args.name, args.version)

service_definition_key = '%s/definition' % service_key
service_definition = {}
service_definition['Service'] = {}
service_definition['Service']['ID'] = service_id
service_definition['Service']['Name'] = args.name
service_definition['Service']['Port'] = int(args.port)
service_definition['Service']['Tags'] = [ 'environment_type:%s' % args.environmenttype, 'environment:%s' % args.environment, 'owning_cluster:%s' % args.cluster, 'version:%s' % args.version ]
print('Writing service definition: %s' % json.dumps(service_definition))
print('To key: %s' % service_definition_key)
consul_session.kv[service_definition_key] = service_definition

service_installation_key = '%s/installation' % service_key
service_installation = {}
service_installation['PackageBucket'] = args.bucket
service_installation['PackageKey'] = args.key
service_installation['InstallationTimeout'] = 5
print('Writing service installation: %s' % json.dumps(service_installation))
print('To key: %s' % service_installation_key)
consul_session.kv[service_installation_key] = service_installation

if args.slice is None:
    deployment_key = 'environments/{0}/roles/{1}/services/{2}'.format(args.environment, args.role, args.name)
else:
    deployment_key = 'environments/{0}/roles/{1}/services/{2}/{3}'.format(args.environment, args.role, args.name, args.slice)
deployment = {}
deployment['Name'] = args.name
deployment['Version'] = args.version
deployment['DeploymentId'] = args.deploymentid
deployment['InstanceIds'] = []
deployment['Slice'] = args.slice
print('Writing deployment details: %s' % json.dumps(deployment))
print('To key: %s' % deployment_key)
consul_session.kv[deployment_key] = deployment

deployment_key = 'deployments/{1}'.format(args.environment, args.deploymentid)
deployment_service_key = '{0}/service'.format(deployment_key)
deployment_service = {}
deployment_service['Name'] = args.name
deployment_service['Version'] = args.version
deployment_service['Environment'] = args.environment
print('Writing deployment service: %s' % json.dumps(deployment_service))
print('To key: %s' % deployment_service_key)
consul_session.kv[deployment_service_key] = deployment_service
deployment_overall_status_key = '{0}/overall_status'.format(deployment_key)
consul_session.kv[deployment_overall_status_key] = 'In Progress'

print('Deployment triggered.')
