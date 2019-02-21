#!/usr/bin/env bash

set -xe

. $DEPLOYMENT_BASE_DIR/code-deploy/environment.sh

echo "Verifying the installation, will wait 60 seconds"

url="https://127.0.0.1:$TTL_SERVICE_PORT/diagnostics/healthcheck"
echo "Service URL=$url"

MAX_RETRIES=60
RETRIES=0

while [[ $RETRIES -lt $MAX_RETRIES ]]; do
	if curl -ik $url | grep "OK"; then
		echo "Success!"
 		exit 0
	fi
	sleep 1
	let RETRIES=$RETRIES+1
done

echo "max retries ($MAX_RETRIES) reached, installation check failed"

echo "Last logs from the service:"
cat /var/log/syslog | grep "$TTL_SERVICE_NAME_WITH_SLICE\\[" | tail

exit 1
