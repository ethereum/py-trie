from collections import defaultdict
import fnmatch
import itertools
import json
import os

from eth_utils import (
    decode_hex,
    encode_hex,
    is_0x_prefixed,
    text_if_str,
    to_bytes,
)
import pytest

from trie import HexaryTrie
from trie.constants import BLANK_NODE_HASH
from trie.exceptions import (
    MissingTrieNode,
    ValidationError,
)
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


def assert_proof(trie, key):
    proof = trie.get_proof(key)
    assert len(proof) > 0

    proof_value = HexaryTrie.get_from_proof(trie.root_hash, key, proof)
    assert proof_value == trie.get(key)


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
            assert_proof(trie, key)

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
        assert_proof(trie, valid_proof_key)

    for absence_proof_key in deleted:
        assert_proof(trie, absence_proof_key)


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


def test_hexary_trie_at_root_lookups():
    changes = ((b'ab', b'b'*32), (b'ac', b'c'*32), (b'ac', None), (b'ad', b'd'*32))

    # track which key is expected to be present in which root
    expected_by_root = defaultdict(set)
    missing_by_root = defaultdict(set)

    trie = HexaryTrie({})
    for key, val in changes:
        if val is None:
            del trie[key]
            missing_by_root[trie.root_hash].add(key)
        else:
            trie[key] = val
            expected_by_root[trie.root_hash].add((key, val))

    # check that the values are still reachable at the old state roots
    for root_hash, expected_items in expected_by_root.items():
        for key, val in expected_items:
            with trie.at_root(root_hash) as snapshot:
                assert key in snapshot
                assert snapshot[key] == val

    # check that missing values are not reachable at the old state roots
    for root_hash, missing_keys in missing_by_root.items():
        for key in missing_keys:
            with trie.at_root(root_hash) as snapshot:
                assert key not in snapshot


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
    with pytest.raises(MissingTrieNode) as excinfo:
        old_trie.root_node

    assert encode_hex(old_root_hash) in str(excinfo.value)


def test_squash_changes_can_still_access_underlying_deleted_data():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b'what floats on water?', b'very small rocks')
    old_root_hash = trie.root_hash

    with trie.squash_changes() as memory_trie:
        memory_trie.set(b'what floats on water?', b'a duck')

        # change to a root hash that the memory trie doesn't have anymore
        memory_trie.root_hash
        memory_trie.root_hash = old_root_hash

        assert memory_trie[b'what floats on water?'] == b'very small rocks'


def test_squash_changes_raises_correct_error_on_new_deleted_data():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b'what floats on water?', b'very small rocks')

    with trie.squash_changes() as memory_trie:
        memory_trie.set(b'what floats on water?', b'a duck')
        middle_root_hash = memory_trie.root_hash

        memory_trie.set(b'what floats on water?', b'ooooohh')
        memory_trie.root_hash

        # change to a root hash that the memory trie doesn't have anymore
        memory_trie.root_hash = middle_root_hash

        with pytest.raises(MissingTrieNode):
            memory_trie[b'what floats on water?']


def test_squash_changes_raises_correct_error_on_underlying_missing_data():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b'what floats on water?', b'very small rocks')
    old_root_hash = trie.root_hash

    # what if the root node hash is missing from the beginning?
    del db[old_root_hash]

    # the appropriate exception should be raised, when squashing changes
    with trie.squash_changes() as memory_trie:
        with pytest.raises(MissingTrieNode):
            memory_trie[b'what floats on water?']


def test_squash_changes_reverts_trie_root_on_exception():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b'\x00', b'B'*32)
    trie.set(b'\xff', b'C'*32)
    old_root_hash = trie.root_hash

    # delete the node that will be used during trie fixup
    del db[trie.root_node[0xf]]

    with pytest.raises(MissingTrieNode):
        with trie.squash_changes() as memory_trie:
            try:
                memory_trie[b'\x11'] = b'new val'
            except MissingTrieNode:
                assert False, "Only the squash_changes context exit should raise this exception"

            del memory_trie[b'\xff']

    assert trie.root_hash == old_root_hash


def test_hexary_trie_missing_node():
    db = {}
    trie = HexaryTrie(db, prune=True)

    key1 = to_bytes(0x0123)
    trie.set(key1, b'use a value long enough that it must be hashed according to trie spec')

    key2 = to_bytes(0x1234)
    trie.set(key2, b'val2')

    trie_root_hash = trie.root_hash

    # delete first child of the root
    root_node = trie.root_node

    first_child_hash = root_node[0]

    del db[first_child_hash]

    # Get exception with relevant info about key
    with pytest.raises(MissingTrieNode) as exc_info:
        trie.get(key1)
    message = str(exc_info.value)

    assert encode_hex(key1) in message
    assert encode_hex(trie_root_hash) in message
    assert encode_hex(first_child_hash) in message

    # Get exception when trying to write into key with shared prefix
    key1_shared_prefix = to_bytes(0x0234)
    with pytest.raises(MissingTrieNode) as set_exc_info:
        trie.set(key1_shared_prefix, b'val2')

    set_exc_message = str(set_exc_info.value)

    assert encode_hex(key1_shared_prefix) in set_exc_message
    assert encode_hex(trie_root_hash) in set_exc_message
    assert encode_hex(first_child_hash) in set_exc_message

    # Get exception when trying to delete key with missing data
    with pytest.raises(MissingTrieNode) as delete_exc_info:
        trie.delete(key1)

    delete_exc_message = str(delete_exc_info.value)

    assert encode_hex(key1) in delete_exc_message
    assert encode_hex(trie_root_hash) in delete_exc_message
    assert encode_hex(first_child_hash) in delete_exc_message

    # Get exception when checking if key exists with missing data
    key1_shared_prefix2 = to_bytes(0x0345)
    with pytest.raises(MissingTrieNode) as existance_exc_info:
        key1_shared_prefix2 in trie

    existance_exc_message = str(existance_exc_info.value)

    assert encode_hex(key1_shared_prefix2) in existance_exc_message
    assert encode_hex(trie_root_hash) in existance_exc_message
    assert encode_hex(first_child_hash) in existance_exc_message

    # Other keys are still accessible
    assert trie.get(key2) == b'val2'


def test_hexary_trie_raises_on_pruning_snapshot():
    trie = HexaryTrie({}, prune=True)

    with pytest.raises(ValidationError):
        with trie.at_root(BLANK_NODE_HASH):
            pass
