#!/usr/bin/env python

import subprocess
import os

git_info = subprocess.check_output(['git', 'describe']).strip()
git_info = git_info.split('-')
git_tag = git_info[0]

if len(git_info) == 1:
    build_version = git_tag
else:
    build_counter = os.getenv('BUILD_COUNTER')
    git_sha = git_info[2]
    build_version = '{0}.{1}-{2}'.format(git_tag, build_counter, git_sha)

def set_build_version(version):
    print("##teamcity[buildNumber '{0}']".format(version))
    print("##teamcity[setParameter name='system.BUILD_VERSION' value='{0}']".format(version))

set_build_version(build_version)

