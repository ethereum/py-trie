import pytest

from trie.exceptions import MissingTrieNode


@pytest.mark.parametrize(
    'valid_prefix',
    (
        None,
        (),
        (0, 0, 0),
        (0xf, ) * 128,  # no length limit on the prefix
    ),
)
def test_valid_MissingTrieNode_prefix(valid_prefix):
    exception = MissingTrieNode(b'', b'', b'', valid_prefix)
    assert exception.prefix == valid_prefix


@pytest.mark.parametrize(
    'invalid_prefix, exception',
    (
        ((b'F', ), ValueError),
        (b'F', TypeError),
        ((b'\x00', ), ValueError),
        ((b'\x0F', ), ValueError),
        (0, TypeError),
        (0xf, TypeError),
        ((0, 0x10), ValueError),
        ((0, -1), ValueError),
    ),
)
def test_invalid_MissingTrieNode_prefix(invalid_prefix, exception):
    with pytest.raises(exception):
        MissingTrieNode(b'', b'', b'', invalid_prefix)
