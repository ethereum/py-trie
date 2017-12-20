from hypothesis import (
    given,
    strategies as st,
    settings,
)

from trie.trie import (
    BinaryTrie,
)
from trie.constants import (
    BLANK_HASH,
)


@given(k=st.lists(st.binary(min_size=32, max_size=32), min_size=100, max_size=100, unique=True),
    v=st.lists(st.binary(min_size=1), min_size=100, max_size=100),
    random=st.randoms())
@settings(max_examples=10)
def test_bin_trie_different_order_insert(k, v, random):
    kv_pairs = list(zip(k, v))
    result = BLANK_HASH
    # Repeat 3 times
    for _ in range(3):
        trie = BinaryTrie(db={})
        random.shuffle(kv_pairs)
        for i, (k, v) in enumerate(kv_pairs):
            trie.set(k, v)
            assert trie.get(k) == v
        assert result is BLANK_HASH or trie.root_hash == result
        result = trie.root_hash
        # insert already exist key/value
        trie.set(kv_pairs[0][0], kv_pairs[0][1])
        assert trie.root_hash == result
        # Delete all key/value
        random.shuffle(kv_pairs)
        for k, v in kv_pairs:
            trie.delete(k)
        assert trie.root_hash == BLANK_HASH
