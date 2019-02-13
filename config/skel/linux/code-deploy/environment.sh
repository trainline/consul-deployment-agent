#!/usr/bin/env bash

# source $(pwd)/code-deploy/environment.props

export TTL_INSTALL_SRC_DIR=$DEPLOYMENT_BASE_DIR

if [ -f "${TTL_INSTALL_SRC_DIR}/config/defaults.env" ]; then
  echo "Found defaults.env!!!!"
  source "${TTL_INSTALL_SRC_DIR}/config/defaults.env"
fi

if [ -f "${TTL_INSTALL_SRC_DIR}/config/${TTL_ENVIRONMENT_TYPE}.env" ]; then
  echo "Found ${TTL_ENVIRONMENT_TYPE}.env!!!!"
  source "${TTL_INSTALL_SRC_DIR}/config/${TTL_ENVIRONMENT_TYPE}.env"
fi

if [ -f "${TTL_INSTALL_SRC_DIR}/config/${TTL_ENVIRONMENT}.env" ]; then
  echo "Found ${TTL_ENVIRONMENT}.env!!!!"
  source "${TTL_INSTALL_SRC_DIR}/config/${TTL_ENVIRONMENT}.env"
fi
  
export TTL_IAM_ROLE=$TTL_ROLE
export TTL_SERVICE_PORT=$EM_SERVICE_PORT
export TTL_SERVICE_SLICE=$EM_SERVICE_SLICE
export TTL_SERVICE_VERSION=$EM_SERVICE_VERSION
export TTL_SERVICE_CONSUL_NAME=$EM_SERVICE_NAME

IFS='-' read -ra SERVICE_NAME_PARTS <<< $EM_SERVICE_NAME
export TTL_SERVICE_NAME=${SERVICE_NAME_PARTS[1]}

if [ "$TTL_SERVICE_SLICE" == "none" ]; then
  export TTL_SERVICE_NAME_WITH_SLICE=$(echo "$TTL_SERVICE_NAME" | tr '[:upper:]' '[:lower:]')
else
  export TTL_SERVICE_NAME_WITH_SLICE=$(echo "$TTL_SERVICE_NAME-$TTL_SERVICE_SLICE" | tr '[:upper:]' '[:lower:]')
fi

export TTL_DEPLOYMENT_ID=$DEPLOYMENT_ID
export TTL_INSTANCE_ID=$EC2_INSTANCE_ID
