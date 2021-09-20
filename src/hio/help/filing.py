# -*- encoding: utf-8 -*-
"""
hio.help.filing module

"""
import os
import errno
import json
import msgpack


def ocfn(filepath, mode='r+', binary=False):
    """Atomically open or create file from filepath.

       If file already exists, Then open file using openMode
       Else create file using write update mode If not binary Else
           write update binary mode
       Returns file object

       If binary Then If new file open with write update binary mode
    """
    try:
        newfd = os.open(filepath, os.O_EXCL | os.O_CREAT | os.O_RDWR, 436) # 436 == octal 0664
        if not binary:
            newfile = os.fdopen(newfd,"w+")
        else:
            newfile = os.fdopen(newfd,"w+b")
    except OSError as ex:
        if ex.errno == errno.EEXIST:
            newfile = open(filepath, mode)
        else:
            raise
    return newfile


def dump(data, filepath):
    '''
    Write data as as type self.ext to filepath. json or .msgpack
    '''
    if ' ' in filepath:
        raise IOError("Invalid filepath '{0}' "
                                "contains space".format(filepath))

    root, ext = os.path.splitext(filepath)
    if ext == '.json':
        with ocfn(filepath, "w+") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    elif ext == '.msgpack':
        if not msgpack:
            raise IOError("Invalid filepath ext '{0}' "
                        "needs msgpack installed".format(filepath))
        with ocfn(filepath, "w+b", binary=True) as f:
            msgpack.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
    else:
        raise IOError("Invalid filepath ext '{0}' "
                    "not '.json' or '.msgpack'".format(filepath))


def load(filepath):
    '''
    Return data read from filepath as dict
    file may be either json or msgpack given by extension .json or .msgpack
    Otherwise return None
    '''
    try:
        root, ext = os.path.splitext(filepath)
        if ext == '.json':
            with ocfn(filepath, "r") as f:
                it = json.load(f)
        elif ext == '.msgpack':
            if not msgpack:
                raise IOError("Invalid filepath ext '{0}' "
                            "needs msgpack installed".format(filepath))
            with ocfn(filepath, "rb", binary=True) as f:
                it = msgpack.load(f)
        else:
            it = None
    except EOFError:
        return None
    except ValueError:
        return None
    return it
