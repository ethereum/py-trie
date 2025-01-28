import pytest
import json
import os

from hypothesis import (
    example,
    given,
    strategies as st,
)
import rlp

from trie import (
    HexaryTrie,
)
from trie.exceptions import (
    MissingTraversalNode,
)
from trie.iter import (
    NodeIterator,
)
from trie.tools.strategies import (
    random_trie_strategy,
    trie_from_keys,
    trie_keys_with_extensions,
)
from trie.utils.nibbles import (
    nibbles_to_bytes,
)
from trie.utils.nodes import (
    is_extension_node,
)

TESTS_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_PROJECT_DIR = os.path.dirname(TESTS_DIR)
NEXT_PREV_FIXTURE_PATH = os.path.join(
    ROOT_PROJECT_DIR, "fixtures", "TrieTests", "trietestnextprev.json"
)
RAW_NEXT_PREV_FIXTURES = [
    (os.path.basename(NEXT_PREV_FIXTURE_PATH), json.load(open(NEXT_PREV_FIXTURE_PATH)))
]
NEXT_PREV_FIXTURES = [
    (f"{fixture_filename}:{key}", fixtures[key])
    for fixture_filename, fixtures in RAW_NEXT_PREV_FIXTURES
    for key in sorted(fixtures.keys())
]


@pytest.mark.parametrize(
    "fixture_name,fixture",
    NEXT_PREV_FIXTURES,
)
def test_trie_next_prev_using_fixtures(fixture_name, fixture):
    trie = HexaryTrie(db={})
    for k in fixture["in"]:
        k = k.encode("utf-8")
        trie[k] = k

    iterator = NodeIterator(trie)
    for point, _, nxt in fixture["tests"]:
        point = point.encode("utf-8")
        nxt = nxt.encode("utf-8")
        if nxt == b"":
            nxt = None
        assert nxt == iterator.next(point)


@given(random_trie_strategy())
def test_iter_next(random_trie):
    trie, contents = random_trie
    iterator = NodeIterator(trie)

    key = iterator.next()

    if len(contents) == 0:
        assert key is None
    else:
        assert key is not None

        visited = []
        while key is not None:
            visited.append(key)
            key = iterator.next(key)
        assert visited == sorted(contents.keys())


@given(trie_keys_with_extensions(), st.integers(min_value=1, max_value=33))
def test_iter_keys(trie_keys, min_value_length):
    trie, contents = trie_from_keys(trie_keys, min_value_length)
    node_iterator = NodeIterator(trie)
    visited = []
    for key in node_iterator.keys():
        visited.append(key)
    assert visited == sorted(contents.keys())


@given(trie_keys_with_extensions(), st.integers(min_value=1, max_value=33))
@example(
    # Test when the values are in reversed order (so that a larger value appears
    #   earlier in a trie). Test that values sorted in key order, not value order.
    trie_keys=(b"\x01\x00", b"\x01\x00\x00"),
    min_value_length=6,
)
def test_iter_values(trie_keys, min_value_length):
    trie, contents = trie_from_keys(trie_keys, min_value_length)
    node_iterator = NodeIterator(trie)
    visited = []
    for value in node_iterator.values():
        visited.append(value)
    values_sorted_by_key = [
        val for _, val in sorted(contents.items())  # only look at value but sort by key
    ]
    assert visited == values_sorted_by_key


@given(trie_keys_with_extensions(), st.integers(min_value=1, max_value=33))
def test_iter_items(trie_keys, min_value_length):
    trie, contents = trie_from_keys(trie_keys, min_value_length)
    node_iterator = NodeIterator(trie)
    visited = []
    for item in node_iterator.items():
        visited.append(item)
    assert visited == sorted(contents.items())


@given(trie_keys_with_extensions(), st.integers(min_value=1, max_value=33))
def test_iter_nodes(trie_keys, min_value_length):
    trie, contents = trie_from_keys(trie_keys, min_value_length)
    visited = set()
    for prefix, node in NodeIterator(trie).nodes():
        # Save a copy of the encoded node to check against the database
        visited.add(rlp.encode(node.raw))
        # Verify that navigating to the node directly
        # returns the same node as this iterator
        assert node == trie.traverse(prefix)
        # Double-check that if the node stores a value, then the implied key matches
        if node.value:
            iterated_key = nibbles_to_bytes(prefix + node.suffix)
            assert node.value == contents[iterated_key]

    # All nodes should be visited
    # Note that because of node embedding, the node iterator will return more nodes
    # than actually exist in the underlying DB (it returns embedded nodes as if they
    # were not embedded). So we can't simply test that trie.db.values()
    # equals visited here.
    assert set(trie.db.values()) - visited == set()


def test_iter_error():
    trie = HexaryTrie({})
    trie[b"cat"] = b"cat"
    trie[b"dog"] = b"dog"
    trie[b"bird"] = b"bird"
    raw_root_node = trie.root_node.raw
    assert is_extension_node(raw_root_node)
    node_to_remove = raw_root_node[1]
    trie.db.pop(node_to_remove)
    iterator = NodeIterator(trie)
    key = b""
    with pytest.raises(MissingTraversalNode):
        while key is not None:
            key = iterator.next(key)
