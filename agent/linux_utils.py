# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

from grp import getgrnam
from pwd import getpwnam

def get_gid(name):
    if getgrnam is None or name is None:
        return None
    try:
        result = getgrnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result.gr_gid
    return None

def get_uid(name):
    if getpwnam is None or name is None:
        return None
    try:
        result = getpwnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result.pw_uid
    return None
