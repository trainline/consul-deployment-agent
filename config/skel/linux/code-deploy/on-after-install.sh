#!/usr/bin/env bash

create_systemd_unit_file() {
  echo "Creating systemd unit file" >&2

  local SRC_FILE=/tmp/test-orchestrator/misc/test-orchestrator.service
  local TARGET_FILE=/lib/systemd/system/test-orchestrator.service
  
  cp -f $SRC_FILE $TARGET_FILE
  chmod 644 $TARGET_FILE
  chown root.root $TARGET_FILE
}

copy_source_files() {
  echo "Copying source files" >&2

  local SRC_DIR=/tmp/test-orchestrator
  local TARGET_DIR=/opt/test-orchestrator
  
  rm -rf $TARGET_DIR
  mkdir $TARGET_DIR
  cp -rf $SRC_DIR/* $TARGET_DIR
}

create_environment_file() {
  echo "Creating config file" >&2

  local SRC_FILE=/tmp/test-orchestrator/misc/test-orchestrator.env
  local TARGET_FILE=/etc/test-orchestrator.env
  
  cp -f $SRC_FILE $TARGET_FILE
  chmod 644 $TARGET_FILE
  chown root.root $TARGET_FILE

  sed -i "s/{{TTL_ENVIRONMENT}}/${TTL_ENVIRONMENT}/g" $TARGET_FILE
  sed -i "s/{{TTL_ENVIRONMENT_TYPE}}/${TTL_ENVIRONMENT_TYPE}/g" $TARGET_FILE
}


copy_source_files
create_environment_file
create_systemd_unit_file

cd /opt/test-orchestrator

echo "Allowing execution of test-orchestrator start script" >&2
chmod a+x /opt/test-orchestrator/src/TestOrchestrator.Web
