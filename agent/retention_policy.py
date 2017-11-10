# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.
"""retention_policy

This module provides functions for implementing a file retention policy.

"""

def get_directories_to_delete(deployment, dirs, retain=0):
    """list the directories to delete.

    This function lists the absolute path of the directories to
    delete

    Args:
        deployment: The deployment.
        retain: Minimum number of directories to retain.
        protect: The absolute paths of directories to protect from deletion.

    Returns:
        list(filename): A list of absolute paths.

    """
    all_dirs = [f for (f, _) in sorted(dirs, key=lambda (_, s): s.st_ctime, reverse=True)]
    current_and_previous = {getattr(deployment, 'dir', None), getattr(deployment, 'last_dir', None)}.difference({None})
    without_current_and_previous = [d for d in all_dirs if d not in current_and_previous]
    most_recent = set(without_current_and_previous[0:max(0, retain-len(all_dirs)+len(without_current_and_previous))])
    protected = most_recent.union(current_and_previous)
    return [directory for directory in all_dirs if directory not in protected]
