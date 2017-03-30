import pytest

from trie.utils.nodes import (
    get_common_prefix_length,
    consume_common_prefix,
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
