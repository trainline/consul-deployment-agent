#!/usr/bin/env bash

set -xe

. $DEPLOYMENT_BASE_DIR/code-deploy/environment.sh

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

copy_certificates() {
  echo "Copying certificates" >&2

  local SRC_FILE=$TTL_INSTALL_SRC_DIR/certificate.pfx
  local TARGET_FILE=/etc/$TTL_SERVICE_NAME.pfx

  cp -f $SRC_FILE $TARGET_FILE
  chmod 644 $TARGET_FILE
  chown root.root $TARGET_FILE
}

create_systemd_unit_file() {
  echo "Creating systemd unit file" >&2

  local SRC_FILE=$TTL_INSTALL_SRC_DIR/misc/service.service
  local TARGET_FILE=/lib/systemd/system/$TTL_SERVICE_NAME_WITH_SLICE.service
  
  cp -f $SRC_FILE $TARGET_FILE
  chmod 644 $TARGET_FILE
  chown root.root $TARGET_FILE
  replace_env_vars $TARGET_FILE
}

copy_source_files() {
  echo "Copying source files" >&2

  local SRC_DIR=$TTL_INSTALL_SRC_DIR
  local TARGET_DIR=/opt/$TTL_SERVICE_NAME_WITH_SLICE

  echo $SRC_DIR
  echo $TARGET_DIR
  
  rm -rf $TARGET_DIR
  mkdir $TARGET_DIR
  cp -rf $SRC_DIR/* $TARGET_DIR
  chmod +x $TARGET_DIR/code-deploy/*.sh
  find $TARGET_DIR/healthchecks -name "*.sh" -exec chmod +xr {} \;
}

create_environment_file() {
  echo "Creating config file" >&2

  local SRC_FILE=$TTL_INSTALL_SRC_DIR/misc/service.env
  local TARGET_FILE=/etc/$TTL_SERVICE_NAME_WITH_SLICE.env
  
  cp -f $SRC_FILE $TARGET_FILE
  find $TTL_INSTALL_SRC_DIR -name '*.env' ! -name 'service.env' -exec cat {} \; >> /etc/$TTL_SERVICE_NAME_WITH_SLICE.env
  chmod 644 $TARGET_FILE
  chown root.root $TARGET_FILE
  replace_env_vars $TARGET_FILE
}

copy_certificates
copy_source_files
create_environment_file
create_systemd_unit_file
replace_env_vars $TTL_INSTALL_SRC_DIR/healthchecks/consul/healthchecks.yml
replace_env_vars $TTL_INSTALL_SRC_DIR/healthchecks/consul/validate-service.sh
replace_env_vars $TTL_INSTALL_SRC_DIR/healthchecks/sensu/healthchecks.yml
replace_env_vars $TTL_INSTALL_SRC_DIR/healthchecks/sensu/validate-service.sh

cd /opt/$TTL_SERVICE_NAME_WITH_SLICE
echo "Allowing execution of $TTL_SERVICE_NAME start script" >&2
chmod a+x /opt/$TTL_SERVICE_NAME_WITH_SLICE/$TTL_SERVICE_EXE
