import pytest
from collections import (
    defaultdict,
)
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
from hypothesis import (
    example,
    given,
    settings,
    strategies as st,
)
import rlp

from trie import (
    HexaryTrie,
)
from trie.constants import (
    BLANK_NODE_HASH,
)
from trie.exceptions import (
    MissingTraversalNode,
    MissingTrieNode,
    TraversedPartialPath,
    ValidationError,
)
from trie.utils.nodes import (
    decode_node,
)


def normalize_fixture(fixture):
    normalized_fixture = {
        "in": tuple(
            (
                decode_hex(key) if is_0x_prefixed(key) else text_if_str(to_bytes, key),
                (
                    decode_hex(value)
                    if is_0x_prefixed(value)
                    else text_if_str(to_bytes, value)
                )
                if value is not None
                else None,
            )
            for key, value in (
                fixture["in"].items()
                if isinstance(fixture["in"], dict)
                else fixture["in"]
            )
        ),
        "root": decode_hex(fixture["root"]),
    }
    return normalized_fixture


TESTS_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_PROJECT_DIR = os.path.dirname(TESTS_DIR)


def recursive_find_files(base_dir, pattern):
    for dirpath, _, filenames in os.walk(base_dir):
        for filename in filenames:
            if fnmatch.fnmatch(filename, pattern):
                yield os.path.join(dirpath, filename)


BASE_FIXTURE_PATH = os.path.join(ROOT_PROJECT_DIR, "fixtures", "TrieTests")


FIXTURES_PATHS = tuple(recursive_find_files(BASE_FIXTURE_PATH, "trietest.json"))


def test_fixtures_exist():
    assert os.path.exists(BASE_FIXTURE_PATH)
    assert FIXTURES_PATHS


RAW_FIXTURES = tuple(
    (
        os.path.basename(fixture_path),
        json.load(open(fixture_path)),
    )
    for fixture_path in FIXTURES_PATHS
)


FIXTURES_NORMALIZED = tuple(
    (
        f"{fixture_filename}:{key}",
        normalize_fixture(fixtures[key]),
    )
    for fixture_filename, fixtures in RAW_FIXTURES
    for key in sorted(fixtures.keys())
)


def get_expected_results(fixture):
    keys_and_values = fixture["in"]
    deletes = tuple(k for k, v in keys_and_values if v is None)
    remaining = {k: v for k, v in keys_and_values if k not in deletes}
    return remaining, deletes


def permute_fixtures(fixtures):
    for fixture_name, fixture in fixtures:
        final_mapping, deleted_keys = get_expected_results(fixture)
        final_root = fixture["root"]

        # fixtures that have duplicate keys (consecutive updates on the same key value)
        # that are not deleted in the final state cannot be permuted since the updates
        # must be applied in order.
        updates = fixture["in"]
        all_keys = sorted(entry[0] for entry in updates)
        duplicate_keys = sorted({key for key in all_keys if all_keys.count(key) > 1})
        if duplicate_keys and not all(key in deleted_keys for key in duplicate_keys):
            yield (fixture_name, updates, final_mapping, deleted_keys, final_root)
        else:
            for update_series in itertools.islice(
                itertools.permutations(fixture["in"]), 100
            ):
                yield (
                    fixture_name,
                    update_series,
                    final_mapping,
                    deleted_keys,
                    final_root,
                )


FIXTURES_PERMUTED = tuple(permute_fixtures(FIXTURES_NORMALIZED))


def trim_long_bytes(param):
    if isinstance(param, bytes) and len(param) > 3:
        return repr("0x" + param[:3].hex() + "...")


def assert_proof(trie, key):
    proof = trie.get_proof(key)

    proof_value = HexaryTrie.get_from_proof(trie.root_hash, key, proof)
    assert proof_value == trie.get(key)


