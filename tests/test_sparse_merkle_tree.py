import pytest

from hypothesis import (
    given,
    strategies as st,
    settings,
)

from eth_hash.auto import (
    keccak,
)

from trie.sparse_merkle_tree import (
    SparseMerkleTree,
)
from trie.constants import (
    EMPTY_NODE_HASHES,
)


@given(k=st.lists(st.binary(min_size=20, max_size=20), min_size=100, max_size=100, unique=True),
       v=st.lists(st.binary(min_size=1), min_size=100, max_size=100))
@settings(max_examples=10)
def test_sparse_merkle_tree(k, v, chosen_numbers):
    kv_pairs = list(zip(k, v))

    # Test basic get/set
    trie = SparseMerkleTree(db={})
    for k, v in kv_pairs:
        assert not trie.exists(k)
        trie.set(k, v)
    for k, v in kv_pairs:
        assert trie.get(k) == v
        trie.delete(k)
    for k, _ in kv_pairs:
        assert not trie.exists(k)
    assert trie.root_hash == keccak(EMPTY_NODE_HASHES[0] + EMPTY_NODE_HASHES[0])
