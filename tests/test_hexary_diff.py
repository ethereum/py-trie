import pytest

from trie import HexaryTrie
from trie.utils.db import (
    KeyAccessLogger,
)


@pytest.mark.parametrize(
    'items1, items2, expected_key_diffs',
    (
        ([], [], {}),
        (
            [(b'a', b'A')],
            [],
            {b'a': (b'A', None)},
        ),
        (
            [],
            [(b'a', b'A')],
            {b'a': (None, b'A')},
        ),
        (
            [(b'a', b'A')],
            [(b'b', b'B')],
            {b'a': (b'A', None), b'b': (None, b'B')},
        ),
        (
            [(b'aa', b'A')],
            [(b'aa', b'A'), (b'ab', b'B')],
            {b'ab': (None, b'B')},
        ),
        (
            [(b'\x0a', b'A'), (b'\x1a', b'B')],
            [(b'\x0a', b'A'), (b'\x1a', b'B'), (b'\x2a', b'C')],
            {b'\x2a': (None, b'C')},
        ),
        (
            [(b'\x0a', b'A'), (b'\x0b', b'B')],
            [(b'\x0ac', b'C')],
            {
                b'\x0a': (b'A', None),
                b'\x0b': (b'B', None),
                b'\x0ac': (None, b'C'),
            },
        ),
        (
            [(b'\x0a', b'A' * 33), (b'\x0b', b'B' * 33)],
            [(b'\x0ac', b'C' * 33)],
            {
                b'\x0a': (b'A' * 33, None),
                b'\x0b': (b'B' * 33, None),
                b'\x0ac': (None, b'C' * 33),
            },
        ),
    ),
)
def test_hexary_diff(items1, items2, expected_key_diffs):
    db1 = {}
    trie1 = HexaryTrie(db1)
    db2 = {}
    trie2 = HexaryTrie(db2)
    for key, val in items1:
        trie1[key] = val
    for key, val in items2:
        trie2[key] = val

    key_diffs = HexaryTrie.diff(trie1, trie2)
    assert key_diffs == expected_key_diffs

    logger1db = KeyAccessLogger(db1)
    logger1 = HexaryTrie(logger1db, trie1.root_hash)
    logger2db = KeyAccessLogger(db2)
    logger2 = HexaryTrie(logger2db, trie2.root_hash)
    for key, (val1, val2) in key_diffs.items():
        # trigger reads to the relavant (diffed) keys
        logger1[key]
        logger2[key]

    proof_only_db1 = {key: db1[key] for key in logger1db.read_keys}
    proof_only_db2 = {key: db2[key] for key in logger2db.read_keys}

    # make sure you don't get KeyErrors when creating the same diff from only the proof:
    proof_only_trie1 = HexaryTrie(proof_only_db1, trie1.root_hash)
    proof_only_trie2 = HexaryTrie(proof_only_db2, trie2.root_hash)
    proof_only_diff = HexaryTrie.diff(proof_only_trie1, proof_only_trie2)
    # also make sure you get the same diff
    assert proof_only_diff == key_diffs

'''
        (
            [(b'aa', b'A' * 33)],
            [(b'aa', b'A' * 33), (b'ab', b'B' * 33)],
            {b'ab': (None, b'B' * 33)},
        ),
        '''
