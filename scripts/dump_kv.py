#!/usr/bin/env python

import consulate

consul_session = consulate.Consul()

for key, value in consul_session.kv.iteritems():
    print('key: %s' % key)
    print('value: %s' % value)
