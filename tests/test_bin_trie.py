import pytest

import random

from trie.trie import (
    BinaryTrie,
)

from trie.constants import (
    BLANK_HASH,
)
from trie.utils.sha3 import (
    keccak,
)


kvpairs = [(keccak(str(i).encode('utf-8')), str(i).encode('utf-8') * 5) for i in range(2000)]


def test_bin_trie_different_order_insert():
    result = BLANK_HASH
    # Repeat 3 times
    for _ in range(3):
        trie = BinaryTrie(db={})
        random.shuffle(kvpairs)
        for i, (k, v) in enumerate(kvpairs):
            trie.set(k, v)
            assert trie.get(k) == v
        assert result is BLANK_HASH or trie.root_hash == result
        result = trie.root_hash
        # insert already exist key/value
        trie.set(kvpairs[0][0], kvpairs[0][1])
        assert trie.root_hash == result
        # Delete all key/value
        random.shuffle(kvpairs)
        for k, v in kvpairs:
            trie.delete(k)
        assert trie.root_hash == BLANK_HASH

# TODO: add more binary trie tests