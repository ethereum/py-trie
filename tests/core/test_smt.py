from hypothesis import (
    given,
    strategies as st,
)

from trie.smt import (
    BLANK_NODE,
    SparseMerkleProof,
    SparseMerkleTree,
    calc_root,
)


@given(
    k=st.binary(min_size=1, max_size=32),
    v=st.binary(min_size=1, max_size=32),
)
def test_simple_kv(k, v):
    smt = SparseMerkleTree(key_size=len(k))
    empty_root = smt.root_hash

    # Nothing has been added yet
    assert not smt.exists(k)

    # Now that something is added, it should be consistent
    smt.set(k, v)
    assert smt.get(k) == v
    assert smt.root_hash != empty_root
    assert smt.root_hash == calc_root(k, v, smt.branch(k))

    # If you delete it, it goes away
    smt.delete(k)
    assert not smt.exists(k)
    assert smt.root_hash == empty_root


@given(
    key_size=st.shared(st.integers(min_value=1, max_value=32), key="key_size"),
    # Do this so that the size of the keys (in bytes) matches the key_size for the test
    keys=st.shared(st.integers(), key="key_size").flatmap(
        lambda key_size: st.lists(
            elements=st.binary(min_size=key_size, max_size=key_size),
            min_size=3,
            max_size=3,
            unique=True,
        )
    ),
    vals=st.lists(
        elements=st.binary(min_size=1, max_size=32),
        min_size=3,
        max_size=3,
    ),
)
def test_branch_updates(key_size, keys, vals):
    # Empty tree
    smt = SparseMerkleTree(key_size=key_size)

    # NOTE: smt._get internal method is used for testing only
    #       because it doesn't do null checks on the empty default
    EMPTY_NODE_HASHES = list(smt._get(keys[0])[1])

    # Objects to track proof data
    proofs = {k: SparseMerkleProof(k, BLANK_NODE, EMPTY_NODE_HASHES) for k in keys}

    # Track the big list of all updates
    proof_updates = []
    for k, p in proofs.items():
        # Update the key in the smt a bunch of times
        for v in vals:
            proof_updates.append((k, v, smt.set(k, v)))

        # Merge all of the updates into the tracked proof entries
        for u in proof_updates:
            p.update(*u)

        # All updates should be consistent with the latest smt root
        assert p.root_hash == smt.root_hash
