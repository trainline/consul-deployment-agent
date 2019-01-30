#!/bin/sh


if [ -s $TCHOME ]; then
  sudo yum -y install rh-ruby22-ruby-devel rh-ruby22-rubygems-devel
  source scl_source enable rh-ruby22
  PATH=$TCHOME/.fpmgem/ruby/bin:$PATH
  mkdir -p $TCHOME/.fpmgem/ruby 2> /dev/null
  GEM_HOME=$TCHOME/.fpmgem/ruby/ gem install --install-dir $TCHOME/.fpmgem/ruby/ --no-ri --no-rdoc fpm
fi

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
cp -R $PWD/skel $PACKAGE_DIR/

if [ -s $TCHOME ]; then
    MYHOME="."
else
    MYHOME="$TEMP_DIR"
fi
# Get build directory
if [ ! -d "$MYHOME/globalpackage" ]; then
  rm -f "$MYHOME/globalpackage"
  mkdir -p "$MYHOME/globalpackage"
fi
# Checks we have rpm-build installed
if [ "$(fpm --help 1>/dev/null ; echo $?)" = "1" ]; then
  echo "fpm is not installed in your system, please run: gem install fpm"
  exit 1
fi


echo " ==> Using branch name $BUILD_TARGET"

VERSION_TIMESTAMP=$(date +%Y%m%d_%H%M)

echo "Changing permissions on package content."
find $PACKAGE_DIR/consul-deployment-agent -type f -exec chmod 755 {} \;
find $PACKAGE_DIR/*.yml -type f -exec chmod 644 {} \;

echo " ==> Building RPM package"
fpm -s dir -t rpm -a all -n consul-deployment-agent-$BUILD_TARGET -v $VERSION --iteration $VERSION_TIMESTAMP --description "Consul Deployment Agent $BUILD_TARGET branch" --rpm-os linux --rpm-user root --rpm-group root --prefix /opt/consul-deployment-agent --package "$MYHOME/globalpackage" -C $PACKAGE_DIR .

DEB_VERSION_TIMESTAMP=`echo $VERSION_TIMESTAMP | tr "_" "."`

# We use FPM to build our package
echo " ==> Building DEB package"
fpm -s dir -t deb -a all -n consul-deployment-agent-$BUILD_TARGET -v $VERSION --iteration $DEB_VERSION_TIMESTAMP --deb-no-default-config-files --description "Consul Deployment Agent $BUILD_TARGET branch" --deb-user root --deb-group root --prefix /opt/consul-deployment-agent --package "$MYHOME/globalpackage" -C $PACKAGE_DIR .
