import subprocess
import os
from codecs import open

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

def write_version_file(version):
    with open('agent/version.py', 'r') as file:
        filedata = file.read()
    filedata = filedata.replace('0.0.0', version)
    with open('agent/version.py', 'w') as file:
        file.write(filedata)

set_build_version(build_version)
write_version_file(build_version)
