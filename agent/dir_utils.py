# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import os, platform
if platform.system().lower() != 'windows':
    import linux_utils

def change_ownership_recursive(directory, user_name, group_name):
    if not os.path.isdir(directory):
        raise Exception(' {0} is not a directory.'.format(object))
    if user_name is None:
        user_id = -1
    else:
        user_id = linux_utils.get_uid(user_name)
        if user_id is None:
            raise Exception('User specified does not exist: {0}'.format(user_name))
    if group_name is None:
        group_id = -1
    else:
        group_id = linux_utils.get_gid(group_name)
        if group_id is None:
            raise Exception('Group specified does not exist: {0}'.format(group_name))
    os.chown(directory, user_id, group_id)
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            os.chown(os.path.join(root, dir), user_id, group_id)
        for file in files:
            os.chown(os.path.join(root, file), user_id, group_id)

def change_mode_recursive(directory, mode):
    if not os.path.isdir(directory):
        raise Exception(' {0} is not a directory.'.format(object))
    if mode is None:
        raise Exception('Invalid mode: {0}'.format(mode))
    if not isinstance(mode, (int, long)):
        raise ValueError('Mode should be provided as a base-10 integer.')
    mode = int('0{0}'.format(str(mode)), base=8)
    os.chmod(directory, mode)
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), mode)
        for file in files:
            os.chmod(os.path.join(root, file), mode)