@pytest.mark.parametrize(
    "name, updates, expected, deleted, final_root",
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
    changes = (
        (b"ab", b"b" * 32),
        (b"ac", b"c" * 32),
        (b"ac", None),
        (b"ad", b"d" * 32),
    )
    expected = ((b"ab", b"b" * 32), (b"ad", b"d" * 32))

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
    changes = (
        (b"ab", b"b" * 32),
        (b"ac", b"c" * 32),
        (b"ac", None),
        (b"ad", b"d" * 32),
    )

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


def test_hexary_trie_root_node_annotation():
    trie = HexaryTrie({})
    trie[b"\x41A"] = b"LONG" * 32
    trie[b"\xffE"] = b"LONG" * 32
    root = trie.root_node

    assert root == trie.traverse(())


def test_hexary_trie_empty_squash_does_not_read_root():
    db = {}
    trie = HexaryTrie(db=db)
    trie[b"AAA"] = b"LONG" * 32
    trie[b"BBB"] = b"LONG" * 32
    trie[b"\xffEE"] = b"LONG" * 32

    flagged_usage_db = KeyAccessLogger(db)
    flag_trie = HexaryTrie(flagged_usage_db, root_hash=trie.root_hash)
    with flag_trie.squash_changes():
        # root node should not be read if no changes are made during squash
        pass

    assert len(flagged_usage_db.read_keys) == 0


@st.composite
def trie_updates_strategy(draw, max_size=256):
    """
    Generate a series of key/value inserts, then create a series of
    (inserts, updates & deletes)

    The idea of this strategy is to make sure that we get updates and deletes by
    reusing keys that have already been created. This is necessary to create
    "interesting" use cases for a trie. Additionally, the length of the value
    changes the shape of the trie, due to node size, so try to vary that length as well.

    :returns: inserts, updates

    Inserts are (key, value) pairs. Updates are one of:
        - single-value tuple: (key,) -- insert key with value of test's choosing
        - double-value tuple: (key, None) -- delete key with given value
        - double-value tuple: (key, value) -- update key with given value

    Note that "update" may be b'', so would be effectively a delete. But tests ought to
    leave this as a trie "set" call, to make sure that code path is tested.
    """
    # starting trie keys
    start_keys = draw(
        st.lists(
            st.binary(min_size=3, max_size=3),
            unique=True,
            min_size=1,
            max_size=1024,
        )
    )

    minimum_insert_value_length = draw(st.integers(min_value=3, max_value=32))

    latest_keys = list(start_keys)
    inserts = [
        (key, key.ljust(minimum_insert_value_length, b"3")) for key in start_keys
    ]
    updates = []

    for _ in range(max_size):
        # Select the next change
        if len(latest_keys):
            next_change = draw(
                st.one_of(
                    # insert
                    st.tuples(
                        st.binary(min_size=3, max_size=3),
                    ),
                    # update
                    st.tuples(
                        st.sampled_from(latest_keys),
                        st.binary(min_size=1, max_size=128),
                    ),
                    # delete
                    st.tuples(
                        st.sampled_from(latest_keys),
                        # Sometimes run deletes as sets, sometimes as deletes.
                        # Test code should call `del trie[key]` if value is None
                        st.one_of(st.none(), st.just(b"")),
                    ),
                )
            )
        else:
            # If there are no current keys, then updating/deleting is not possible,
            #   so only insert in this case.
            next_change = draw(
                # insert
                st.tuples(
                    st.binary(min_size=3, max_size=3),
                ),
            )

        if len(next_change) == 1:
            key = next_change[0]
            if key in latest_keys:
                # Inserting an existing key is not allowed (it would actually be an
                # update), so treat it as a no-op.
                continue
            else:
                latest_keys.append(key)
                updates.append((key, key.ljust(minimum_insert_value_length, b"3")))
        elif len(next_change) == 2:
            updates.append(next_change)
            key, next_val = next_change
            if next_val in (None, b""):
                latest_keys.remove(key)
        else:
            raise Exception(f"Invalid code path: next_change = {next_change}")

        # on average, build an update list of length ~100,
        # but "shrinks" down to short lists
        should_continue = draw(st.integers(min_value=0, max_value=99))
        if should_continue == 0:
            break

    return inserts, updates


@given(trie_updates_strategy())
@example(
    # Triggers a case where the delete of a leaf succeeds, but the normalization fails
    # because of a missing trie node. The exception was *not* preventing the pruning
    # from happening.
    inserts_and_updates=(
        [
            (b"\x00\x00\x00", b"\x00\x00\x0033333333333333333333333"),
            (b"\x01\x00\x00", b"\x01\x00\x0033333333333333333333333"),
        ],
        [
            (b"\x00\x00\x00", None),
        ],
    )
)
@example(
    # An old implementation treated trie.set(key, b'') and trie.delete(key) differently,
    # and this test case exposed the issue.
    inserts_and_updates=(
        [],
        [
            (b"", b""),
            (b"", None),
            (b"\x00", b""),
            (b"", b""),
            (b"\x00", None),
        ],
    ),
)
@settings(max_examples=100)
def test_squash_changes_does_not_prune_on_missing_trie_node(inserts_and_updates):
    inserts, updates = inserts_and_updates
    node_db = {}
    trie = HexaryTrie(node_db)
    with trie.squash_changes() as trie_batch:
        for key, value in inserts:
            trie_batch[key] = value

    missing_nodes = dict(node_db)
    node_db.clear()

    with trie.squash_changes() as trie_batch:
        for key, value in updates:
            # repeat until change is complete
            change_complete = False
            while not change_complete:
                # Catch any missing nodes during trie change, and fix them up.
                # This is equivalent to Trinity's "Beam Sync".

                previous_db = trie_batch.db.copy()
                try:
                    if value is None:
                        del trie_batch[key]
                    else:
                        trie_batch[key] = value
                except MissingTrieNode as exc:
                    # When an exception is raised, we must never change the database
                    current_db = trie_batch.db.copy()
                    assert current_db == previous_db

                    node_db[exc.missing_node_hash] = missing_nodes.pop(
                        exc.missing_node_hash
                    )
                else:
                    change_complete = True


@given(
    st.lists(st.tuples(st.binary(), st.binary())),
    st.lists(st.binary()),
)
@example(
    # The root node is special: it always gets turned into a node, even if it's short.
    # The rest of the pruning machinery expects to only prune long nodes.
    # If you *never* try to prune the root node, then it will leave straggler nodes in
    # the database. This is because the "normal" pruning machinery will not mark a
    # short root node for pruning. The test will fail in the flagged_usage_db test
    # below, which makes sure that all present database keys are used when walking
    # through the trie.
    updates=[(b"", b"\x00"), (b"", b"\x00"), (b"", b"")],
    deleted=[],
)
@example(
    # Continuation of special root node handling from above...
    # If you *always* try to prune the root node in _set_root_node,
    # then you will *double* mark it (because if the root node is big enough, it will
    # already be handled by the "normal" pruning machinery). So this test just makes
    # sure you don't accidentally over-prune the root node. If you do, then the test
    # will raise a MissingTrieNode
    updates=[(b"\xa0", b"\x00\x00\x00\x00\x00\x00"), (b"\xa1", b"\x00\x00")],
    deleted=[b""],
)
@example(
    # Hm, the reason for this test case is lost to the sands of time.
    # It had to do with some intermediate pruning implementation that didn't
    # survive a squash.
    updates=[(b"", b""), (b"", b"")],
    deleted=[b""],
)
@example(
    # Wow, found a bug where a deleting a missing key could delete a *different, longer*
    # key. Deleting the b'' key here will cause the b'\x01' key to get deleted!
    updates=[(b"\x01", b"\x00"), (b"\x01\x00", b"\x00")],
    deleted=[b""],
)
@settings(max_examples=500)
def test_hexary_trie_squash_all_changes(updates, deleted):
    db = {}
    trie = HexaryTrie(db=db)
    expected = {}
    root_hashes = set()
    with trie.squash_changes() as memory_trie:
        for _index, (key, value) in enumerate(updates):
            if value is None:
                del memory_trie[key]
                expected.pop(key, None)
            else:
                memory_trie[key] = value
                expected[key] = value
            root_hashes.add(memory_trie.root_hash)

        for _index, key in enumerate(deleted):
            del memory_trie[key]
            expected.pop(key, None)
            root_hashes.add(memory_trie.root_hash)

    final_root_hash = trie.root_hash

    # access all of the values in the trie, triggering reads for all the database keys
    # that support the final state
    flagged_usage_db = KeyAccessLogger(db)
    flag_trie = HexaryTrie(flagged_usage_db, root_hash=final_root_hash)
    for key, val in expected.items():
        assert flag_trie[key] == val

    # assert that no unnecessary database values were created
    unread = flagged_usage_db.unread_keys()
    straggler_data = {k: (db[k], decode_node(db[k])) for k in unread}
    assert len(unread) == 0, straggler_data

    # rebuild without squashing, to compare root hash
    verbose_trie = HexaryTrie({})
    for key, value in updates:
        if value is None:
            del verbose_trie[key]
        else:
            verbose_trie[key] = value

    for _index, key in enumerate(deleted):
        del verbose_trie[key]

    assert final_root_hash == verbose_trie.root_hash


@pytest.mark.parametrize(
    "name, updates, expected, deleted, final_root",
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
    trie.set(b"what floats on water?", b"very small rocks")
    old_root_hash = trie.root_hash

    with trie.squash_changes() as memory_trie:
        memory_trie.set(b"what floats on water?", b"a duck")
        verify_ref_count(memory_trie)

    assert trie[b"what floats on water?"] == b"a duck"

    old_trie = HexaryTrie(db, root_hash=old_root_hash)
    assert old_trie[b"what floats on water?"] == b"very small rocks"


def test_hexary_trie_batch_save_drops_last_root_data_when_pruning():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b"what floats on water?", b"very small rocks")
    old_root_hash = trie.root_hash

    with trie.squash_changes() as memory_trie:
        memory_trie.set(b"what floats on water?", b"a duck")
        verify_ref_count(memory_trie)

    assert trie[b"what floats on water?"] == b"a duck"

    old_trie = HexaryTrie(db, root_hash=old_root_hash)
    with pytest.raises(MissingTraversalNode) as excinfo:
        old_trie.root_node

    assert encode_hex(old_root_hash) in str(excinfo.value)


def test_squash_changes_can_still_access_underlying_deleted_data():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b"what floats on water?", b"very small rocks")
    old_root_hash = trie.root_hash

    with trie.squash_changes() as memory_trie:
        memory_trie.set(b"what floats on water?", b"a duck")
        verify_ref_count(memory_trie)

        # change to a root hash that the memory trie doesn't have anymore
        memory_trie.root_hash
        memory_trie.root_hash = old_root_hash

        assert memory_trie[b"what floats on water?"] == b"very small rocks"


