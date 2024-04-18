import pytest

from hypothesis import (
    given,
    settings,
    strategies as st,
)

from trie.binary import (
    BinaryTrie,
)
from trie.constants import (
    BLANK_HASH,
)
from trie.exceptions import (
    NodeOverrideError,
)


@given(
    k=st.lists(
        st.binary(min_size=32, max_size=32), min_size=100, max_size=100, unique=True
    ),
    v=st.lists(st.binary(min_size=1), min_size=100, max_size=100),
    random=st.randoms(use_true_random=True),
)
@settings(max_examples=10, deadline=1000)
def test_bin_trie_different_order_insert(k, v, random):
    kv_pairs = list(zip(k, v))
    result = BLANK_HASH
    # Repeat 3 times
    for _ in range(3):
        trie = BinaryTrie(db={})
        random.shuffle(kv_pairs)
        for _i, (k, v) in enumerate(kv_pairs):
            trie.set(k, v)
            assert trie.get(k) == v
        assert result is BLANK_HASH or trie.root_hash == result
        result = trie.root_hash
        # insert already exist key/value
        trie.set(kv_pairs[0][0], kv_pairs[0][1])
        assert trie.root_hash == result
        # Delete all key/value
        random.shuffle(kv_pairs)
        for k, _v in kv_pairs:
            trie.delete(k)
        assert trie.root_hash == BLANK_HASH


@pytest.mark.parametrize(
    "kv1,kv2,key_to_be_deleted,will_delete,will_rasie_error",
    (
        (
            (b"\x12\x34\x56\x78", b"78"),
            (b"\x12\x34\x56\x79", b"79"),
            b"\x12\x34\x56",
            True,
            False,
        ),
        (
            (b"\x12\x34\x56\x78", b"78"),
            (b"\x12\x34\x56\xff", b"ff"),
            b"\x12\x34\x56",
            True,
            False,
        ),
        (
            (b"\x12\x34\x56\x78", b"78"),
            (b"\x12\x34\x56\x79", b"79"),
            b"\x12\x34\x57",
            False,
            False,
        ),
        (
            (b"\x12\x34\x56\x78", b"78"),
            (b"\x12\x34\x56\x79", b"79"),
            b"\x12\x34\x56\x78\x9a",
            False,
            True,
        ),
    ),
)
def test_bin_trie_delete_subtrie(
    kv1, kv2, key_to_be_deleted, will_delete, will_rasie_error
):
    trie = BinaryTrie(db={})
    # First test case, delete subtrie of a kv node
    trie.set(kv1[0], kv1[1])
    trie.set(kv2[0], kv2[1])
    assert trie.get(kv1[0]) == kv1[1]
    assert trie.get(kv2[0]) == kv2[1]

    if will_delete:
        trie.delete_subtrie(key_to_be_deleted)
        assert trie.get(kv1[0]) is None
        assert trie.get(kv2[0]) is None
        assert trie.root_hash == BLANK_HASH
    else:
        if will_rasie_error:
            with pytest.raises(NodeOverrideError):
                trie.delete_subtrie(key_to_be_deleted)
        else:
            root_hash_before_delete = trie.root_hash
            trie.delete_subtrie(key_to_be_deleted)
            assert trie.get(kv1[0]) == kv1[1]
            assert trie.get(kv2[0]) == kv2[1]
            assert trie.root_hash == root_hash_before_delete


@pytest.mark.parametrize(
    "invalide_key,if_error",
    (
        (b"\x12\x34\x56", False),
        (b"\x12\x34\x56\x77", False),
        (b"\x12\x34\x56\x78\x9a", True),
        (b"\x12\x34\x56\x79\xab", True),
        (b"\xab\xcd\xef", False),
    ),
)
def test_bin_trie_invalid_key(invalide_key, if_error):
    trie = BinaryTrie(db={})
    trie.set(b"\x12\x34\x56\x78", b"78")
    trie.set(b"\x12\x34\x56\x79", b"79")

    assert trie.get(invalide_key) is None
    if if_error:
        with pytest.raises(NodeOverrideError):
            trie.delete(invalide_key)
    else:
        previous_root_hash = trie.root_hash
        trie.delete(invalide_key)
        assert previous_root_hash == trie.root_hash


@given(
    keys=st.lists(
        st.binary(min_size=32, max_size=32), min_size=100, max_size=100, unique=True
    ),
    chosen_numbers=st.lists(
        st.integers(min_value=0, max_value=99), min_size=50, max_size=50, unique=True
    ),
)
@settings(max_examples=10)
def test_bin_trie_update_value(keys, chosen_numbers):
    """
    This is a basic test to see if updating value works as expected.
    """
    trie = BinaryTrie(db={})
    for key in keys:
        trie.set(key, b"old")

    current_root = trie.root_hash
    for i in chosen_numbers:
        trie.set(keys[i], b"old")
        assert current_root == trie.root_hash
        trie.set(keys[i], b"new")
        assert current_root != trie.root_hash
        assert trie.get(keys[i]) == b"new"
        current_root = trie.root_hash
