import pytest

from eth_utils import (
        keccak,
        to_int,
    )

from trie.smt import (
    SparseMerkleTree,
    calc_root,
)


@pytest.mark.parametrize(
        "k,v",
        (
            (b'\x01', b'\x01'),
            (b'\xff', b'\xff'),
        )
    )
def test_simple_kv(k, v):
    smt = SparseMerkleTree(keysize=1)
    
    # Nothing has been added yet
    assert not smt.exists(k)
    
    # Now that something is added, it should be consistent
    smt.set(k, v)
    assert smt.get(k) == v
    assert smt.root_hash == calc_root(k, v, smt.branch(k))
    
    # If you delete it, it goes away
    smt.delete(k)
    assert not smt.exists(k)