def test_squash_changes_raises_correct_error_on_new_deleted_data():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b"what floats on water?", b"very small rocks")

    with trie.squash_changes() as memory_trie:
        memory_trie.set(b"what floats on water?", b"a duck")
        verify_ref_count(memory_trie)
        middle_root_hash = memory_trie.root_hash

        memory_trie.set(b"what floats on water?", b"ooooohh")
        memory_trie.root_hash
        verify_ref_count(memory_trie)

        # change to a root hash that the memory trie doesn't have anymore
        memory_trie.root_hash = middle_root_hash

        with pytest.raises(MissingTrieNode):
            memory_trie[b"what floats on water?"]


def test_squash_changes_raises_correct_error_on_underlying_missing_data():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b"what floats on water?", b"very small rocks")
    old_root_hash = trie.root_hash

    # what if the root node hash is missing from the beginning?
    del db[old_root_hash]

    # the appropriate exception should be raised, when squashing changes
    with trie.squash_changes() as memory_trie:
        with pytest.raises(MissingTrieNode):
            memory_trie[b"what floats on water?"]


def test_squash_changes_reverts_trie_root_on_exception():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie.set(b"\x00", b"B" * 32)
    trie.set(b"\xff", b"C" * 32)
    old_root_hash = trie.root_hash

    # delete the node that will be used during trie fixup
    del db[trie.root_node.raw[0xF]]

    with pytest.raises(MissingTrieNode):
        with trie.squash_changes() as memory_trie:
            try:
                memory_trie[b"\x11"] = b"new val"
            except MissingTrieNode:
                raise AssertionError(
                    "Only the squash_changes context exit should raise this exception"
                )

            del memory_trie[b"\xff"]

    assert trie.root_hash == old_root_hash


