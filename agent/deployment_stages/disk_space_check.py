# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import ctypes
import os
import platform
from .common import DeploymentError, DeploymentStage


class CheckDiskSpace(DeploymentStage):
    def __init__(self):
        DeploymentStage.__init__(self, name='CheckDiskSpace')

    def _run(self, deployment):
        root = ''
        if platform.system() == 'Windows':
            root = ['C:', 'D:']
        else:
            root = ['/']

        for x in root:
            if get_free_space_mb(x) < 500:
                raise DeploymentError(
                    'The disk space on the machine is less than 500MB.')


def get_free_space_mb(dirname):
    """Return folder/drive free space (in megabytes)."""
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(dirname), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value / 1024 / 1024
    else:
        st = os.statvfs(dirname)
        return st.f_bavail * st.f_frsize / 1024 / 1024
