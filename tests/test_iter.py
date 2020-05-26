import json
import os

import pytest

from hypothesis import (
    given,
    settings,
    strategies,
)

from trie import HexaryTrie
from trie.iter import NodeIterator
from trie.utils.nodes import is_extension_node
from .utils import make_random_trie


ROOT_PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
NEXT_PREV_FIXTURE_PATH = os.path.join(
    ROOT_PROJECT_DIR, 'fixtures', 'TrieTests', 'trietestnextprev.json')
RAW_NEXT_PREV_FIXTURES = [
    (os.path.basename(NEXT_PREV_FIXTURE_PATH), json.load(open(NEXT_PREV_FIXTURE_PATH)))
]
NEXT_PREV_FIXTURES = [
    ("{0}:{1}".format(fixture_filename, key), fixtures[key])
    for fixture_filename, fixtures in RAW_NEXT_PREV_FIXTURES
    for key in sorted(fixtures.keys())
]


@pytest.mark.parametrize(
    'fixture_name,fixture', NEXT_PREV_FIXTURES,
)
def test_trie_next_prev_using_fixtures(fixture_name, fixture):
    trie = HexaryTrie(db={})
    for k in fixture['in']:
        k = k.encode('utf-8')
        trie[k] = k

    iterator = NodeIterator(trie)
    for point, _, nxt in fixture['tests']:
        point = point.encode('utf-8')
        nxt = nxt.encode('utf-8')
        if nxt == b'':
            nxt = None
        assert nxt == iterator.next(point)


@given(random=strategies.randoms())
@settings(max_examples=10, deadline=500)
def test_iter(random):
    trie, contents = make_random_trie(random)
    iterator = NodeIterator(trie)
    visited = []
    key = iterator.next(b'')
    assert key is not None
    while key is not None:
        visited.append(key)
        key = iterator.next(key)
    assert visited == sorted(contents.keys())


def test_iter_error():
    trie = HexaryTrie({})
    trie[b'cat'] = b'cat'
    trie[b'dog'] = b'dog'
    trie[b'bird'] = b'bird'
    raw_root_node = trie.root_node.raw
    assert is_extension_node(raw_root_node)
    node_to_remove = raw_root_node[1]
    trie.db.pop(node_to_remove)
    iterator = NodeIterator(trie)
    key = b''
    with pytest.raises(KeyError):
        while key is not None:
            key = iterator.next(key)
