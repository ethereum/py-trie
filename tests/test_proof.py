import pytest

from eth_hash.auto import (
    keccak,
)

from trie.hexary import HexaryTrie
from trie.exceptions import BadTrieProof


def test_get_from_proof_key_exists():
    from .sample_proof_key_exists import key, state_root, proof
    assert HexaryTrie.get_from_proof(state_root, key, proof) != b''


def test_get_from_proof_key_does_not_exist():
    from .sample_proof_key_does_not_exist import key, state_root, proof
    assert HexaryTrie.get_from_proof(state_root, key, proof) == b''


def test_get_from_proof_invalid():
    from .sample_proof_key_exists import key, state_root, proof
    proof[5][3] = b''
    with pytest.raises(BadTrieProof):
        HexaryTrie.get_from_proof(state_root, key, proof)


def test_get_from_proof_empty():
    state_root = keccak(b'state root')
    key = keccak(b'some key')
    proof = []
    with pytest.raises(BadTrieProof):
        HexaryTrie.get_from_proof(state_root, key, proof)


def test_get_from_proof_node_less_than_32bytes():
    t = HexaryTrie(db={})
    t[b'some key'] = b'some value'
    assert HexaryTrie.get_from_proof(t.root_hash, b'some key', [t.root_node]) == b'some value'

    t[b'some key2'] = b'some value2'

    proof = [
        t.root_node,
        [b'', b'', b'', [b'2', b'some value2'], b'', b'', b'',
         b'', b'', b'', b'', b'', b'', b'', b'', b'', b'some value']
    ]
    assert HexaryTrie.get_from_proof(t.root_hash, b'some key2', proof) == b'some value2'
