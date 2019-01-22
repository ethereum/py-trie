import pytest

import itertools
import fnmatch
import json
import os

from eth_utils import (
    is_0x_prefixed,
    decode_hex,
    text_if_str,
    to_bytes,
)

from trie import HexaryTrie
from trie.utils.nodes import (
    decode_node,
)


def normalize_fixture(fixture):
    normalized_fixture = {
        'in': tuple(
            (
                decode_hex(key) if is_0x_prefixed(key) else text_if_str(to_bytes, key),
                (
                    decode_hex(value) if is_0x_prefixed(value) else text_if_str(to_bytes, value)
                ) if value is not None else None,
            )
            for key, value
            in (fixture['in'].items() if isinstance(fixture['in'], dict) else fixture['in'])
        ),
        'root': decode_hex(fixture['root'])
    }
    return normalized_fixture


ROOT_PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))


def recursive_find_files(base_dir, pattern):
    for dirpath, _, filenames in os.walk(base_dir):
        for filename in filenames:
            if fnmatch.fnmatch(filename, pattern):
                yield os.path.join(dirpath, filename)


BASE_FIXTURE_PATH = os.path.join(ROOT_PROJECT_DIR, 'fixtures', 'TrieTests')


FIXTURES_PATHS = tuple(recursive_find_files(BASE_FIXTURE_PATH, "trietest.json"))


def test_fixtures_exist():
    assert os.path.exists(BASE_FIXTURE_PATH)
    assert FIXTURES_PATHS


RAW_FIXTURES = tuple(
    (
        os.path.basename(fixture_path),
        json.load(open(fixture_path)),
    ) for fixture_path in FIXTURES_PATHS
)


FIXTURES_NORMALIZED = tuple(
    (
        "{0}:{1}".format(fixture_filename, key),
        normalize_fixture(fixtures[key]),
    )
    for fixture_filename, fixtures in RAW_FIXTURES
    for key in sorted(fixtures.keys())
)


def get_expected_results(fixture):
    keys_and_values = fixture['in']
    deletes = tuple(k for k, v in keys_and_values if v is None)
    remaining = {
        k: v
        for k, v
        in keys_and_values
        if k not in deletes
    }
    return remaining, deletes


def permute_fixtures(fixtures):
    for fixture_name, fixture in fixtures:
        final_mapping, deleted_keys = get_expected_results(fixture)
        final_root = fixture['root']
        for update_series in itertools.islice(itertools.permutations(fixture['in']), 100):
            yield (fixture_name, update_series, final_mapping, deleted_keys, final_root)


FIXTURES_PERMUTED = tuple(permute_fixtures(FIXTURES_NORMALIZED))


def trim_long_bytes(param):
    if isinstance(param, bytes) and len(param) > 3:
        return repr('0x' + param[:3].hex() + '...')


@pytest.mark.parametrize(
    'name, updates, expected, deleted, final_root',
    FIXTURES_PERMUTED,
    ids=trim_long_bytes,
)
def test_trie_using_fixtures(name, updates, expected, deleted, final_root):
    trie = HexaryTrie(db={})

    for key, value in updates:
        if value is None:
            del trie[key]
        else:
            trie[key] = value

    for key in deleted:
        del trie[key]

    for key, expected_value in expected.items():
        assert key in trie
        actual_value = trie[key]
        assert actual_value == expected_value

    for key in deleted:
        assert key not in trie

    actual_root = trie.root_hash
    assert actual_root == final_root

    for valid_proof_key in expected:
        valid_proof = trie.get_proof(valid_proof_key)
        assert len(valid_proof) > 0

        valid_proof_value = HexaryTrie.get_from_proof(trie.root_hash, valid_proof_key, valid_proof)
        assert valid_proof_value == trie.get(valid_proof_key)

    for invalid_proof_key in deleted:
        with pytest.raises(KeyError):
            trie.get_proof(invalid_proof_key)


class KeyAccessLogger(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read_keys = set()

    def __getitem__(self, key):
        result = super().__getitem__(key)
        self.read_keys.add(key)
        return result

    def unread_keys(self):
        return self.keys() - self.read_keys


def test_hexary_trie_saves_each_root():
    changes = ((b'ab', b'b'*32), (b'ac', b'c'*32), (b'ac', None), (b'ad', b'd'*32))
    expected = ((b'ab', b'b'*32), (b'ad', b'd'*32))
    db = {}
    trie = HexaryTrie(db=db)
    for key, val in changes:
        if val is None:
            del trie[key]
        else:
            trie[key] = val

    # access all of the values in the trie, triggering reads for all the database keys
    # that support the final state
    flagged_usage_db = KeyAccessLogger(db)
    flag_trie = HexaryTrie(flagged_usage_db, root_hash=trie.root_hash)
    for key, val in expected:
        assert flag_trie[key] == val

    # the trie that doesn't prune will certainly have extra keys that aren't needed by
    # the state with the final root_hash
    unread = flagged_usage_db.unread_keys()
    assert len(unread) > 0


@pytest.mark.parametrize(
    'name, updates, expected, deleted, final_root',
    FIXTURES_PERMUTED,
    ids=trim_long_bytes,
)
def test_hexary_trie_saving_final_root(name, updates, expected, deleted, final_root):
    db = {}
    trie = HexaryTrie(db=db)
    with trie.squash_changes() as memory_trie:
        for key, value in updates:
            if value is None:
                del memory_trie[key]
            else:
                memory_trie[key] = value

        for key in deleted:
            del memory_trie[key]

    # access all of the values in the trie, triggering reads for all the database keys
    # that support the final state
    flagged_usage_db = KeyAccessLogger(db)
    flag_trie = HexaryTrie(flagged_usage_db, root_hash=trie.root_hash)
    for key, val in expected.items():
        assert flag_trie[key] == val

    # assert that no unnecessary database values were created
    unread = flagged_usage_db.unread_keys()
    straggler_data = {k: (db[k], decode_node(db[k])) for k in unread}
    assert len(unread) == 0, straggler_data

    actual_root = trie.root_hash
    assert actual_root == final_root


def test_hexary_trie_batch_save_keeps_last_root_data():
    db = {}
    trie = HexaryTrie(db)
    trie.set(b'what floats on water?', b'very small rocks')
    old_root_hash = trie.root_hash

    with trie.squash_changes() as memory_trie:
        memory_trie.set(b'what floats on water?', b'a duck')

    assert trie[b'what floats on water?'] == b'a duck'

    old_trie = HexaryTrie(db, root_hash=old_root_hash)
    assert old_trie[b'what floats on water?'] == b'very small rocks'


def test_hexary_trie_batch_save_drops_last_root_data_when_pruning():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b'what floats on water?', b'very small rocks')
    old_root_hash = trie.root_hash

    with trie.squash_changes() as memory_trie:
        memory_trie.set(b'what floats on water?', b'a duck')

    assert trie[b'what floats on water?'] == b'a duck'

    old_trie = HexaryTrie(db, root_hash=old_root_hash)
    with pytest.raises(KeyError):
        old_trie.root_node
