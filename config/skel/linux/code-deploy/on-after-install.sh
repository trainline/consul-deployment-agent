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
  # Scripts needs to be read and execute for the consul user to work with them
  if [ -d $SRC_DIR/healthchecks ]; then
    find $SRC_DIR/healthchecks -name "*.sh" -exec chmod 775 {} \;
  fi
}

create_environment_file() {
  echo "Creating config file" >&2
  local TARGET_FILE="/etc/${TTL_SERVICE_NAME_WITH_SLICE}.env"
  cat "${TTL_INSTALL_SRC_DIR}/misc/service.env" > "${TARGET_FILE}"

  if [ -f "${TTL_INSTALL_SRC_DIR}/configuration.env" ]; then
    echo >> "${TTL_INSTALL_SRC_DIR}/configuration.env"
    cat "${TTL_INSTALL_SRC_DIR}/configuration.env" >> "${TARGET_FILE}"
  fi

  chmod 644 $TARGET_FILE
  chown root.root $TARGET_FILE
  replace_env_vars $TARGET_FILE
}

link_encrypted_secret_file() {
  local SECRETS="/etc/${TTL_SERVICE_NAME_WITH_SLICE}.env"
  if [ -f "${SECRETS}" ]; then
    ln -fs "/etc/${TTL_SERVICE_NAME_WITH_SLICE}.env" "/opt/${TTL_SERVICE_NAME_WITH_SLICE}/secret.env"
  fi
}

create_systemd_unit_execstart_script() {
  # TODO: fix hard-coded path below
  local SRC_FILE=/opt/consul-deployment-agent/skel/linux/misc/start.sh
  local TARGET_FILE=/opt/${TTL_SERVICE_NAME_WITH_SLICE}/start

  cp -f "${SRC_FILE}" "${TARGET_FILE}"
  chmod 755 "${TARGET_FILE}"
  chown root.root "${TARGET_FILE}"
  replace_env_vars "${TARGET_FILE}"
}

install_tlcrypt() {

  if [ -f "/etc/ssl/ttl/dev.key" ]; then
    echo "TTL_ENCRYPT_KEY_FILE=/etc/ssl/ttl/dev.key" >> "/etc/${TTL_SERVICE_NAME_WITH_SLICE}.env"
  fi
  if [ -f "/etc/ssl/ttl/prod.key" ]; then
    echo "TTL_ENCRYPT_KEY_FILE=/etc/ssl/ttl/prod.key" >> "/etc/${TTL_SERVICE_NAME_WITH_SLICE}.env"
  fi

  local SRC_FILE=/opt/consul-deployment-agent/tools/tlcrypt/tlcrypt
  local TARGET_FILE=/usr/local/bin/tlcrypt

  chmod 755 "${SRC_FILE}"
  chown root.root "${SRC_FILE}"
  ln -f -s "${SRC_FILE}" "${TARGET_FILE}"
}

################################################################################
# Create healthchecks by merging user-supplied healthcheck definitions with
# default healthcheck definitions. Any template expressions in the healthcheck
# definitions (healthchecks.yml) and in any supporting files such as check
# scripts are expanded.
#
# Globals:
#   DEPLOYMENT_BASE_DIR: the root directory of the unpacked deployment archive.
# Arguments:
#   CHECK_TYPE: one of {"consul", "sensu"}
# Returns:
#   None
#
# TODO(merlint): This implementation does not parse or validate the user-
#   supplied healthcheck definition files. It assumes that the checks are
#   found between the first unindented line and the next unindented line or
#   EOF.
################################################################################
create_healthchecks() {
  echo "Creating health checks"
  local CHECK_TYPE="${1}"
  echo "Health check type: ${CHECK_TYPE}"
  local BASE_DIR=$(dirname "${DEPLOYMENT_BASE_DIR}")
  echo "Base directory: ${BASE_DIR}"
  local ARCHIVE_DIR="${DEPLOYMENT_BASE_DIR}"
  echo "Archive directory: ${ARCHIVE_DIR}"
  local DEFAULTS_DIR="${BASE_DIR}/defaults"
  echo "Defaults directory: ${DEFAULTS_DIR}"
  local WORK_DIR="${BASE_DIR}/work"
  echo "Work directory: ${WORK_DIR}"

  local DEFAULTS="${DEFAULTS_DIR}/healthchecks/${CHECK_TYPE}/healthchecks.yml"
  echo "Defaults: ${DEFAULTS}"
  local OUT_DIR="${WORK_DIR}/out/healthchecks/${CHECK_TYPE}"
  echo "Out directory: ${OUT_DIR}"
  local USER_DIR="${ARCHIVE_DIR}/healthchecks/${CHECK_TYPE}"
  echo "User directory: ${USER_DIR}"

  # Create a healthcheck.yml file by merging the default and user-supplied
  # files.
  local OUT="${OUT_DIR}/healthchecks.yml"
  echo "Out: ${OUT}"
  local USER="${USER_DIR}/healthchecks.yml"
  echo "User: ${USER}"
  mkdir -p "${OUT_DIR}"
  echo "Made output directory success"
  for FILE in "${DEFAULTS}" "${USER}";
  do
    if [ -f "${FILE}" ]; then
      echo "${FILE} is a file"
      # The user may not have supplied a healthcheck file. 
      sed -nE "/^${CHECK_TYPE}_healthchecks/,/^[^ ]/ p" "${FILE}";
    fi
  done | sed -E '/^[^ ]/ d' | sed -E "1 i ${CHECK_TYPE}_healthchecks:" \
    > "${OUT}"

  echo "Done with file replacement."

  # Replace any template expressions in the generated healthcheck.yml.
  replace_env_vars "${OUT}"
  echo "Done with environment variable replacement."
  # Create or replace the user-supplied healthcheck.yml with a link to the
  # merge of the default and user-supplied healthcheck.yml files
  mkdir -p "${USER_DIR}" && ln -fs "${OUT}" "${USER}"
  echo "Done making directories and linking out to user."

  # Copy check script files from the defaults directory to the runtime directory
  # Do not overwrite any that are already present as these are user-supplied.
  cp -Rn ${DEFAULTS_DIR}/healthchecks/${CHECK_TYPE}/* \
    "${ARCHIVE_DIR}/healthchecks/${CHECK_TYPE}/"

  echo "Done copying from ${DEFAULTS_DIR} to ${ARCHIVE_DIR}."

  # Replace any template expressions in check script files.
  for FILE in $(find ${ARCHIVE_DIR}/healthchecks/${CHECK_TYPE}/ -type f);
  do
    echo "Working with ${FILE} from ${ARCHIVE_DIR}"
    replace_env_vars "${FILE}";
    chmod 755 "${FILE}"
    chown root.root "${FILE}"
  done
}

copy_certificates
copy_source_files
create_environment_file
create_systemd_unit_execstart_script
create_systemd_unit_file
install_tlcrypt
link_encrypted_secret_file

create_healthchecks 'consul'
create_healthchecks 'sensu'

cd /opt/$TTL_SERVICE_NAME_WITH_SLICE
echo "Allowing execution of $TTL_SERVICE_NAME start script" >&2
chmod a+x /opt/$TTL_SERVICE_NAME_WITH_SLICE/$TTL_SERVICE_EXE
