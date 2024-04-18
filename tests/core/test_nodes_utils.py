import pytest

from trie.exceptions import (
    InvalidNode,
    ValidationError,
)
from trie.utils.nodes import (
    consume_common_prefix,
    encode_branch_node,
    encode_kv_node,
    encode_leaf_node,
    get_common_prefix_length,
    parse_node,
)


@pytest.mark.parametrize(
    "left,right,expected",
    (
        ([], [], 0),
        ([], [1], 0),
        ([1], [1], 1),
        ([1], [1, 1], 1),
        ([1, 2], [1, 1], 1),
        ([1, 2, 3, 4, 5, 6], [1, 2, 3, 5, 6], 3),
    ),
)
def test_get_common_prefix_length(left, right, expected):
    actual_a = get_common_prefix_length(left, right)
    actual_b = get_common_prefix_length(right, left)
    assert actual_a == actual_b == expected


@pytest.mark.parametrize(
    "left,right,expected",
    (
        ([], [], ([], [], [])),
        ([], [1], ([], [], [1])),
        ([1], [1], ([1], [], [])),
        ([1], [1, 1], ([1], [], [1])),
        ([1, 2], [1, 1], ([1], [2], [1])),
        ([1, 2, 3, 4, 5, 6], [1, 2, 3, 5, 6], ([1, 2, 3], [4, 5, 6], [5, 6])),
    ),
)
def test_consume_common_prefix(left, right, expected):
    actual_a = consume_common_prefix(left, right)
    actual_b = consume_common_prefix(right, left)
    expected_b = (expected[0], expected[2], expected[1])
    assert actual_a == expected
    assert actual_b == expected_b


@pytest.mark.parametrize(
    "node,expected_output",
    (
        (
            b"\x00\x03\x04\x05\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            (
                0,
                b"\x00\x00\x01\x01\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01",  # noqa: E501
                b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            ),
        ),
        (
            b"\x01\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            (
                1,
                b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
                b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            ),
        ),
        (b"\x02value", (2, None, b"value")),
        (b"", None),
        (None, None),
        (
            b"\x00\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            None,
        ),
        (
            b"\x01\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            None,
        ),
        (
            b"\x01\x02\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            None,
        ),
        (b"\x02", None),
    ),
)
def test_binary_trie_node_parsing(node, expected_output):
    if expected_output:
        assert expected_output == parse_node(node)
    else:
        with pytest.raises(InvalidNode):
            parse_node(node)


@pytest.mark.parametrize(
    "keypath,node,expected_output",
    (
        (
            b"\x00",
            b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            b"\x00\x10\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
        ),
        (
            b"",
            b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            None,
        ),
        (
            b"\x00",
            b"\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            None,
        ),
        (b"\x00", 12345, None),
        (b"\x00", range(32), None),
        (
            b"\x01",
            b"\x00\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            None,
        ),
        (b"\x02", b"", None),
    ),
)
def test_encode_binary_trie_kv_node(keypath, node, expected_output):
    if expected_output:
        assert expected_output == encode_kv_node(keypath, node)
    else:
        with pytest.raises(ValidationError):
            encode_kv_node(keypath, node)


@pytest.mark.parametrize(
    "left_child_node_hash,right_child_node_hash,expected_output",
    (
        (
            b"\xc8\x9e\xfd\xaaT\xc0\xf2\x0cz\xdfa(\x82\xdf\tP\xf5\xa9Qc~\x03\x07\xcd\xcbLg/)\x8b\x8b\xc6",  # noqa: E501
            b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            (
                b"\x01\xc8\x9e\xfd\xaaT\xc0\xf2\x0cz\xdfa(\x82\xdf\tP\xf5\xa9Qc~\x03\x07\xcd\xcbLg/)\x8b\x8b\xc6\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"  # noqa: E501
            ),
        ),
        (
            b"",
            b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            None,
        ),
        (
            b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            b"\x01",
            None,
        ),
        (
            b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p",  # noqa: E501
            12345,
            None,
        ),
        ([3] * 32, [4] * 32, None),
        (b"\x01" * 33, b"\x01" * 32, None),
    ),
)
def test_encode_binary_trie_branch_node(
    left_child_node_hash, right_child_node_hash, expected_output
):
    if expected_output:
        assert expected_output == encode_branch_node(
            left_child_node_hash, right_child_node_hash
        )
    else:
        with pytest.raises(ValidationError):
            encode_branch_node(left_child_node_hash, right_child_node_hash)


@pytest.mark.parametrize(
    "value,expected_output",
    (
        (b"\x03\x04\x05", b"\x02\x03\x04\x05"),
        (b"", None),
        (12345, None),
        (range(5), None),
    ),
)
def test_encode_binary_trie_leaf_node(value, expected_output):
    if expected_output:
        assert expected_output == encode_leaf_node(value)
    else:
        with pytest.raises(ValidationError):
            encode_leaf_node(value)
