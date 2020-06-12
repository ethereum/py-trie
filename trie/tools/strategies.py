from hypothesis import (
    strategies as st,
)

from trie import HexaryTrie


@st.composite
def random_trie_strategy(draw):
    trie_items = draw(st.lists(
        st.tuples(
            # key
            st.binary(max_size=32),
            # value
            st.binary(min_size=1, max_size=64),
        ),
        unique=True,
        max_size=512,
    ))

    trie = HexaryTrie({})
    for key, value in trie_items:
        trie[key] = value
    return trie, dict(trie_items)


@st.composite
def trie_keys_with_extensions(draw):
    """
    Build trie keys that tend to have lots of extension/branch/leaf nodes.
    Anecdotally, this was more likely to produce examples like the one
    in test_trie_walk_root_change_with_traverse() about TraversedPartialPath.
    """
    # Simplest possible trie: an empty trie
    # Test it about once, on average, per run of 200 tests (the default example count)
    # Also, this will shrink down to the empty trie as you shrink these integers.
    if draw(st.integers(min_value=0, max_value=200)) == 0:
        return ()

    def build_up_from_children(children):
        # Branch out
        return st.tuples(
            st.binary(min_size=0, max_size=3),
            children,
            st.binary(min_size=0, max_size=3),
            children,
        )

    # build tree
    tree = draw(st.recursive(
        # key suffix
        st.tuples(
            st.binary(min_size=0, max_size=3),
        ),
        # branches/extensions
        build_up_from_children,
    ))

    def unroll_keys(node):
        if len(node) == 1:
            # leaf
            yield node[0]
        elif len(node) == 4:
            # branch
            for subkey in unroll_keys(node[1]):
                yield node[0] + subkey
            for subkey in unroll_keys(node[3]):
                yield node[2] + subkey

    # Use a hashable type here, to make uniqueness checks faster/possible
    return tuple(set(unroll_keys(tree)))


def trie_from_keys(keys, min_value_length=1):
    trie = HexaryTrie({})
    contents = {}
    with trie.squash_changes() as batch:
        for key in keys:
            # flood 3's at the end of the value to make it longer. b'3' is encoded to 0x33,
            #   so the bytes and HexBytes representation look the same. Just a convenience.
            value = (b'v' + key).ljust(min_value_length, b'3')
            batch[key] = value
            contents[key] = value

    return trie, contents
