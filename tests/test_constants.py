import collections

from eth_utils import (
    keccak,
)
from rlp.codec import (
    encode_raw,
)

from trie.constants import (
    BLANK_HASH,
    BLANK_NODE,
    BLANK_NODE_HASH,
)
from trie.smt import (
    SparseMerkleTree as SMT,
)


def test_hash_constants():
    assert BLANK_HASH == keccak(BLANK_NODE)
    assert BLANK_NODE_HASH == keccak(encode_raw(b""))


def test_smt256_empty_hashes():
    DEPTH = 256  # Default depth is 32 bytes

    # Start at the bottom
    EMPTY_LEAF_NODE_HASH = BLANK_HASH
    EMPTY_NODE_HASHES = collections.deque([EMPTY_LEAF_NODE_HASH])

    # More hashes the lower you go down the tree (to the root)
    # NOTE: Did this with different code as a sanity check
    for _ in range(DEPTH - 1):
        EMPTY_NODE_HASHES.appendleft(
            keccak(EMPTY_NODE_HASHES[0] + EMPTY_NODE_HASHES[0])
        )
    EMPTY_ROOT_HASH = keccak(EMPTY_NODE_HASHES[0] + EMPTY_NODE_HASHES[0])

    smt = SMT()
    assert smt.root_hash == EMPTY_ROOT_HASH

    key = b"\x00" * 32
    # _get(key) returns value, branch tuple
    assert smt._get(key)[1] == tuple(EMPTY_NODE_HASHES)
