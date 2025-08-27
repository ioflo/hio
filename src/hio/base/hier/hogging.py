# -*- encoding: utf-8 -*-
"""
hio.base.hier.hogging Module

Provides support for hold logging (hogging)


"""
from __future__ import annotations  # so type hints of classes get resolved later

from ..filing import Filer
from .acting import Act

class Hog(Act, Filer):
    """Hog is Act that supports metrical logging of hold items based on logging
    rules such as time period, update, or change.

    Act comes before Filer in .__mro__ so Act.name property is used not Filer.name

    Inherited Class Attributes:
        Registry (dict): subclass registry whose items are (name, cls) where:
                name is unique name for subclass
                cls is reference to class object
        Instances (dict): instance registry whose items are (name, instance) where:
                name is unique instance name and instance is instance reference
        Index (int): default naming index for subclass instances. Each subclass
                overrides with a subclass specific Index value to track
                subclass specific instance default names.

        HeadDirPath (str): default abs dir path head such as "/usr/local/var"
        TailDirPath (str): default rel dir path tail when using head
        CleanTailDirPath (str): default rel dir path tail when creating clean
        AltHeadDirPath (str): default alt dir path head such as  "~"
                              as fallback when desired head not permitted.
        AltTailDirPath (str): default alt rel dir path tail as fallback
                              when using alt head.
        AltCleanTailDirPath (str): default alt rel path tail when creating clean
        TempHeadDir (str): default temp abs dir path head such as "/tmp"
        TempPrefix (str): default rel dir path prefix when using temp head
        TempSuffix (str): default rel dir path suffix when using temp head and tail
        Perm (int): explicit default octal perms such as 0o1700
        Mode (str): open mode such as "r+"
        Fext (str): default file extension such as "text" for "fname.text"

    Inherited Attributes  see Act, File
        hold (Hold): data shared by boxwork

        name (str): overriden by .name property from Act (see name property)
        base (str): another unique path component inserted before name
        temp (bool): True means use TempHeadDir in /tmp directory
        headDirPath (str): head directory path
        path (str | None):  full directory or file path once created else None
        perm (int):  octal OS permissions for path directory and/or file
        filed (bool): True means .path ends in file.
                       False means .path ends in directory
        extensioned (bool): When not filed:
                                True means ensure .path ends with fext
                                False means do not ensure .path ends with fext
        mode (str): file open mode if filed
        fext (str): file extension if filed
        file (File | None): File instance when filed and created.
        opened (bool): True means directory created and if filed then file
                is opened. False otherwise


    Inherited Properties  see Act, File
        name (str): unique name string of instance used for registering Act
                    instance in Act registry as well providing a unique path
                    component used in file path name
        iops (dict): input-output-parameters for .act
        nabe (str): action nabe (context) for .act


    Hidden:
        _name (str): unique name of instance for .name property
        _iopts (dict): input-output-paramters for .act for .iops property
        _nabe (str): action nabe (context) for .act for .nabe property


    """

    def __init__(self, **kwa):
        """Initialize instance.

        Inherited Parameters:
            name (str|None): unique name of this instance. When None then
                generate name from .Index. Used for .name property which is
                 used for registering Act instance in Act registry as well
                 providing a unique path component used in file path name.
                 When system employs more than one installation, name allows
                 differentiating each installation by name
            iops (dict|None): input-output-parameters for .act. When None then
                set to empty dict.
            nabe (str): action nabe (context) for act. default is "endo"
            hold (None|Hold): data shared across boxwork

            base (str): optional directory path segment inserted before name
                that allows further differentation with a hierarchy. "" means
                optional.
            temp (bool): assign to .temp
                True then open in temporary directory, clear on close
                Otherwise then open persistent directory, do not clear on close
            headDirPath (str): optional head directory pathname for main database
                Default .HeadDirPath
            perm (int): optional numeric os dir permissions for database
                directory and database files. Default .DirMode
            reopen (bool): True (re)open with this init
                           False not (re)open with this init but later (default)
            clear (bool): True means remove directory upon close when reopening
                          False means do not remove directory upon close when reopening
            reuse (bool): True means reuse self.path if already exists
                          False means do not reuse but remake self.path
            clean (bool): True means path uses clean tail variant
                             False means path uses normal tail variant
            filed (bool): True means .path is file path not directory path
                          False means .path is directiory path not file path
            extensioned (bool): When not filed:
                                True means ensure .path ends with fext
                                False means do not ensure .path ends with fext
            mode (str): File open mode when filed
            fext (str): File extension when filed or extensioned
        """
        super(Hog, self).__init__(**kwa)
