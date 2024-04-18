import pytest

from hypothesis import (
    example,
    given,
    settings,
    strategies as st,
)

from trie.exceptions import (
    MissingTraversalNode,
    MissingTrieNode,
    PerfectVisibility,
    TraversedPartialPath,
)
from trie.fog import (
    HexaryTrieFog,
    TrieFrontierCache,
)
from trie.iter import (
    NodeIterator,
)
from trie.tools.builder import (
    trie_from_keys,
)
from trie.tools.strategies import (
    trie_keys_with_extensions,
)
from trie.typing import (
    Nibbles,
)


@given(
    # starting trie keys
    trie_keys_with_extensions(allow_empty_trie=False),
    # minimum value length (to help force trie nodes to stop embedding)
    st.integers(min_value=1, max_value=32),
    st.lists(
        st.integers(min_value=0, max_value=0xF),
        max_size=4 * 2,  # one byte (two nibbles) deeper than the longest key above
    ),
)
@settings(max_examples=300)
def test_trie_walk_backfilling(trie_keys, minimum_value_length, index_nibbles):
    """
    - Create a random trie of 3-byte keys
    - Drop all node bodies from the trie
    - Use fog to index into random parts of the trie
    - Every time a node is missing from the DB, replace it and retry
    - Repeat until full trie has been explored with the HexaryTrieFog
    """
    node_db, trie = trie_from_keys(trie_keys, minimum_value_length, prune=True)
    index_key = Nibbles(index_nibbles)

    # delete all nodes
    dropped_nodes = dict(node_db)
    node_db.clear()

    # Core of the test: use the fog to convince yourself that you've
    # traversed the entire trie
    fog = HexaryTrieFog()
    for _ in range(100000):
        # Look up the next prefix to explore
        try:
            nearest_key = fog.nearest_unknown(index_key)
        except PerfectVisibility:
            # Test Complete!
            break

        # Try to navigate to the prefix, catching any errors about
        # nodes missing from the DB
        try:
            node = trie.traverse(nearest_key)
        except MissingTraversalNode as exc:
            # Node was missing, so fill in the node and try again
            node_db[exc.missing_node_hash] = dropped_nodes.pop(exc.missing_node_hash)
            continue
        else:
            # Node was found, use the found node to "lift the fog" down
            # to its longer prefixes
            fog = fog.explore(nearest_key, node.sub_segments)
    else:
        raise AssertionError("Must finish iterating the trie within ~100k runs")

    # Make sure we removed all the dropped nodes to push them back to the trie db
    assert len(dropped_nodes) == 0
    # Make sure the fog agrees that it's completed
    assert fog.is_complete
    # Make sure we can walk the whole trie without any missing nodes
    iterator = NodeIterator(trie)
    found_keys = set(iterator.keys())
    # Make sure we found all the keys
    assert found_keys == set(trie_keys)


@given(
    # starting trie keys
    trie_keys_with_extensions(allow_empty_trie=False),
    # minimum value length (to help force trie nodes to stop embedding)
    st.integers(min_value=1, max_value=32),
    st.lists(
        st.integers(min_value=0, max_value=0xF),
        max_size=4 * 2,  # one byte (two nibbles) deeper than the longest key above
    ),
)
@settings(max_examples=200)
def test_trie_walk_backfilling_with_traverse_from(
    trie_keys, minimum_value_length, index_nibbles
):
    """
    Like test_trie_walk_backfilling but using the HexaryTrie.traverse_from API
    """
    node_db, trie = trie_from_keys(trie_keys, minimum_value_length, prune=True)
    index_key = Nibbles(index_nibbles)

    # delete all nodes
    dropped_nodes = dict(node_db)
    node_db.clear()

    # traverse_from() cannot traverse to the root node, so resolve that manually
    try:
        root = trie.root_node
    except MissingTraversalNode as exc:
        node_db[exc.missing_node_hash] = dropped_nodes.pop(exc.missing_node_hash)
        root = trie.root_node

    # Core of the test: use the fog to convince yourself that you've
    # traversed the entire trie
    fog = HexaryTrieFog()
    for _ in range(100000):
        # Look up the next prefix to explore
        try:
            nearest_key = fog.nearest_unknown(index_key)
        except PerfectVisibility:
            # Test Complete!
            break

        # Try to navigate to the prefix, catching any errors about nodes
        # missing from the DB
        try:
            node = trie.traverse_from(root, nearest_key)
        except MissingTraversalNode as exc:
            # Node was missing, so fill in the node and try again
            node_db[exc.missing_node_hash] = dropped_nodes.pop(exc.missing_node_hash)
            continue
        else:
            # Node was found, use the found node to "lift the fog" down
            # to its longer prefixes
            fog = fog.explore(nearest_key, node.sub_segments)
    else:
        raise AssertionError("Must finish iterating the trie within ~100k runs")

    # Make sure we removed all the dropped nodes to push them back to the trie db
    assert len(dropped_nodes) == 0
    # Make sure the fog agrees that it's completed
    assert fog.is_complete
    # Make sure we can walk the whole trie without any missing nodes
    iterator = NodeIterator(trie)
    found_keys = set(iterator.keys())
    # Make sure we found all the keys
    assert found_keys == set(trie_keys)


