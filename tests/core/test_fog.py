import pytest

from eth_utils import (
    ValidationError,
)
from hypothesis import (
    given,
    strategies as st,
)

from trie.exceptions import (
    FullDirectionalVisibility,
    PerfectVisibility,
)
from trie.fog import (
    HexaryTrieFog,
)


def test_trie_fog_completion():
    fog = HexaryTrieFog()

    # fog should start with *nothing* verified
    assert not fog.is_complete

    # completing the empty prefix should immediately mark it as complete
    empty_prefix = ()
    completed_fog = fog.explore(empty_prefix, ())
    assert completed_fog.is_complete

    # original fog should be untouched
    assert not fog.is_complete


def test_trie_fog_expand_before_complete():
    fog = HexaryTrieFog()

    empty_prefix = ()
    branched = fog.explore(empty_prefix, ((1,), (5,)))
    assert not branched.is_complete

    # complete only one prefix
    single_prefix = branched.explore((1,), ())
    assert not single_prefix.is_complete

    completed = single_prefix.explore((5,), ())
    assert completed.is_complete


def test_trie_fog_expand_before_mark_all_complete():
    fog = HexaryTrieFog()

    empty_prefix = ()
    branched = fog.explore(empty_prefix, ((1,), (5,)))
    assert not branched.is_complete

    # complete all sub-segments at once
    completed = branched.mark_all_complete(((1,), (5,)))
    assert completed.is_complete


def test_trie_fog_composition_equality():
    fog = HexaryTrieFog()

    empty_prefix = ()
    single_exploration = fog.explore(empty_prefix, ((9, 9, 9),))

    half_explore = fog.explore(empty_prefix, ((9,),))
    full_explore = half_explore.explore((9,), ((9, 9),))

    assert single_exploration == full_explore


def test_trie_fog_immutability():
    fog = HexaryTrieFog()

    fog1 = fog.explore((), ((1,), (2,)))

    fog2 = fog1.explore((1,), ((3,),))

    assert fog.nearest_unknown(()) == ()
    assert fog1.nearest_unknown(()) == (1,)
    assert fog2.nearest_unknown(()) == (1, 3)

    assert fog != fog1
    assert fog1 != fog2
    assert fog != fog2


@pytest.mark.parametrize(
    "sub_segments",
    (
        [(1, 2), (1, 2, 3, 4)],
        [(1, 2), (1, 2)],
    ),
)
def test_trie_fog_explore_invalid(sub_segments):
    """
    Cannot explore with a sub_segment that is a child of another sub_segment,
    or a duplicate
    """
    fog = HexaryTrieFog()
    with pytest.raises(ValidationError):
        fog.explore((), sub_segments)


def test_trie_fog_nearest_unknown():
    fog = HexaryTrieFog()

    empty_prefix = ()
    assert fog.nearest_unknown((1, 2, 3)) == empty_prefix

    branched = fog.explore(empty_prefix, ((1, 1), (5, 5)))

    # Test shallower
    assert branched.nearest_unknown((0,)) == (1, 1)
    assert branched.nearest_unknown((1,)) == (1, 1)
    assert branched.nearest_unknown((2,)) == (1, 1)
    assert branched.nearest_unknown((4,)) == (5, 5)
    assert branched.nearest_unknown((5,)) == (5, 5)
    assert branched.nearest_unknown((6,)) == (5, 5)

    # Test same level
    assert branched.nearest_unknown((0, 9)) == (1, 1)
    assert branched.nearest_unknown((1, 1)) == (1, 1)
    assert branched.nearest_unknown((2, 1)) == (1, 1)
    assert branched.nearest_unknown((3, 2)) == (1, 1)
    assert branched.nearest_unknown((3, 3)) == (5, 5)
    assert branched.nearest_unknown((4, 9)) == (5, 5)
    assert branched.nearest_unknown((5, 5)) == (5, 5)
    assert branched.nearest_unknown((6, 1)) == (5, 5)

    # Test deeper
    assert branched.nearest_unknown((0, 9, 9)) == (1, 1)
    assert branched.nearest_unknown((1, 1, 0)) == (1, 1)
    assert branched.nearest_unknown((2, 1, 1)) == (1, 1)
    assert branched.nearest_unknown((4, 9, 9)) == (5, 5)
    assert branched.nearest_unknown((5, 5, 0)) == (5, 5)
    assert branched.nearest_unknown((6, 1, 1)) == (5, 5)