def test_hexary_trie_missing_node():
    db = {}
    trie = HexaryTrie(db, prune=True)

    key1 = to_bytes(0x0123)
    trie.set(
        key1, b"use a value long enough that it must be hashed according to trie spec"
    )

    key2 = to_bytes(0x1234)
    trie.set(key2, b"val2")

    trie_root_hash = trie.root_hash

    # delete first child of the root
    root_node = trie.root_node.raw

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
        trie.set(key1_shared_prefix, b"val2")

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
        assert key1_shared_prefix2 in trie

    existance_exc_message = str(existance_exc_info.value)

    assert encode_hex(key1_shared_prefix2) in existance_exc_message
    assert encode_hex(trie_root_hash) in existance_exc_message
    assert encode_hex(first_child_hash) in existance_exc_message

    # Other keys are still accessible
    assert trie.get(key2) == b"val2"


def test_hexary_trie_missing_traversal_node():
    db = {}
    trie = HexaryTrie(db, prune=True)

    key1 = to_bytes(0x0123)
    trie.set(
        key1, b"use a value long enough that it must be hashed according to trie spec"
    )

    key2 = to_bytes(0x1234)
    trie.set(key2, b"val2")

    # delete first child of the root
    root_node = trie.root_node.raw

    first_child_hash = root_node[0]

    del db[first_child_hash]

    # Get exception with relevant info about lookup nibbles
    with pytest.raises(MissingTraversalNode) as exc_info:
        trie.traverse((0, 1, 2, 3))

    exception = exc_info.value
    assert exception.nibbles_traversed == (0,)
    assert encode_hex(first_child_hash) in str(exception)

    # Other keys are still traversable
    node = trie.traverse((1,))
    assert node.value == b"val2"
    assert node.sub_segments == ()