@given(
    # starting trie keys
    trie_keys_with_extensions(allow_empty_trie=False),
    # minimum value length (to help force trie nodes to stop embedding)
    st.integers(min_value=1, max_value=32),
    # how many fog expansions to try before modifying the trie
    st.integers(min_value=0, max_value=10000),
    # all trie changes to make before the second trie walk
    st.lists(
        # one change, might be a...
        st.one_of(
            # insert
            st.binary(min_size=3, max_size=3),
            # update
            st.tuples(
                # index into existing key
                st.integers(min_value=1, max_value=1024),
                st.binary(min_size=1, max_size=128),
            ),
            # delete
            st.tuples(
                # index into existing key
                st.integers(min_value=1, max_value=1024),
                st.none(),
            ),
        ),
    ),
    # where to look for missing nodes in the first trie walk
    st.lists(
        st.integers(min_value=0, max_value=0xF),
        max_size=4 * 2,  # one byte (two nibbles) deeper than the longest key above
    ),
    # where to look for missing nodes in the second trie walk
    st.lists(
        st.integers(min_value=0, max_value=0xF),
        max_size=4 * 2,  # one byte (two nibbles) deeper than the longest key above
    ),
)
@example(
    # Catch bug where TraversedPartialPath is raised when traversing into a leaf,
    # even though the leaf suffix doesn't match the prefix that was being traversed to.
    trie_keys=[b"\x00\x00\x00", b"\x10\x00\x00"],
    minimum_value_length=26,
    number_explorations=86,
    trie_changes=[(1, None)],
    index_nibbles=[],
    index_nibbles2=[],
)
@example(
    # This is the example that inspired
    # test_squash_a_pruning_trie_keeps_unchanged_short_root_node
    # Leave it in as a backup regression test, and to test in a broader context.
    trie_keys=[b"\x00\x00\x01"],
    minimum_value_length=0,
    number_explorations=0,
    trie_changes=[b"\x00\x00\x01"],
    index_nibbles=[],
    index_nibbles2=[],
)
@example(
    # Interesting scenario:
    #   - during trie change, delete prunes leaf node for key b'\x00\x01\x00'
    #   - *after* pruning, a MissingTrieNode is raised during a normalize step
    #   - this exception ought to revert the delete, but it's too late
    #   - a subsequent attempt to delete the key fails because the leaf node is missing
    trie_keys=[b"\x00\x01\x00", b"\x00\x01\x01", b"\x00\x00\x00"],
    minimum_value_length=27,
    number_explorations=0,
    trie_changes=[(1, None), (3, None)],
    index_nibbles=[],
    index_nibbles2=[],
)
@example(
    # Catch bug where TraversedPartialPath is raised when traversing into a leaf,
    # even though the leaf suffix doesn't match the prefix that was being traversed to.
    trie_keys=[b"\x00\x00\x00", b"\x10\x00\x00"],
    minimum_value_length=26,
    number_explorations=86,
    trie_changes=[(1, None)],
    index_nibbles=[],
    index_nibbles2=[],
)
@example(
    # Test that covers a TraversedPartialPath exception, to make sure the sub_segments
    #   are correctly generated on the simulated node of the exception
    trie_keys=[b"\x01\x00\x00", b"\x01\x01\x00", b"\x00\x00"],
    minimum_value_length=3,
    number_explorations=2,
    trie_changes=[(2, None)],
    index_nibbles=[],
    index_nibbles2=[],
)
@settings(max_examples=500)
def test_trie_walk_root_change_with_traverse(
    trie_keys,
    minimum_value_length,
    number_explorations,
    trie_changes,
    index_nibbles,
    index_nibbles2,
):
    """
    Like test_trie_walk_backfilling, but:
    - Halt the trie walk early
    - Modify the trie according to parameter trie_changes
    - Continue walking the trie using the same HexaryTrieFog, until completion
    - Verify that all required database values were replaced (where only the nodes under
        the NEW trie root are required)
    """
    # Turn on pruning to simulate having peers lose access to old trie nodes over time
    node_db, trie = trie_from_keys(trie_keys, minimum_value_length, prune=True)

    number_explorations %= len(node_db)

    # delete all nodes
    missing_nodes = dict(node_db)
    node_db.clear()

    # First walk
    index_key = tuple(index_nibbles)
    fog = HexaryTrieFog()
    for _ in range(number_explorations):
        # Look up the next prefix to explore
        try:
            nearest_key = fog.nearest_unknown(index_key)
        except PerfectVisibility:
            raise AssertionError(
                "Number explorations should be lower than database size, shouldn't finish"  # noqa: E501
            )

        # Try to navigate to the prefix, catching any errors about
        # nodes missing from the DB
        try:
            node = trie.traverse(nearest_key)
            # Note that a TraversedPartialPath should not happen here, because no trie
            # changes have happened, so we should have a perfect picture of the trie
        except MissingTraversalNode as exc:
            # Node was missing, so fill in the node and try again
            node_db[exc.missing_node_hash] = missing_nodes.pop(exc.missing_node_hash)
            continue
        else:
            # Node was found, use the found node to "lift the fog"
            # down to its longer prefixes
            fog = fog.explore(nearest_key, node.sub_segments)

    # Modify Trie mid-walk, keeping track of the expected list of final keys
    expected_final_keys = set(trie_keys)
    with trie.squash_changes() as trie_batch:
        for change in trie_changes:
            # repeat until change is complete
            change_complete = False
            while not change_complete:
                # Catch any missing nodes during trie change, and fix them up.
                # This is equivalent to Trinity's "Beam Sync".
                try:
                    if isinstance(change, bytes):
                        # insert!
                        trie_batch[change] = change
                        expected_final_keys.add(change)
                    else:
                        key_index, new_value = change
                        key = trie_keys[key_index % len(trie_keys)]
                        if new_value is None:
                            del trie_batch[key]
                            expected_final_keys.discard(key)
                        else:
                            # update (though may be an insert,
                            # if there was a previous delete)
                            trie_batch[key] = new_value
                            expected_final_keys.add(key)
                except MissingTrieNode as exc:
                    node_db[exc.missing_node_hash] = missing_nodes.pop(
                        exc.missing_node_hash
                    )
                else:
                    change_complete = True

    # Second walk
    index_key2 = tuple(index_nibbles2)

    for _ in range(100000):
        try:
            nearest_key = fog.nearest_unknown(index_key2)
        except PerfectVisibility:
            # Complete!
            break

        try:
            node = trie.traverse(nearest_key)
            sub_segments = node.sub_segments
        except MissingTraversalNode as exc:
            node_db[exc.missing_node_hash] = missing_nodes.pop(exc.missing_node_hash)
            continue
        except TraversedPartialPath as exc:
            # You might only get part-way down a path of nibbles if your
            # fog is based on an old trie. Determine the new sub-segments
            # that are accessible from this partial traversal
            sub_segments = exc.simulated_node.sub_segments

        # explore the fog if there were no exceptions,
        # or if you traversed a partial path
        fog = fog.explore(nearest_key, sub_segments)
    else:
        raise AssertionError("Must finish iterating the trie within ~100k runs")

    # Final assertions
    assert fog.is_complete
    # We do *not* know that we have replaced all the missing_nodes,
    # because of the trie changes

    # Make sure we can walk the whole trie without any missing nodes
    iterator = NodeIterator(trie)
    found_keys = set(iterator.keys())
    assert found_keys == expected_final_keys


