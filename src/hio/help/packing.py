# -*- encoding: utf-8 -*-
"""
hio.help.packing Module

Packs and unpacks bit fields using format string whereas struct in std lib only
packs and unpacks byte fields.

"""



def packify(fmt=u'8', fields=[0x00], size=None, reverse=False):
    """
    Packs fields sequence of bit fields into bytearray of size bytes using fmt string.
    Each white space separated field of fmt is the length of the associated bit field
    If not provided size is the least integer number of bytes that hold the fmt.
    If reverse is true reverse the order of the bytes in the byte array before
    returning. This is useful for converting between bigendian and littleendian.

    Assumes unsigned fields values.
    Assumes network big endian so first fields element is high order bits.
    Each field in format string is number of bits for the associated bit field
    Fields with length of 1 are treated as has having boolean truthy field values
       that is,   nonzero is True and packs as a 1
    for 2+ length bit fields the field element is truncated to the number of
       low order bits in the bit field
    if sum of number of bits in fmt less than size bytes then the last byte in
       the bytearray is right zero padded
    if sum of number of bits in fmt greater than size bytes returns exception
    to pad just use 0 value in source field.
    example
    packify("1 3 2 2", (True, 4, 0, 3)). returns bytearry([0xc3])
    """
    tbfl = sum((int(x) for x in fmt.split()))
    if size is None:
        size = (tbfl // 8) + 1 if tbfl % 8 else tbfl // 8

    if not (0 <= tbfl <= (size * 8)):
        raise ValueError("Total bit field lengths in fmt not in [0, {0}]".format(size * 8))

    n = 0
    bfp = 8 * size  # starting bit field position
    bu = 0  # bits used

    for i, bfmt in enumerate(fmt.split()):
        bits = 0x0
        bfl = int(bfmt)
        bu += bfl

        if bfl == 1:
            bits = 0x1 if fields[i] else 0x0

        else:
            bits = fields[i] & (2**bfl - 1)  # bit-and mask out high order bits

        bits <<= (bfp - bfl) #shift left to bit position less bit field size

        n |= bits  # bit-or in bits
        bfp -= bfl #adjust bit field position for next element

    return bytify(n=n, size=size, reverse=reverse, strict=True)  # use int.to_bytes


def packifyInto(b, fmt=u'8', fields=[0x00], size=None, offset=0, reverse=False):
    """
    Packs fields sequence of bit fields using fmt string into bytearray b
    starting at offset and packing into size bytes
    Each white space separated field of fmt is the length of the associated bit field
    If not provided size is the least integer number of bytes that hold the fmt.
    Extends the length of b to accomodate size after offset if not enough.
    Returns actual size of portion packed into.
    The default assumes big endian.
    If reverse is True then reverses the byte order before extending. Useful for
    little endian.

    Assumes unsigned fields values.
    Assumes network big endian so first fields element is high order bits.
    Each field in format string is number of bits for the associated bit field
    Fields with length of 1 are treated as has having boolean truthy field values
       that is,   nonzero is True and packs as a 1
    for 2+ length bit fields the field element is truncated
    to the number of low order bits in the bit field
    if sum of number of bits in fmt less than size bytes then the last byte in
       the bytearray is right zero padded
    if sum of number of bits in fmt greater than size bytes returns exception
    to pad just use 0 value in source field.
    example
    packify("1 3 2 2", (True, 4, 0, 3)). returns bytearry([0xc3])
    """
    tbfl = sum((int(x) for x in fmt.split()))
    if size is None:
        size = (tbfl // 8) + 1 if tbfl % 8 else tbfl // 8

    if not (0 <= tbfl <= (size * 8)):
        raise ValueError("Total bit field lengths in fmt not in [0, {0}]".format(size * 8))

    if len(b) < (offset + size):
        b.extend([0x00]*(offset + size - len(b)))

    n = 0
    bfp = 8 * size  # starting bit field position
    bu = 0  # bits used

    for i, bfmt in enumerate(fmt.split()):
        bits = 0x0
        bfl = int(bfmt)
        bu += bfl

        if bfl == 1:
            bits = 0x1 if fields[i] else 0x0
        else:
            bits = fields[i] & (2**bfl - 1)  # bit-and mask out high order bits

        bits <<= (bfp - bfl) #shift left to bit position less bit field size

        n |= bits  # bit-or in bits
        bfp -= bfl #adjust bit field position for next element

    bp = bytify(n=n, size=size, reverse=reverse, strict=True) # use int.to_bytes

    b[offset:offset + len(bp)] = bp

    return size


def unpackify(fmt=u'1 1 1 1 1 1 1 1',
              b=bytearray([0x00]),
              boolean=False,
              size=None,
              reverse=False):
    """
    Returns tuple of unsigned int bit field values that are unpacked from the
    bytearray b according to fmt string. b maybe an integer iterator
    If not provided size is the least integer number of bytes that hold the fmt.
    The default assumes big endian.
    If reverse is True then reverse the byte order of b before unpackifing. This
    is useful for little endian.

    Each white space separated field of fmt is the length of the associated bit field.
    returns unsigned fields values.

    Assumes network big endian so first fmt is high order bits.
    Format string is number of bits per bit field
    If boolean parameter is True then return boolean values for
       bit fields of length 1

    if sum of number of bits in fmt less than 8 * size) then remaining
    bits are returned as additional field in result.

    if sum of number of bits in fmt greater 8 * len(b) returns exception

    example:
    unpackify(u"1 3 2 2", bytearray([0xc3]), False) returns (1, 4, 0, 3)
    unpackify(u"1 3 2 2", 0xc3, True) returns (True, 4, 0, 3)
    """
    b = bytearray(b)
    if reverse:
        b.reverse()

    tbfl = sum((int(x) for x in fmt.split()))
    if size is None:
        size = (tbfl // 8) + 1 if tbfl % 8 else tbfl // 8

    if not (0 <= tbfl <= (size * 8)):
        raise ValueError("Total bit field lengths in fmt not in [0, {0}]".format(size * 8))

    b = b[:size]
    fields = []  # list of bit fields
    bfp = 8 * size  # bit field position
    bu = 0  # bits used
    n = unbytify(b)  # unsigned int equivalent of b  # use int.from_bytes instead

    for i, bfmt in enumerate(fmt.split()):
        bfl = int(bfmt)
        bu += bfl

        mask = (2**bfl - 1) << (bfp - bfl)  # make mask
        bits = n & mask  # mask off other bits
        bits >>= (bfp - bfl)  # right shift to low order bits
        if bfl == 1 and boolean: #convert to boolean
            bits = True if bits else False

        fields.append(bits) #assign to fields list
        bfp -= bfl #adjust bit field position for next element

    if bfp != 0:  # remaining bits
        bfl = bfp
        mask = (2**bfl - 1) # make mask
        bits = n & mask  # mask off other bits
        if bfl == 1 and boolean: #convert to boolean
            bits = True if bits else False

        fields.append(bits) #assign to fields list
    return tuple(fields) #convert to tuple

