import os
from codecs import open

def write_version_file(version):
    with open('agent/version.py', 'r') as file:
        filedata = file.read()
    filedata = filedata.replace('0.0.0', version)
    with open('agent/version.py', 'w') as file:
        file.write(filedata)

build_version = os.getenviron('BUILD_VERSION')
write_version_file(build_version)

