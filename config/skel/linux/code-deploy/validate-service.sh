#!/usr/bin/env bash

set -xe

. $DEPLOYMENT_BASE_DIR/code-deploy/environment.sh

echo "Verifying the installation"

url="https://127.0.0.1:$TTL_SERVICE_PORT/diagnostics/healthcheck"
echo "Service URL=$url"

max_retries=20
retries=0

while [[ $retries -lt $max_retries ]]
do
	if curl -ik $url | grep "OK"; then
		echo "Success!"
 		exit 0
	fi
	sleep 4
	((retries++))
done

echo "max retries ($max_retries) reached, installation check failed"
exit 1

