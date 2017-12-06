from trie.constants import (
    TWO_BITS,
    PREFIX_00,
    PREFIX_100000,
)


def safe_ord(value):
    if isinstance(value, int):
        return value
    else:
        return ord(value)


def decode_from_bin(input_bin):
    """
    0100000101010111010000110100100101001001 -> ASCII
    """
    output = bytearray(len(input_bin) // 8)
    for i in range(0, len(input_bin), 8):
        byte_value = 0
        for bit_value in input_bin[i:i+8]:
            byte_value = byte_value * 2 + bit_value
        output[i//8] = byte_value
    return bytes(output)


def encode_to_bin(value):
    """
    ASCII -> 0100000101010111010000110100100101001001
    """
    output = b''
    for char in value:
        char = safe_ord(char)
        byte_str = bytearray(8)
        for i in range(8):
            byte_str[7-i] = char % 2
            char //= 2
        output += byte_str
    return output


def encode_from_bin_keypath(input_bin):
    """
    Encodes a sequence of 0s and 1s into tightly packed bytes
    Used in encoding key path of a KV-NODE
    """
    padded_bin = bytes((4 - len(input_bin)) % 4) + input_bin
    prefix = TWO_BITS[len(input_bin) % 4]
    if len(padded_bin) % 8 == 4:
        return decode_from_bin(PREFIX_00 + prefix + padded_bin)
    else:
        return decode_from_bin(PREFIX_100000 + prefix + padded_bin)


def decode_to_bin_keypath(path):
    """
    Decodes bytes into a sequence of 0s and 1s
    Used in decoding key path of a KV-NODE
    """
    path = encode_to_bin(path)
    if path[0] == 1:
        path = path[4:]
    assert path[0:2] == PREFIX_00
    padded_len = TWO_BITS.index(path[2:4])
    return path[4+((4 - padded_len) % 4):]
