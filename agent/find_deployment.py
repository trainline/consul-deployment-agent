# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

from os import listdir
from os.path import exists, isdir, join

def find_deployment_dir_win(base_dir, service_id, deployment_id):
    candidate_paths = [
        join(base_dir, service_id, deployment_id),
        join(base_dir, deployment_id)
    ]
    return next((path for path in candidate_paths if exists(path)), None)

def find_deployment_dirs(base_dir, service_id):
    directory = join(base_dir, service_id)
    all_files = [join(directory, dirname) for dirname in listdir(directory)]
    return [f for f in all_files if isdir(f)]
