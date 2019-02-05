#!/usr/bin/env bash

set -xe

. $DEPLOYMENT_BASE_DIR/code-deploy/environment.sh

systemctl enable $TTL_SERVICE_NAME_WITH_SLICE
systemctl start $TTL_SERVICE_NAME_WITH_SLICE

