#!/usr/bin/env bash

sudo yum -y install rh-ruby22-ruby-devel rh-ruby22-rubygems-devel
source scl_source enable rh-ruby22
PATH=$TCHOME/.fpmgem/ruby/bin:$PATH
mkdir -p $TCHOME/.fpmgem/ruby 2> /dev/null
GEM_HOME=$TCHOME/.fpmgem/ruby/ gem install --install-dir $TCHOME/.fpmgem/ruby/ --no-ri --no-rdoc fpm

PATH=$TCHOME/.fpmgem/ruby/bin:$PATH
source scl_source enable rh-ruby22
export GEM_HOME=$TCHOME/.fpmgem/ruby/

# BUILD_TARGET is a build variable that defines which target we are building
echo "Run build..."
( ./build.sh "${BUILD_TARGET}" )

