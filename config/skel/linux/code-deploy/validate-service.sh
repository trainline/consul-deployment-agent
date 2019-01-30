#!/usr/bin/env bash

set +e

echo "Verifying the installation"

url="http://127.0.0.1:40665/api/diagnostics/healthcheck"
echo "Service URL=$url"

max_retries=20
retries=0

while [[ $retries -lt $max_retries ]]
do
	if curl -i $url | grep "OK"; then
		echo "Success!"
 		exit 0
	fi
	sleep 2
	((retries++))
done

echo "max retries ($max_retries) reached, installation check failed"
exit 1
