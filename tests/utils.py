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
