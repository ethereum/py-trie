import pytest

from trie.BaseNode import (
    LeafNode,
)


def test_insert():
    root = LeafNode((0, 1, 2, 3), "v1")
    root = root.insert_child((1, 2, 3, 4), "v2")
    root = root.insert_child((1, 2, 7, 8), "v3")
    root = root.insert_child((), "v4")
    assert root.get_value((1, 2, 3, 4)) == "v2"
    root = root.insert_child((1, 2, 3, 4), "v5")
    assert root.get_value((1, 2, 3, 4)) == "v5"


def test_delete():
    root = LeafNode((1, 2, 3), "v1")
    root = root.insert_child((1, 2, 4), "v2")
    root = root.insert_child((2, 2, 7), "v3")
    assert root.get_value((1, 2, 4)) == "v2"
    assert root.get_value((2, 2, 7)) == "v3"
    assert root.get_value((1, 2, 3)) == "v1"
    root = root.delete_value((1, 2, 3))

    with pytest.raises(Exception):
        root.get_value((1, 2, 3))
