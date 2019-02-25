#!/usr/bin/env bash

set -xe

set -o allexport
echo "Sourcing environment and configuration"
source $DEPLOYMENT_BASE_DIR/code-deploy/environment.sh
printenv
set +o allexport

replace_env_vars() {
  local TARGET_FILE=$1
  sed -i "s/{{TTL_SERVICE_EXE}}/${TTL_SERVICE_EXE}/g" $TARGET_FILE
  sed -i "s/{{TTL_IAM_ROLE}}/${TTL_IAM_ROLE}/g" $TARGET_FILE
  sed -i "s/{{TTL_SERVICE_PORT}}/${TTL_SERVICE_PORT}/g" $TARGET_FILE
  sed -i "s/{{TTL_SERVICE_SLICE}}/${TTL_SERVICE_SLICE}/g" $TARGET_FILE
  sed -i "s/{{TTL_SERVICE_VERSION}}/${TTL_SERVICE_VERSION}/g" $TARGET_FILE
  sed -i "s/{{TTL_SERVICE_CONSUL_NAME}}/${TTL_SERVICE_CONSUL_NAME}/g" $TARGET_FILE
  sed -i "s/{{TTL_SERVICE_NAME}}/${TTL_SERVICE_NAME}/g" $TARGET_FILE
  sed -i "s/{{TTL_SERVICE_NAME_WITH_SLICE}}/${TTL_SERVICE_NAME_WITH_SLICE}/g" $TARGET_FILE
  sed -i "s/{{TTL_INSTANCE_ID}}/${TTL_INSTANCE_ID}/g" $TARGET_FILE
  sed -i "s/{{TTL_ENVIRONMENT}}/${TTL_ENVIRONMENT}/g" $TARGET_FILE
  sed -i "s/{{TTL_ENVIRONMENT_TYPE}}/${TTL_ENVIRONMENT_TYPE}/g" $TARGET_FILE
}

create_environment_file() {
  echo "Creating config file" >&2

  local TARGET_FILE="${TTL_INSTALL_SRC_DIR}/environment.env"
  cat "${TTL_INSTALL_SRC_DIR}/misc/service.env" > "${TARGET_FILE}"

  if [ -f "${TTL_INSTALL_SRC_DIR}/configuration.env" ]; then
    echo >> "${TTL_INSTALL_SRC_DIR}/configuration.env"
    cat "${TTL_INSTALL_SRC_DIR}/configuration.env" >> "${TARGET_FILE}"
  fi

  chmod 644 $TARGET_FILE
  chown root.root $TARGET_FILE
  replace_env_vars $TARGET_FILE
}

create_environment_file