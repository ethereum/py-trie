from hypothesis import (
        given,
        strategies as st,
    )

from trie.smt import (
    SparseMerkleTree,
    SparseMerkleProof,
    calc_root,
    BLANK_NODE,
)


@given(
    k=st.binary(min_size=1, max_size=32),
    v=st.binary(min_size=1, max_size=32),
)
def test_simple_kv(k, v):
    smt = SparseMerkleTree(key_size=len(k))

    # Nothing has been added yet
    assert not smt.exists(k)

    # Now that something is added, it should be consistent
    smt.set(k, v)
    assert smt.get(k) == v
    assert smt.root_hash == calc_root(k, v, smt.branch(k))

    # If you delete it, it goes away
    smt.delete(k)
    assert not smt.exists(k)


@given(
    data=st.data(),
    key_size=st.integers(min_value=1, max_value=32),
)
def test_branch_updates(data, key_size):
    num_elements = data.draw(st.integers(min_value=1, max_value=key_size*8//10+1))
    keys = data.draw(
        st.lists(
            elements=st.binary(min_size=key_size, max_size=key_size),
            min_size=1,
            max_size=num_elements,
            unique=True,
        )
    )
    vals = data.draw(
        st.lists(
            elements=st.binary(min_size=1, max_size=32),
            min_size=len(keys),
            max_size=len(keys),
        )
    )

    # Empty tree
    smt = SparseMerkleTree(key_size=key_size)

    # NOTE: smt._get internal method is used for testing only
    EMPTY_NODE_HASHES = list(smt._get(keys[0])[1])

    # Objects to track proof data
    proofs = dict([(k, SparseMerkleProof(k, BLANK_NODE, EMPTY_NODE_HASHES)) for k in keys])

    # Track the big list of all updates
    proof_updates = []
    for k, p in proofs.items():
        # Update the key in the smt a bunch of times
        for v in vals:
            proof_updates.append((k, v, smt.set(k, v)))

        # Merge all of the updates into the tracked proof entries
        for u in proof_updates:
            p.merge(*u)

        # All merges should be consistent with the latest smt root
        assert p.root_hash == smt.root_hash