def test_hexary_trie_missing_traversal_node_with_traverse_from():
    db = {}
    trie = HexaryTrie(db, prune=True)

    key1 = to_bytes(0x0123)
    trie.set(
        key1, b"use a value long enough that it must be hashed according to trie spec"
    )

    key2 = to_bytes(0x1234)
    trie.set(key2, b"val2")

    # delete first child of the root
    root_node = trie.root_node

    first_child_hash = root_node.raw[0]

    del db[first_child_hash]

    # Get exception with relevant info about lookup nibbles
    with pytest.raises(MissingTraversalNode) as exc_info:
        trie.traverse_from(root_node, (0, 1, 2, 3))

    exception = exc_info.value
    assert exception.nibbles_traversed == (0,)
    assert encode_hex(first_child_hash) in str(exception)

    # Other keys are still traversable
    node = trie.traverse((1,))
    assert node.value == b"val2"
    assert node.sub_segments == ()


def test_hexary_trie_raises_on_pruning_snapshot():
    trie = HexaryTrie({}, prune=True)

    with pytest.raises(ValidationError):
        with trie.at_root(BLANK_NODE_HASH):
            pass


def verify_ref_count(trie):
    enumerated_ref_count = trie.regenerate_ref_count()

    tracked_keys = set(trie.ref_count.keys())
    enumerated_keys = set(enumerated_ref_count.keys())

    # we shouldn't be able to find any keys via enumeration that are untracked
    untracked_keys = enumerated_keys - tracked_keys
    assert len(untracked_keys) == 0

    # any tracked keys that aren't enumerated should have 0 references
    # (maybe they were added and subsequently removed)
    for unenumerated_key in tracked_keys - enumerated_keys:
        assert trie.ref_count[unenumerated_key] == 0

    # all keys that were found in enumeration and tracking should have the
    # same reference count
    for matching_key in tracked_keys & enumerated_keys:
        actual_num = trie.ref_count[matching_key]
        expected_num = enumerated_ref_count[matching_key]
        assert actual_num == expected_num


@pytest.mark.parametrize(
    "name, updates, expected, deleted, final_root",
    FIXTURES_PERMUTED,
    ids=trim_long_bytes,
)
def test_hexary_trie_ref_count(name, updates, expected, deleted, final_root):
    db = {}
    trie = HexaryTrie(db=db)
    with trie.squash_changes() as memory_trie:
        for key, value in updates:
            if value is None:
                del memory_trie[key]
            else:
                memory_trie[key] = value

            verify_ref_count(memory_trie)

        for key in deleted:
            del memory_trie[key]
            verify_ref_count(memory_trie)


