#!/usr/bin/env bash

set -xe

echo "Simple Consul health check"

url="https://127.0.0.1:{{TTL_SERVICE_PORT}}/diagnostics/healthcheck"
echo "Service URL=$url"

if curl -ik $url | grep "OK"; then
	echo "Success!"
 	exit 0
fi

exit 1
