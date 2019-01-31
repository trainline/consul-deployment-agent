#!/usr/bin/env bash

set -xe

. $DEPLOYMENT_BASE_DIR/code-deploy/environment.sh

if systemctl is-active $TTL_SERVICE_NAME_WITH_SLICE | grep "^active$"; then
  systemctl stop $TTL_SERVICE_NAME_WITH_SLICE
fi

