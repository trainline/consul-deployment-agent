#!/usr/bin/env python

import argparse
import consulate
import sys

class Options(object):
    pass

options = Options()

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', required=True, help='service name')
parser.add_argument('-s', '--slice', help='slice name (optional)')
parser.add_argument('-r', '--role', required=True, help='server role name')
parser.add_argument('-e', '--environment', required=True, help='environment name')

args = parser.parse_args(namespace=options)

print('[Initiating service removal]')
print('  Service: %s' % args.name)
print('  Slice: %s' % args.slice)
print('  Role: %s' % args.role)
print('  Environment: %s' % args.environment)

consul_session = consulate.Consul()

if args.slice is None:
    deployment_key = 'enviroments/{0}/roles/{1}/services/{2}'.format(args.environment, args.role, args.name)
else:
    deployment_key = 'enviroments/{0}/roles/{1}/services/{2}/{3}'.format(args.environment, args.role, args.name, args.slice)
del consul_session.kv[deployment_key]

print('Service removal triggered.')
