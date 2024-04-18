import pytest

from trie.exceptions import (
    MissingTraversalNode,
    MissingTrieNode,
    TraversedPartialPath,
    ValidationError,
)
from trie.typing import (
    Nibbles,
)
from trie.utils.nodes import (
    annotate_node,
    compute_extension_key,
    compute_leaf_key,
)


@pytest.mark.parametrize(
    "valid_prefix",
    (
        None,
        (),
        (0, 0, 0),
        (0xF,) * 128,  # no length limit on the prefix
    ),
)
def test_valid_MissingTrieNode_prefix(valid_prefix):
    exception = MissingTrieNode(b"", b"", b"", valid_prefix)
    assert exception.prefix == valid_prefix
    if valid_prefix is not None:
        assert str(Nibbles(valid_prefix)) in repr(exception)


@pytest.mark.parametrize(
    "invalid_prefix, exception",
    (
        ((b"F",), ValueError),
        (b"F", TypeError),
        ((b"\x00",), ValueError),
        ((b"\x0F",), ValueError),
        (0, TypeError),
        (0xF, TypeError),
        ((0, 0x10), ValueError),
        ((0, -1), ValueError),
    ),
)
def test_invalid_MissingTrieNode_prefix(invalid_prefix, exception):
    with pytest.raises(exception):
        MissingTrieNode(b"", b"", b"", invalid_prefix)


@pytest.mark.parametrize(
    "valid_nibbles",
    (
        (),
        (0, 0, 0),
        (0xF,) * 128,  # no length limit on the nibbles
    ),
)
def test_valid_MissingTraversalNode_nibbles(valid_nibbles):
    exception = MissingTraversalNode(b"", valid_nibbles)
    assert exception.nibbles_traversed == valid_nibbles
    assert str(Nibbles(valid_nibbles)) in repr(exception)


@pytest.mark.parametrize(
    "invalid_nibbles, exception",
    (
        (None, TypeError),
        ((b"F",), ValueError),
        (b"F", TypeError),
        ((b"\x00",), ValueError),
        ((b"\x0F",), ValueError),
        (0, TypeError),
        (0xF, TypeError),
        ((0, 0x10), ValueError),
        ((0, -1), ValueError),
    ),
)
def test_invalid_MissingTraversalNode_nibbles(invalid_nibbles, exception):
    with pytest.raises(exception):
        MissingTraversalNode(b"", invalid_nibbles)


@pytest.mark.parametrize(
    "valid_nibbles",
    (
        (),
        (0, 0, 0),
        (0xF,) * 128,  # no length limit on the nibbles
    ),
)
@pytest.mark.parametrize("key_encoding", (compute_extension_key, compute_leaf_key))
def test_valid_TraversedPartialPath_traversed_nibbles(valid_nibbles, key_encoding):
    some_node_key = (1, 2)
    node = annotate_node([key_encoding(some_node_key), b"random-value"])
    exception = TraversedPartialPath(valid_nibbles, node, some_node_key[:1])
    assert exception.nibbles_traversed == valid_nibbles
    assert str(Nibbles(valid_nibbles)) in repr(exception)


@pytest.mark.parametrize(
    "invalid_nibbles, exception",
    (
        (None, TypeError),
        ((b"F",), ValueError),
        (b"F", TypeError),
        ((b"\x00",), ValueError),
        ((b"\x0F",), ValueError),
        (0, TypeError),
        (0xF, TypeError),
        ((0, 0x10), ValueError),
        ((0, -1), ValueError),
    ),
)
def test_invalid_TraversedPartialPath_traversed_nibbles(invalid_nibbles, exception):
    with pytest.raises(exception):
        TraversedPartialPath(invalid_nibbles, annotate_node(b""), (1,))


@pytest.mark.parametrize(
    "valid_nibbles",
    (
        (0, 0, 0),
        (0xF,) * 128,  # no length limit on the nibbles
    ),
)
@pytest.mark.parametrize("key_encoding", (compute_extension_key, compute_leaf_key))
def test_valid_TraversedPartialPath_untraversed_nibbles(valid_nibbles, key_encoding):
    # This exception means that the actual node key should have more than the
    # untraversed amount. So we simulate some longer key for the given node
    longer_key = valid_nibbles + (0,)
    node = annotate_node([key_encoding(longer_key), b"random-value"])
    exception = TraversedPartialPath((), node, valid_nibbles)
    assert exception.untraversed_tail == valid_nibbles
    assert str(Nibbles(valid_nibbles)) in repr(exception)


@pytest.mark.parametrize("key_encoding", (compute_extension_key, compute_leaf_key))
def test_TraversedPartialPath_keeps_node_value(key_encoding):
    node_key = (0, 0xF, 9)
    untraversed_tail = node_key[:1]
    remaining_key = node_key[1:]
    node_value = b"unicorns"
    node = annotate_node([key_encoding(node_key), node_value])
    tpp = TraversedPartialPath(node_key, node, untraversed_tail)
    simulated_node = tpp.simulated_node
    assert simulated_node.raw[1] == node_value
    if key_encoding is compute_leaf_key:
        assert simulated_node.sub_segments == ()
        assert simulated_node.suffix == remaining_key
        assert simulated_node.raw[0] == compute_leaf_key(remaining_key)
        assert simulated_node.value == node_value
    elif key_encoding is compute_extension_key:
        assert simulated_node.sub_segments == (remaining_key,)
        assert simulated_node.suffix == ()
        assert simulated_node.raw[0] == compute_extension_key(remaining_key)
    else:
        raise Exception("Unsupported way to encode keys: {key_encoding}")


@pytest.mark.parametrize(
    "invalid_nibbles, node_key, exception",
    (
        ((), (), ValueError),
        (None, (), TypeError),
        ((b"F",), (), ValueError),
        (b"F", (), TypeError),
        ((b"\x00",), (), ValueError),
        ((b"\x0F",), (), ValueError),
        (0, (), TypeError),
        (0xF, (), TypeError),
        ((0, 0x10), (), ValueError),
        ((0, -1), (), ValueError),
        # There must be some kind of tail
        ((), (1,), ValueError),
        # The untraversed tail must be a prefix of the node key
        ((0,), (1,), ValidationError),
        # The untraversed tail must not be the full length of the node key
        ((1,), (1,), ValidationError),
    ),
)
@pytest.mark.parametrize("key_encoding", (compute_extension_key, compute_leaf_key))
def test_invalid_TraversedPartialPath_untraversed_nibbles(
    invalid_nibbles, node_key, exception, key_encoding
):
    if node_key == ():
        node = annotate_node(b"")
    else:
        node = annotate_node([key_encoding(node_key), b"some-val"])

    # Handle special case: leaf nodes are permitted to have the
    # untraversed tail equal the suffix
    if len(node.suffix) > 0 and node.suffix == invalid_nibbles:
        # So in this one case, make sure we don't raise an exception
        TraversedPartialPath((), node, invalid_nibbles)
    else:
        with pytest.raises(exception):
            TraversedPartialPath((), node, invalid_nibbles)
