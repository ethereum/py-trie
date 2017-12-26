import pytest

from trie.trie import (
    BinaryTrie,
)
from trie.exceptions import (
    InvalidKeyError,
)

from trie.branches import (
    if_branch_exist,
    get_branch,
    verify_branch,
    get_trie_nodes,
    get_witness,
)

@pytest.fixture
def test_trie():
    trie = BinaryTrie(db={})
    trie.set(b'\x12\x34\x56\x78\x9a', b'9a')
    trie.set(b'\x12\x34\x56\x78\x9b', b'9b')
    trie.set(b'\x12\x34\x56\xff', b'ff')

    return trie


@pytest.mark.parametrize(
    'key_prefix,if_exist',
    (
        (b'\x12\x34', True),
        (b'\x12\x34\x56\x78\x9b', True),
        (b'\x12\x56', False),
        (b'\x12\x34\x56\xff\xff', False),
        (b'\x12\x34\x56', True),
        (b'\x12\x34\x56\x78', True),
    ),
)
def test_branch_exist(test_trie, key_prefix, if_exist):
    assert if_branch_exist(test_trie.db, test_trie.root_hash, key_prefix) == if_exist


@pytest.mark.parametrize(
    'key,key_valid',
    (
        (b'\x12\x34', False),
        (b'\x12\x34\x56\xff', True),
        (b'\x12\x34\x56\x78\x9b', True),
        (b'\x12\x56', False),
        (b'\x12\x34\x56\xff\xff', False),
    ),
)
def test_branch(test_trie, key, key_valid):
    if key_valid:
        lf_branch = get_branch(test_trie.db, test_trie.root_hash, key)
        assert verify_branch(lf_branch, test_trie.root_hash, key, test_trie.get(key))
        branch = get_branch(test_trie.db, test_trie.root_hash, key)
        assert verify_branch(branch, test_trie.root_hash, key, test_trie.get(key))
    else:
        with pytest.raises(InvalidKeyError):
            get_branch(test_trie.db, test_trie.root_hash, key)
        with pytest.raises(InvalidKeyError):
            get_branch(test_trie.db, test_trie.root_hash, key)
