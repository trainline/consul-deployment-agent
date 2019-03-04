#!/bin/sh
#
# Package the consul-deployment-agent as a self-contained executable and
# create a Debian package containing it.

#######################################
# Cleanup files from the backup dir
# Globals:
#   BUILD_NUMBER
# Arguments:
#   BUILD_TARGET
# Returns:
#   None
#######################################

BUILD_TARGET=$1
VERSION=$BUILD_NUMBER

TEMP_DIR=$PWD/temp
OUTPUT_DIR=$TEMP_DIR/output
PACKAGE_DIR=$OUTPUT_DIR/consul-deployment-agent
if [ -d $TEMP_DIR ]; then
  echo "Cleaning up directory $TEMP_DIR"
  rm -f $TEMP_DIR
fi
echo "Creating directory $OUTPUT_DIR for package staging"
mkdir -p $OUTPUT_DIR

echo "Create self-contained executable folder from Python script in $OUTPUT_DIR"
pyinstaller --noconfirm --clean --log-level=ERROR \
    --workpath=$TEMP_DIR/pyinstaller \
    --distpath=$OUTPUT_DIR \
    --specpath=$TEMP_DIR/pyinstaller \
    --name=consul-deployment-agent \
    --paths=$PWD/agent \
    $PWD/agent/core.py

echo "Copying $PWD/config/config-logging-linux.yml to $OUTPUT_DIR/config-logging.yml"
cp $PWD/config/config-logging-linux.yml $PACKAGE_DIR/config-logging.yml

echo "Copying Skeleton files to $OUTPUT_DIR/skel/"
cp -R $PWD/config/skel $PACKAGE_DIR/

echo "Copying tools files to $OUTPUT_DIR/tools/"
cp -R $PWD/tools $PACKAGE_DIR/

echo " ==> Using branch name $BUILD_TARGET"

echo "Changing permissions on package content."
chmod 755 $OUTPUT_DIR/consul-deployment-agent
find $PACKAGE_DIR/consul-deployment-agent -type f -exec chmod 755 {} \;
find $PACKAGE_DIR/*.yml -type f -exec chmod 644 {} \;

DEB_VERSION_TIMESTAMP=$(date +%Y%m%d.%H%M)

# We use FPM to build our package
echo " ==> Building DEB package"
fpm \
  --architecture all \
  --chdir $PACKAGE_DIR \
  --deb-group root \
  --deb-no-default-config-files \
  --deb-use-file-permissions \
  --deb-user root \
  --description "Consul Deployment Agent $BUILD_TARGET branch" \
  --input-type dir \
  --iteration $DEB_VERSION_TIMESTAMP \
  --name consul-deployment-agent-$BUILD_TARGET \
  --output-type deb \
  --prefix /opt/consul-deployment-agent \
  --version $VERSION \
  .
