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
       v=st.lists(st.binary(min_size=1), min_size=100, max_size=100),
       chosen_numbers=st.lists(
           st.integers(min_value=1, max_value=99),
           min_size=50,
           max_size=100,
           unique=True),
       random=st.randoms())
@settings(max_examples=10)
def test_sparse_merkle_tree(k, v, chosen_numbers, random):
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

    # Test single update
    random.shuffle(kv_pairs)
    for k, v in kv_pairs:
        trie.set(k, v)
    prior_to_update_root = trie.root_hash
    for i in chosen_numbers:
        # Update
        trie.set(kv_pairs[i][0], i.to_bytes(i, byteorder='big'))
        assert trie.get(kv_pairs[i][0]) == i.to_bytes(i, byteorder='big')
        assert trie.root_hash != prior_to_update_root
        # Un-update
        trie.set(kv_pairs[i][0], kv_pairs[i][1])
        assert trie.root_hash == prior_to_update_root

    # Test batch update with different update order
    # First batch update
    for i in chosen_numbers:
        trie.set(kv_pairs[i][0], i.to_bytes(i, byteorder='big'))
    batch_updated_root = trie.root_hash
    # Un-update
    for i in chosen_numbers:
        trie.set(kv_pairs[i][0], kv_pairs[i][1])
    assert trie.root_hash == prior_to_update_root
    # Second batch update
    random.shuffle(chosen_numbers)
    for i in chosen_numbers:
        trie.set(kv_pairs[i][0], i.to_bytes(i, byteorder='big'))
    assert trie.root_hash == batch_updated_root
