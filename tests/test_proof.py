import pytest

from trie.exceptions import BadTrieProof
from trie.proof import verify_proof
from trie.utils.sha3 import keccak


def test_verify_proof_key_exists():
    from .sample_proof_key_exists import key, state_root, proof
    assert verify_proof(state_root, key, proof) != b''


def test_verify_proof_key_does_not_exist():
    from .sample_proof_key_does_not_exist import key, state_root, proof
    assert verify_proof(state_root, key, proof) == b''


def test_verify_proof_invalid():
    from .sample_proof_key_exists import key, state_root, proof
    proof[5][3] = b''
    with pytest.raises(BadTrieProof):
        verify_proof(state_root, key, proof)


def test_verify_proof_empty():
    state_root = keccak(b'state root')
    key = keccak(b'some key')
    proof = []
    with pytest.raises(BadTrieProof):
        verify_proof(state_root, key, proof)


