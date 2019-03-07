#!/usr/bin/env bash

set -xe

set -o allexport
echo "Sourcing environment and configuration"
source $DEPLOYMENT_BASE_DIR/environment.env
printenv
set +o allexport

if systemctl is-active $TTL_SERVICE_NAME_WITH_SLICE | grep "^active$"; then
  systemctl stop $TTL_SERVICE_NAME_WITH_SLICE
fi

