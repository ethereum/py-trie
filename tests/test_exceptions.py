import pytest

from trie.exceptions import (
    MissingTraversalNode,
    MissingTrieNode,
    TraversedPartialPath,
)
from trie.typing import Nibbles
from trie.utils.nodes import annotate_node


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
    if valid_prefix is not None:
        assert str(Nibbles(valid_prefix)) in repr(exception)


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


@pytest.mark.parametrize(
    'valid_nibbles',
    (
        (),
        (0, 0, 0),
        (0xf, ) * 128,  # no length limit on the nibbles
    ),
)
def test_valid_MissingTraversalNode_nibbles(valid_nibbles):
    exception = MissingTraversalNode(b'', valid_nibbles)
    assert exception.nibbles_traversed == valid_nibbles
    assert str(Nibbles(valid_nibbles)) in repr(exception)


@pytest.mark.parametrize(
    'invalid_nibbles, exception',
    (
        (None, TypeError),
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
def test_invalid_MissingTraversalNode_nibbles(invalid_nibbles, exception):
    with pytest.raises(exception):
        MissingTraversalNode(b'', invalid_nibbles)


@pytest.mark.parametrize(
    'valid_nibbles',
    (
        (),
        (0, 0, 0),
        (0xf, ) * 128,  # no length limit on the nibbles
    ),
)
def test_valid_TraversedPartialPath_nibbles(valid_nibbles):
    exception = TraversedPartialPath(valid_nibbles, b'')
    assert exception.nibbles_traversed == valid_nibbles
    assert str(Nibbles(valid_nibbles)) in repr(exception)


@pytest.mark.parametrize(
    'invalid_nibbles, exception',
    (
        (None, TypeError),
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
def test_invalid_TraversedPartialPath_nibbles(invalid_nibbles, exception):
    with pytest.raises(exception):
        TraversedPartialPath(invalid_nibbles, annotate_node(b''))