def test_trie_fog_nearest_unknown_fully_explored():
    fog = HexaryTrieFog()
    empty_prefix = ()
    fully_explored = fog.explore(empty_prefix, ())

    with pytest.raises(PerfectVisibility):
        fully_explored.nearest_unknown(())

    with pytest.raises(PerfectVisibility):
        fully_explored.nearest_unknown((0,))


def test_trie_fog_nearest_right():
    fog = HexaryTrieFog()

    empty_prefix = ()
    assert fog.nearest_right((1, 2, 3)) == empty_prefix

    branched = fog.explore(empty_prefix, ((1, 1), (5, 5)))

    # Test shallower
    assert branched.nearest_right((0,)) == (1, 1)
    assert branched.nearest_right((1,)) == (1, 1)
    assert branched.nearest_right((2,)) == (5, 5)
    assert branched.nearest_right((4,)) == (5, 5)
    assert branched.nearest_right((5,)) == (5, 5)
    with pytest.raises(FullDirectionalVisibility):
        assert branched.nearest_right((6,))

    # Test same level
    assert branched.nearest_right((0, 9)) == (1, 1)
    assert branched.nearest_right((1, 1)) == (1, 1)
    assert branched.nearest_right((2, 1)) == (5, 5)
    assert branched.nearest_right((3, 2)) == (5, 5)
    assert branched.nearest_right((3, 3)) == (5, 5)
    assert branched.nearest_right((4, 9)) == (5, 5)
    assert branched.nearest_right((5, 5)) == (5, 5)
    with pytest.raises(FullDirectionalVisibility):
        assert branched.nearest_right((5, 6))
    with pytest.raises(FullDirectionalVisibility):
        assert branched.nearest_right((6, 1))

    # Test deeper
    assert branched.nearest_right((0, 9, 9)) == (1, 1)
    assert branched.nearest_right((1, 1, 0)) == (1, 1)
    assert branched.nearest_right((2, 1, 1)) == (5, 5)
    assert branched.nearest_right((4, 9, 9)) == (5, 5)
    assert branched.nearest_right((5, 5, 0)) == (5, 5)
    assert branched.nearest_right((5, 5, 15)) == (5, 5)
    with pytest.raises(FullDirectionalVisibility):
        assert branched.nearest_right((6, 0, 0))


def test_trie_fog_nearest_right_empty():
    fog = HexaryTrieFog()
    empty_prefix = ()
    fully_explored = fog.explore(empty_prefix, ())

    with pytest.raises(PerfectVisibility):
        fully_explored.nearest_right(())

    with pytest.raises(PerfectVisibility):
        fully_explored.nearest_right((0,))


@given(
    st.lists(
        st.tuples(
            # next index to use to search for a prefix to expand
            st.lists(
                st.integers(min_value=0, max_value=0xF),
                max_size=4
                * 2,  # one byte (two nibbles) deeper than the longest key above
            ),
            # sub_segments to use to lift the fog
            st.one_of(
                # branch node (or leaf node if size == 0)
                st.lists(
                    st.tuples(
                        st.integers(min_value=0, max_value=0xF),
                    ),
                    max_size=16,
                    unique=True,
                ),
                # or extension node
                st.tuples(
                    st.lists(
                        st.integers(min_value=0, max_value=0xF),
                        min_size=2,
                    ),
                ),
            ),
        ),
    ),
)
def test_trie_fog_serialize(expand_points):
    """
    Build a bunch of random trie fogs, serialize them to a bytes representation,
    then deserialize them back.

    Validate that all deserialized tries are equal to their starting tries and
    respond to nearest_unknown the same as the original.
    """
    starting_fog = HexaryTrieFog()
    for next_index, children in expand_points:
        try:
            next_unknown = starting_fog.nearest_unknown(next_index)
        except PerfectVisibility:
            # Have already completely explored the trie
            break

        starting_fog = starting_fog.explore(next_unknown, children)

    if expand_points:
        assert starting_fog != HexaryTrieFog()
    else:
        assert starting_fog == HexaryTrieFog()

    resumed_fog = HexaryTrieFog.deserialize(starting_fog.serialize())
    assert resumed_fog == starting_fog

    if starting_fog.is_complete:
        assert resumed_fog.is_complete
    else:
        for search_index, _ in expand_points:
            nearest_unknown_original = starting_fog.nearest_unknown(search_index)
            nearest_unknown_deserialized = resumed_fog.nearest_unknown(search_index)
            assert nearest_unknown_deserialized == nearest_unknown_original
