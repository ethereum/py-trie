BLANK_NODE = b''
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
