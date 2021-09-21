# -*- encoding: utf-8 -*-
"""
hio.help.filing module

"""
import os
import errno
import json
import msgpack


def ocfn(path, mode='r+'):
    """
    Atomically open or create file from filepath.

    If file already exists, Then open file using openMode
    Else create file using write update mode If not binary Else
        write update binary mode
    Returns file object

    If binary Then If new file open with write update binary mode
    """
    try:
        # 436 == octal 0664
        newfd = os.open(path, os.O_EXCL | os.O_CREAT | os.O_RDWR, 436)
        if "b" in mode:
            file = os.fdopen(newfd,"w+b")
        else:
            file = os.fdopen(newfd,"w+")

    except OSError as ex:
        if ex.errno == errno.EEXIST:
            file = open(path, mode)
        else:
            raise
    return file


def dump(data, path):
    '''
    Write data as as type self.ext to path as either json or msgpack
    '''
    if ' ' in path:
        raise IOError("Invalid file path '{0}' "
                                "contains space".format(path))

    root, ext = os.path.splitext(path)
    if ext == '.json':
        with ocfn(path, "w+") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    elif ext == '.mgpk':
        if not msgpack:
            raise IOError("Invalid file path ext '{0}' "
                        "needs msgpack installed".format(path))
        with ocfn(path, "w+b") as f:
            msgpack.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
    else:
        raise IOError("Invalid file path ext '{0}' "
                    "not '.json' or '.mgpk'".format(path))


def load(path):
    '''
    Return data read from file path as dict
    file may be either json or msgpack given by extension .json or .msgpack
    Otherwise return None
    '''
    try:
        root, ext = os.path.splitext(path)
        if ext == '.json':
            with ocfn(path, "r") as f:
                it = json.load(f)
        elif ext == '.mgpk':
            if not msgpack:
                raise IOError("Invalid file path ext '{0}' "
                            "needs msgpack installed".format(path))
            with ocfn(path, "rb") as f:
                it = msgpack.load(f)
        else:
            it = None
    except EOFError:
        return None
    except ValueError:
        return None
    return it
