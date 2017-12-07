BLANK_NODE = b''
# sha3(b'')
BLANK_HASH = b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"  # noqa: E501
# sha3(rlp.encode(b''))
BLANK_NODE_HASH = b'V\xe8\x1f\x17\x1b\xccU\xa6\xff\x83E\xe6\x92\xc0\xf8n\x5bH\xe0\x1b\x99l\xad\xc0\x01b/\xb5\xe3c\xb4!'  # noqa: E501


NIBBLES_LOOKUP = {hex_char: idx for idx, hex_char in enumerate(b'0123456789abcdef')}
NIBBLE_TERMINATOR = 16

HP_FLAG_2 = 2
HP_FLAG_0 = 0


NODE_TYPE_BLANK = 0
NODE_TYPE_LEAF = 1
NODE_TYPE_EXTENSION = 2
NODE_TYPE_BRANCH = 3

# Constants for Binary Trie
TWO_BITS = [bytes([0, 0]), bytes([0, 1]),
            bytes([1, 0]), bytes([1, 1])]
PREFIX_00 = bytes([0, 0])
PREFIX_100000 = bytes([1, 0, 0, 0, 0, 0])

KV_TYPE = 0
BRANCH_TYPE = 1
LEAF_TYPE = 2

BYTE_1 = bytes([1])
BYTE_0 = bytes([0])
