"""
Destructive alternatives to functions in the shutil module.
"""

# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

from shutil import copy2, Error, copystat, os

def mergetree(src, dst, symlinks=False, ignore=None):
    """
    Like shutil.copytree except it overwrites the destination

    If dst does not exist it is created.

    If dst exists but is not a directory it is repaced.

    If dst exists and is a directory the files in src are copied to dst. If a file already exists in dst it is overwritten. The child directories of src are copied to dst by recursive calls to mergetree.

    The implementation is adapted from the code for shutil.copytree at https://docs.python.org/2/library/shutil.html#copytree-example
    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if os.path.exists(dst) and not os.path.isdir(dst):
        os.remove(dst)
    if not os.path.isdir(dst):
        os.makedirs(dst)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                mergetree(srcname, dstname, symlinks, ignore)
            else:
                copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
    try:
        copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise Error(errors)
        