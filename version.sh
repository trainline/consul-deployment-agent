#!/usr/bin/env bash

set -euf
set -o pipefail

GIT_INFO=$(git describe)
TAG=$(echo $GIT_INFO | cut -d'-' -f1)
SHA=$(echo $GIT_INFO | cut -d'-' -f3)

if [[ "$TAG" == "$SHA" ]]; then
  BUILD_VERSION="$TAG"
else
  BUILD_VERSION="$TAG-$BUILD_COUNTER.${SHA}"
fi

echo "##teamcity[buildNumber '${BUILD_VERSION}']"

