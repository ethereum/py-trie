import pytest

import itertools
import fnmatch
import json
import os

from eth_utils import (
    is_0x_prefixed,
    decode_hex,
    force_bytes,
)

from trie import (
    Trie,
)
from trie.db.memory import (
    MemoryDB,
)


def normalize_fixture(fixture):
    normalized_fixture = {
        'in': tuple(
            (
                decode_hex(key) if is_0x_prefixed(key) else force_bytes(key),
                (
                    decode_hex(value) if is_0x_prefixed(value) else force_bytes(value)
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


RAW_FIXTURES = tuple(
    (
        os.path.basename(fixture_path),
        json.load(open(fixture_path)),
    ) for fixture_path in FIXTURES_PATHS
)


FIXTURES = tuple(
    (
        "{0}:{1}".format(fixture_filename, key),
        normalize_fixture(fixtures[key]),
    )
    for fixture_filename, fixtures in RAW_FIXTURES
    for key in sorted(fixtures.keys())
)


@pytest.mark.parametrize(
    'fixture_name,fixture', FIXTURES,
)
def test_trie_using_fixtures(fixture_name, fixture):

    keys_and_values = fixture['in']
    deletes = tuple(k for k, v in keys_and_values if v is None)
    remaining = {
        k: v
        for k, v
        in keys_and_values
        if k not in deletes
    }

    for kv_permutation in itertools.islice(itertools.permutations(keys_and_values), 100):
        print("in it")
        trie = Trie(db=MemoryDB())

        for key, value in kv_permutation:
            if value is None:
                del trie[key]
            else:
                trie[key] = value
        for key in deletes:
            del trie[key]

        for key, expected_value in remaining.items():
            actual_value = trie[key]
            assert actual_value == expected_value

        expected_root = fixture['root']
        actual_root = trie.root_hash

        assert actual_root == expected_root
