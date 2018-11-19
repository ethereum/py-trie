from eth_utils import (
        keccak,
    )

from rlp.codec import encode_raw

from trie.constants import (
        BLANK_NODE,
        BLANK_HASH,
        BLANK_NODE_HASH,
    )


def test_hash_constants():
    assert BLANK_HASH == keccak(BLANK_NODE)
    assert BLANK_NODE_HASH == keccak(encode_raw(b''))