def test_hexary_trie_avoid_over_pruning():
    db = {}
    trie = HexaryTrie(db, prune=True)

    def _insert(trie, index, val):
        index_key = rlp.encode(index, sedes=rlp.sedes.big_endian_int)
        trie[index_key] = val
        return index_key

    inserted_keys = []
    for index, val in enumerate([b"\0" * 32] * 129):
        new_key = _insert(trie, index, val)
        inserted_keys.append(new_key)

        # poke the trie to make sure all nodes are still present
        for key in inserted_keys:
            # If there's a problem, this will raise a MissingTrieNode
            trie.get(key)

        verify_ref_count(trie)


@pytest.mark.parametrize(
    "name, updates, expected, deleted, final_root",
    FIXTURES_PERMUTED,
    ids=trim_long_bytes,
)
def test_hexary_trie_traverse(name, updates, expected, deleted, final_root):
    # Create trie with fixture data
    db = {}
    traversal_trie = HexaryTrie(db=db)
    with traversal_trie.squash_changes() as trie:
        for key, value in updates:
            if value is None:
                del trie[key]
            else:
                trie[key] = value

        for key in deleted:
            del trie[key]

    # Traverse full trie, starting with the root. Compares traverse() and
    # traverse_from() result values found while traversing
    found_values = set()

    def traverse_via_cache(parent_prefix, parent_node, child_extension):
        if parent_node is None:
            # Can't traverse_from to the root node
            node = traversal_trie.traverse(())
        elif not len(child_extension):
            raise AssertionError(
                "For all but the root node, the child extension must not be empty"
            )
        else:
            logging_db = KeyAccessLogger(db)
            single_access_trie = HexaryTrie(logging_db)
            node = single_access_trie.traverse_from(parent_node, child_extension)
            # Traversing from parent to child should touch at most one node (the child)
            # It might touch 0 nodes, if the child was embedded inside the parent
            assert len(logging_db.read_keys) in {0, 1}

            # Validate that traversal from the root gives you the same result:
            slow_node = traversal_trie.traverse(parent_prefix + child_extension)
            assert node == slow_node

        if node.value:
            found_values.add(node.value)

        for new_child in node.sub_segments:
            # traverse into children
            traverse_via_cache(parent_prefix + child_extension, node, new_child)

    # start traversal at root
    traverse_via_cache((), None, ())

    # gut check that we have traversed the whole trie by checking all expected
    # values are visited
    for _, expected_value in expected.items():
        assert expected_value in found_values


@pytest.mark.parametrize(
    "trie_items, traverse_key, path_to_node, sub_segments, node_val",
    (
        (
            ((b"1", b"leaf-at-root"),),
            (3,),  # first nibble in b'1'
            (),  # nibbles to leaf node
            (),  # no sub-segments
            b"leaf-at-root",
        ),
        (
            ((b"1", b"leaf-at-root"),),
            (3, 1),  # nibbles for b'1'
            (),  # nibbles to leaf node
            (),  # no sub-segments
            b"leaf-at-root",
        ),
        (
            ((b"AAB", b"long0" * 7), (b"AAC", b"long1" * 7), (b"ZED", b"long3" * 7)),
            (4, 1),  # nibbles for b'A'
            (
                4,
            ),  # nibble to extension node (because ZED key breaks the root into a branch)  # noqa: E501
            # nibbles down to branch separating AAB and AAC:
            (
                (
                    1,  # second half of A
                    4,
                    1,  # next A
                    4,  # first nibble of both B and C
                ),
            ),
            b"",
        ),
        # Same as ^ but with short values
        (
            ((b"AAB", b"short"), (b"AAC", b"short"), (b"ZED", b"short")),
            (4, 1),  # nibbles for b'A'
            (
                4,
            ),  # nibble to extension node (because ZED key breaks the root into a branch)  # noqa: E501
            # nibbles down to branch separating AAB and AAC:
            (
                (
                    1,  # second half of A
                    4,
                    1,  # next A
                    4,  # first nibble of both B and C
                ),
            ),
            b"",
        ),
    ),
)
def test_traverse_into_partial_path(
    trie_items, traverse_key, path_to_node, sub_segments, node_val
):
    """
    What happens when you try to traverse into an extension or leaf node
    """
    db = {}
    trie = HexaryTrie(db)
    for key, val in trie_items:
        trie[key] = val

    with pytest.raises(TraversedPartialPath) as excinfo:
        trie.traverse(traverse_key)

    exc = excinfo.value
    assert exc.nibbles_traversed == path_to_node
    assert exc.node.sub_segments == sub_segments
    assert exc.node.value == node_val


