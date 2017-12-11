import pytest

from trie.exceptions import (
    InvalidNode,
    ValidationError,
)
from trie.utils.nodes import (
    get_common_prefix_length,
    consume_common_prefix,
    parse_node,
    encode_kv_node,
    encode_branch_node,
    encode_leaf_node,
)


@pytest.mark.parametrize(
    'left,right,expected',
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
    'left,right,expected',
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
    'valid_node',
    (
        (b"\x00\x03\x04\x05\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
        (b"\x01\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
        (b"\x02value"),  # noqa: E501
    ),
)
def test_binary_trie_node_parsing_with_valid_input(valid_node):
    parse_node(valid_node)


@pytest.mark.parametrize(
    'invalid_node',
    (
        (b''),
        (None),
        (b"\x00\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
        (b"\x01\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
        (b"\x01\x02\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
        (b'\x02'),
    ),
)
def test_binary_trie_node_parsing_with_invalid_input(invalid_node):
    with pytest.raises(InvalidNode):
        parse_node(invalid_node)


@pytest.mark.parametrize(
    'keypath,valid_value',
    (
        (b'\x00', b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
    ),
)
def test_encode_binary_trie_kv_node_with_valid_input(keypath, valid_value):
    encode_kv_node(keypath, valid_value)
        
        
@pytest.mark.parametrize(
    'keypath,invalid_node',
    (
        (b'', b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
        (b'\x00', b"\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
        (b'\x00', 12345),
        (b'\x00', range(32)),
        (b'\x01', b"\x00\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
        (b'\x02', b''),
    ),
)
def test_encode_binary_trie_kv_node_with_invalid_input(keypath, invalid_node):
    with pytest.raises(ValidationError):
        encode_kv_node(keypath, invalid_node)


@pytest.mark.parametrize(
    'left_child_node_hash,right_child_node_hash',
    (
        (b'\xc8\x9e\xfd\xaaT\xc0\xf2\x0cz\xdfa(\x82\xdf\tP\xf5\xa9Qc~\x03\x07\xcd\xcbLg/)\x8b\x8b\xc6', b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
    ),
)
def test_encode_binary_trie_branch_node_with_valid_input(left_child_node_hash, right_child_node_hash):
    encode_branch_node(left_child_node_hash, right_child_node_hash)
        
        
@pytest.mark.parametrize(
    'invalid_left_child_node_hash,invalid_right_child_node_hash',
    (
        (b'', b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"),  # noqa: E501
        (b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p", b'\x01'),  # noqa: E501
        (b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p", 12345),  # noqa: E501
        ([3] * 32, [4] * 32),
        (b'\x01' * 33, b'\x01' * 32),
    ),
)
def test_encode_binary_trie_branch_node_with_invalid_input(invalid_left_child_node_hash, invalid_right_child_node_hash):
    with pytest.raises(ValidationError):
        encode_branch_node(invalid_left_child_node_hash, invalid_right_child_node_hash)


@pytest.mark.parametrize(
    'valid_value',
    (
        (b'\x01\x02x\03'),
    ),
)
def test_encode_binary_trie_leaf_node_with_invalid_input(valid_value):
    encode_leaf_node(valid_value)
        
        
@pytest.mark.parametrize(
    'invalid_value',
    (
        (b''),
        (12345),
        (range(5)),
    ),
)
def test_encode_binary_trie_leaf_node_with_invalid_input(invalid_value):
    with pytest.raises(ValidationError):
        encode_leaf_node(invalid_value)
