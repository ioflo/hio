# -*- encoding: utf-8 -*-
"""
hio.help.naming Module

Mixin Base Class for one-to-one mapping with inverse: name-to-addr and addr-to-name
that add support for MemoGrams to datagram based transports.

Provide mixin classes.
Takes of advantage of multiple inheritance to enable mixtures of behaviors
with minimal code duplication (more DRY).

New style python classes use the C3 linearization algorithm. Multiple inheritance
forms a directed acyclic graph called a diamond graph. This graph is linarized
into the method resolution order.
Use class.mro() or class.__mro__

(see https://www.geeksforgeeks.org/method-resolution-order-in-python-inheritance/)
Basically:
* children always precede their parents
* immediate parent classes of a child are visited in the order listed in the
child class statement.
* a super class is visited only after all sub classes have been visited
* linearized graph is monotonic (a class is only visted once)

"""


from .. import hioing
from . import helping

class Namer(hioing.Mixin):
    """
    Namer mixin class for adding support for mappings between names and addresses.
    May be used to provide in-memory lookup of mapping and its inverse of
    address from name and name from address.

    """

    def __init__(self, entries=None, **kwa):
        """
        Setup instance

        Inherited Parameters:

        Parameters:
            entries (dict | interable): dict or iterable of (name, addr) duples
                to  bulk initialize the mappings between addresses and names


        Attributes:

        Hidden:
            _addrByName (dict): mapping between (name, address) pairs, these
                must be one-to-one so that inverse is also one-to-one
            _nameByAddr (dict): mapping between (address, name) pairs, these
                must be one-to-one so that inverse is also one-to-one



        """
        self._addrByName = dict()
        self._nameByAddr = dict()

        if helping.isNonStringIterable(entries):
            items = entries
        else:
            items = entries.items() if entries else []

        for name, addr in items:
            self.addEntry(name=name, addr=addr)

        super(Namer, self).__init__(**kwa)


    @property
    def addrByName(self):
        """Property that returns copy of ._addrByName
        """
        return dict(self._addrByName)

    @property
    def nameByAddr(self):
        """Property that returns copy of ._nameByAddr
        """
        return dict(self._nameByAddr)


    def getAddr(self, name):
        """Returns addr for given name or None if non-existant

        Parameters:
            name (str): name
        """
        return self._addrByName.get(name)


    def getName(self, addr):
        """Returns name for given addr or None if non-existant

        Parameters:
            addr (str): address
        """
        return self._nameByAddr.get(addr)


    def addEntry(self, name, addr):
        """Add mapping and inverse mapping entries for
        name to addr and addr to name
        All mappings must be one-to-one

        Returns:
            result (bool):  True if successfully added new entry.
                            False If matching entry already exists.
                            Otherwise raises NamerError if partial matching
                                entry with either name or addr

        Parameters:
            name (str): name of entry
            addr (str): address of entry

        Raise error if preexistant
        """
        if not name or not addr:
            raise  hioing.NamerError(f"Attempt to add incomplete or empty entry "
                                   f"({name=}, {addr=}).")
        if name in self._addrByName:
            if addr == self._addrByName[name]:
                return False  # already existing matching entry
            else:
                raise  hioing.NamerError(f"Attempt to add conflicting entry "
                               f"({name=}, {addr=}).")

        if addr in self._nameByAddr:
            if name == self._nameByAddr[addr]:
                return False  # already existing matching entry
            else:
                raise  hioing.NamerError(f"Attempt to add conflicting entry "
                               f"({name=}, {addr=}).")

        self._addrByName[name] = addr
        self._nameByAddr[addr] = name

        return True  # added new entry


    def remEntry(self, name=None, addr=None):
        """Delete both name to addr and addr to name mapping entries.
           When an entry is found for either name or addr or both.
           When both provided must be matching one-to-one entries.
           All mappings must be one-to-one

        Returns:
            result (bool):  True if matching entry successfully deleted
                            False if no matching entry, nothing deleted

        Parameters:
            name (str | None): name of remote to delete or None if delete by addr
            addr (str | None): addr of remote to delete or None if delete by name

            When both name and addr provided deletes by name

        Raise error when at least one of name or addr is not None and no mappings
        exist.
        """

        if name:
            if name not in self._addrByName:  # no entry for name
                return False

            if not addr:  # addr not provided so look it up
                addr = self._addrByName[name]

            if addr != self._addrByName[name]:  # mismatch do nothing
                return False

            del self._addrByName[name]
            del self._nameByAddr[addr]
            return True

        if addr:
            if addr not in self._nameByAddr:  # no entry for addr
                return False

            if not name:  # no name so look it up
                name = self._nameByAddr[addr]

            if name != self._nameByAddr[addr]:  # mismatch do nothing
                return False

            del self._addrByName[name]
            del self._nameByAddr[addr]
            return True

        return False  # nothing deleted neither name nor addr provided


    def clearEntries(self):
        """Clears all entries

        """
        self._addrByName = dict()
        self._nameByAddr = dict()


    def changeAddrAtName(self, *, name=None, addr=None):
        """Changes existing name to addr mapping to new addr. Replaces
        inverse mapping of addr to name.
        All mappings must be one-to-one

        Returns:
            result (bool):  True If successfully updated existing entries.
                            False If matching entry already exists, no change.
                            Otherwise raises NamerError

        Parameters:
            name (str): name of entry
            addr (str): address of entry

        Raise error if preexistant
        """
        if not name or not addr:
            raise  hioing.NamerError(f"Attempt to update with incomplete "
                                     f"or empty entry ({name=}, {addr=}).")

        if name not in self._addrByName:
            return False

        if addr == self._addrByName[name]:
            return False  # no change to entries

        if addr in self._nameByAddr:
            raise  hioing.NamerError(f"Conflicting entry for {addr=}.")

        oldAddr = self._addrByName[name]
        self._addrByName[name] = addr
        del self._nameByAddr[oldAddr]
        self._nameByAddr[addr] = name

        return True  # updated entries


    def changeNameAtAddr(self, *, addr=None, name=None):
        """Changes existing addr to name mapping to new name. Replaces
        inverse mapping of name to addr.
        All mappings must be one-to-one

        Returns:
            result (bool):  True If successfully updated existing entries.
                            False If matching entry already exists, no change.
                            Otherwise raises NamerError

        Parameters:
            addr (str): address of entry
            name (str): name of entry

        Raise error if preexistant
        """
        if not name or not addr:
            raise  hioing.NamerError(f"Attempt to update with incomplete entry "
                                   f"({name=}, {addr=}).")

        if addr not in self._nameByAddr:
            return False

        if name == self._nameByAddr[addr]:
            return False  # no change to entries

        if name in self._addrByName:
            raise  hioing.NamerError(f"Conflicting entry for {name=}.")

        oldName = self._nameByAddr[addr]
        self._nameByAddr[addr] = name
        del self._addrByName[oldName]
        self._addrByName[name] = addr

        return True  # updated entries