@given(
    # starting trie keys
    trie_keys_with_extensions(allow_empty_trie=False),
    # minimum value length (to help force trie nodes to stop embedding)
    st.integers(min_value=1, max_value=32),
    # how many fog expansions to try before modifying the trie
    st.integers(min_value=0, max_value=10000),
    # all trie changes to make before the second trie walk
    st.lists(
        # one change, might be a...
        st.one_of(
            # insert
            st.binary(min_size=3, max_size=3),
            # update
            st.tuples(
                # index into existing key
                st.integers(min_value=1, max_value=1024),
                st.binary(min_size=1, max_size=128),
            ),
            # delete
            st.tuples(
                # index into existing key
                st.integers(min_value=1, max_value=1024),
                st.none(),
            ),
        ),
    ),
    # where to look for missing nodes in the first trie walk
    st.lists(
        st.integers(min_value=0, max_value=0xF),
        max_size=4 * 2,  # one byte (two nibbles) deeper than the longest key above
    ),
    # where to look for missing nodes in the second trie walk
    st.lists(
        st.integers(min_value=0, max_value=0xF),
        max_size=4 * 2,  # one byte (two nibbles) deeper than the longest key above
    ),
)
@example(
    # Test that covers a TraversedPartialPath exception, and make sure that the
    # sub_segments and cached node are generated properly.
    trie_keys=[b"\x01\x00\x00", b"\x01\x01\x00", b"\x00\x00"],
    minimum_value_length=3,
    number_explorations=2,
    trie_changes=[(2, None)],
    index_nibbles=[],
    index_nibbles2=[],
)
@settings(max_examples=500)
@pytest.mark.parametrize("do_cache_reset", (True, False))
def test_trie_walk_root_change_with_cached_traverse_from(
    do_cache_reset,
    trie_keys,
    minimum_value_length,
    number_explorations,
    trie_changes,
    index_nibbles,
    index_nibbles2,
):
    """
    Like test_trie_walk_root_change_with_traverse but using HexaryTrie.traverse_from
    when possible.
    """
    # Turn on pruning to simulate having peers lose access to old trie nodes over time
    node_db, trie = trie_from_keys(trie_keys, minimum_value_length, prune=True)

    number_explorations %= len(node_db)
    cache = TrieFrontierCache()

    # delete all nodes
    missing_nodes = dict(node_db)
    node_db.clear()

    # First walk
    index_key = tuple(index_nibbles)
    fog = HexaryTrieFog()
    for _ in range(number_explorations):
        try:
            nearest_prefix = fog.nearest_unknown(index_key)
        except PerfectVisibility:
            raise AssertionError(
                "Number explorations should be lower than database size, shouldn't finish"  # noqa: E501
            )

        try:
            # Use the cache, if possible, to look up the parent node of nearest_prefix
            try:
                cached_node, uncached_key = cache.get(nearest_prefix)
            except KeyError:
                # Must navigate from the root. In this 1st walk,
                # only the root should not be cached
                assert nearest_prefix == ()
                node = trie.traverse(nearest_prefix)
            else:
                # Only one database lookup required
                node = trie.traverse_from(cached_node, uncached_key)

            # Note that a TraversedPartialPath should not happen here, because no trie
            # changes have happened, so we should have a perfect picture of the trie
        except MissingTraversalNode as exc:
            # Each missing node should only need to be retrieve (at most) once
            node_db[exc.missing_node_hash] = missing_nodes.pop(exc.missing_node_hash)
            continue
        else:
            fog = fog.explore(nearest_prefix, node.sub_segments)

            if node.sub_segments:
                cache.add(nearest_prefix, node, node.sub_segments)
            else:
                cache.delete(nearest_prefix)

    # Modify Trie mid-walk, keeping track of the expected list of final keys
    expected_final_keys = set(trie_keys)
    with trie.squash_changes() as trie_batch:
        for change in trie_changes:
            # repeat until change is complete
            change_complete = False
            while not change_complete:
                # Catch any missing nodes during trie change, and fix them up.
                # This is equivalent to Trinity's "Beam Sync".
                try:
                    if isinstance(change, bytes):
                        # insert!
                        trie_batch[change] = change.rjust(minimum_value_length, b"3")
                        expected_final_keys.add(change)
                    else:
                        key_index, new_value = change
                        key = trie_keys[key_index % len(trie_keys)]
                        if new_value is None:
                            del trie_batch[key]
                            expected_final_keys.discard(key)
                        else:
                            # update (though may be an insert,
                            # if there was a previous delete)
                            trie_batch[key] = new_value
                            expected_final_keys.add(key)
                except MissingTrieNode as exc:
                    node_db[exc.missing_node_hash] = missing_nodes.pop(
                        exc.missing_node_hash
                    )
                else:
                    change_complete = True

    # Second walk
    index_key2 = tuple(index_nibbles2)
    if do_cache_reset:
        cache = TrieFrontierCache()

    for _ in range(100000):
        try:
            nearest_prefix = fog.nearest_unknown(index_key2)
        except PerfectVisibility:
            # Complete!
            break

        try:
            try:
                cached_node, uncached_key = cache.get(nearest_prefix)
            except KeyError:
                node = trie.traverse(nearest_prefix)
                cached_node = None
            else:
                node = trie.traverse_from(cached_node, uncached_key)
        except MissingTraversalNode as exc:
            node_hash = exc.missing_node_hash
            if node_hash in missing_nodes:
                # Each missing node should only need to be retrieve (at most) once
                node_db[node_hash] = missing_nodes.pop(node_hash)
            elif cached_node is not None:
                # But, it could also be missing because of an old cached node
                # Delete the bad cache and try again
                cache.delete(nearest_prefix)
            else:
                raise AssertionError(f"Bad node hash request: {node_hash}")
            continue
        except TraversedPartialPath as exc:
            node = exc.simulated_node

        sub_segments = node.sub_segments
        fog = fog.explore(nearest_prefix, sub_segments)

        if sub_segments:
            cache.add(nearest_prefix, node, sub_segments)
        else:
            cache.delete(nearest_prefix)
    else:
        raise AssertionError("Must finish iterating the trie within ~100k runs")

    # Final assertions
    assert fog.is_complete
    # We do *not* know that we have replaced all the missing_nodes,
    # because of the trie changes

    # Make sure we can walk the whole trie without any missing nodes
    iterator = NodeIterator(trie)
    found_keys = set(iterator.keys())
    assert found_keys == expected_final_keys
