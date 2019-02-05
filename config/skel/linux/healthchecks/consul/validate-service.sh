#!/usr/bin/env bash

set -xe

echo "Verifying the installation"

url="https://127.0.0.1:{{TTL_SERVICE_PORT}}/diagnostics/healthcheck"
echo "Service URL=$url"

MAX_RETRIES=1000
RETRIES=0

while [[ $RETRIES -lt $MAX_RETRIES ]]; do
	if curl -ik $url | grep "OK"; then
		echo "Success!"
 		exit 0
	fi
	sleep 10
	let RETRIES=$RETRIES+1
done

echo "max retries ($MAX_RETRIES) reached, installation check failed"
exit 1