@pytest.mark.parametrize(
    "trie_items, traverse_key, path_to_node, sub_segments, node_val",
    (
        (
            ((b"AAB", b"long0" * 7), (b"AAC", b"long1" * 7), (b"ZED", b"long3" * 7)),
            (4, 1),  # nibbles for b'A'
            (
                4,
            ),  # nibble to extension node (because ZED key breaks the root into a branch)  # noqa: E501
            # nibbles down to branch separating AAB and AAC:
            (
                (
                    1,  # second half of A
                    4,
                    1,  # next A
                    4,  # first nibble of both B and C
                ),
            ),
            b"",
        ),
        # Same as ^ but with short values
        (
            ((b"AAB", b"short"), (b"AAC", b"short"), (b"ZED", b"short")),
            (4, 1),  # nibbles for b'A'
            (
                4,
            ),  # nibble to extension node (because ZED key breaks the root into a branch)  # noqa: E501
            # nibbles down to branch separating AAB and AAC:
            (
                (
                    1,  # second half of A
                    4,
                    1,  # next A
                    4,  # first nibble of both B and C
                ),
            ),
            b"",
        ),
    ),
)
def test_traverse_from_partial_path(
    trie_items, traverse_key, path_to_node, sub_segments, node_val
):
    """
    What happens when you try to traverse_from() into an extension or leaf node
    """
    db = {}
    trie = HexaryTrie(db)
    for key, val in trie_items:
        trie[key] = val

    root = trie.root_node
    with pytest.raises(TraversedPartialPath) as excinfo:
        trie.traverse_from(root, traverse_key)

    exc = excinfo.value
    assert exc.nibbles_traversed == path_to_node
    assert exc.node.sub_segments == sub_segments
    assert exc.node.value == node_val


def test_traverse_non_matching_leaf():
    trie = HexaryTrie({})
    EMPTY_NODE = trie.root_node

    trie[b"\xFFleaf-at-root"] = b"some-value"
    final_root = trie.root_node

    # Traversing partway into the leaf raises the TraversedPartialPath exception
    with pytest.raises(TraversedPartialPath):
        trie.traverse((0xF,))
    with pytest.raises(TraversedPartialPath):
        trie.traverse_from(final_root, (0xF,))

    # But traversing to any *non*-matching nibble should return a blank node, because no
    # children reside underneath that nibble. Returning the leaf with a mismatched
    # nibble would be a bug.
    for nibble in range(0xF):
        # Note that we do not want to look at the 0xf nibble, because that's the one
        # that should raise the exception above
        assert trie.traverse((nibble,)) == EMPTY_NODE
        assert trie.traverse_from(final_root, (nibble,)) == EMPTY_NODE


def test_squash_a_pruning_trie_keeps_unchanged_short_root_node():
    db = {}
    trie = HexaryTrie(db, prune=True)
    trie[b"any"] = b"short"
    root_hash = trie.root_hash
    with trie.squash_changes() as trie_batch:
        trie_batch[b"any"] = b"short"
        assert trie.root_hash == root_hash
        assert root_hash in trie_batch.db
        assert root_hash in db
    assert trie.root_hash == root_hash
    assert root_hash in trie.db
    assert root_hash in db


@pytest.mark.parametrize("prune", (True, False))
def test_squash_a_trie_handles_setting_new_root(prune):
    db = {}
    trie = HexaryTrie(db, prune=prune)
    with trie.squash_changes() as trie_batch:
        trie[b"\x00"] = b"33\x00"
        old_root_hash = trie.root_hash

    # The ref-count doesn't get reset at the end of the batch, but the pending prune
    # count does make sure the logic here can handle that

    with trie.squash_changes() as trie_batch:
        trie_batch[b"\x00\x00\x00"] = b"\x00\x00\x00"

        assert trie_batch.root_hash != old_root_hash
        assert trie_batch.root_hash != trie.root_hash

    assert trie.root_hash != old_root_hash
    assert trie[b"\x00\x00\x00"] == b"\x00\x00\x00"
