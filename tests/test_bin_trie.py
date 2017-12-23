import pytest

from hypothesis import (
    given,
    strategies as st,
    settings,
)

from trie.trie import (
    BinaryTrie,
)
from trie.constants import (
    BLANK_HASH,
)
from trie.exceptions import (
    LeafNodeOverrideError,
)


@given(k=st.lists(st.binary(min_size=32, max_size=32), min_size=100, max_size=100, unique=True),
    v=st.lists(st.binary(min_size=1), min_size=100, max_size=100),
    random=st.randoms())
@settings(max_examples=10)
def test_bin_trie_different_order_insert(k, v, random):
    kv_pairs = list(zip(k, v))
    result = BLANK_HASH
    # Repeat 3 times
    for _ in range(3):
        trie = BinaryTrie(db={})
        random.shuffle(kv_pairs)
        for i, (k, v) in enumerate(kv_pairs):
            trie.set(k, v)
            assert trie.get(k) == v
        assert result is BLANK_HASH or trie.root_hash == result
        result = trie.root_hash
        # insert already exist key/value
        trie.set(kv_pairs[0][0], kv_pairs[0][1])
        assert trie.root_hash == result
        # Delete all key/value
        random.shuffle(kv_pairs)
        for k, v in kv_pairs:
            trie.delete(k)
        assert trie.root_hash == BLANK_HASH


@pytest.mark.parametrize(
    'kv1,kv2,key_to_be_deleted,will_delete,will_rasie_error',
    (
        ((b'\x12\x34\x56\x78', b'78'), (b'\x12\x34\x56\x79', b'79'), b'\x12\x34\x56', True, False),
        ((b'\x12\x34\x56\x78', b'78'), (b'\x12\x34\x56\xff', b'ff'), b'\x12\x34\x56', True, False),
        ((b'\x12\x34\x56\x78', b'78'), (b'\x12\x34\x56\x79', b'79'), b'\x12\x34\x57', False, False),
        ((b'\x12\x34\x56\x78', b'78'), (b'\x12\x34\x56\x79', b'79'), b'\x12\x34\x56\x78\x9a', False, True),
    ),
)
def test_bin_trie_delete_subtrie(kv1, kv2, key_to_be_deleted, will_delete, will_rasie_error):
    trie = BinaryTrie(db={})
    # First test case, delete subtrie of a kv node
    trie.set(kv1[0], kv1[1])
    trie.set(kv2[0], kv2[1])
    assert trie.get(kv1[0]) == kv1[1]
    assert trie.get(kv2[0]) == kv2[1]

    if will_delete:
        trie.delete_subtrie(key_to_be_deleted)
        assert trie.get(kv1[0]) == None
        assert trie.get(kv2[0]) == None
        assert trie.root_hash == BLANK_HASH
    else:
        if will_rasie_error:
            with pytest.raises(LeafNodeOverrideError):
                trie.delete_subtrie(key_to_be_deleted)
        else:
            root_hash_before_delete = trie.root_hash
            trie.delete_subtrie(key_to_be_deleted)
            assert trie.get(kv1[0]) == kv1[1]
            assert trie.get(kv2[0]) == kv2[1]
            assert trie.root_hash == root_hash_before_delete
