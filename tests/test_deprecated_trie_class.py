import pytest

from trie import Trie


def test_deprecated_trie():
    with pytest.warns(DeprecationWarning):
        trie = Trie(db={})

    trie[b'foo'] = b'bar'
    assert b'foo' in trie
    assert trie[b'foo'] == b'bar'
