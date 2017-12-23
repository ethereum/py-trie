import pytest

from trie.trie import (
    BinaryTrie,
)
from trie.utils.branches import (
    if_branch_exist,
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
