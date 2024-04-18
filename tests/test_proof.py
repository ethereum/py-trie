import pytest

from eth_hash.auto import (
    keccak,
)

from trie.exceptions import (
    BadTrieProof,
)
from trie.hexary import (
    HexaryTrie,
)


def test_get_from_proof_key_exists():
    from .sample_proof_key_exists import (
        key,
        proof,
        state_root,
    )

    assert HexaryTrie.get_from_proof(state_root, key, proof) != b""


def test_get_from_proof_key_does_not_exist():
    from .sample_proof_key_does_not_exist import (
        key,
        proof,
        state_root,
    )

    assert HexaryTrie.get_from_proof(state_root, key, proof) == b""


def test_get_proof_key_does_not_exist():
    trie = HexaryTrie({})
    trie[b"hello"] = b"world"
    trie[b"hi"] = b"there"
    proof = trie.get_proof(b"hey")

    assert len(proof) > 0
    assert HexaryTrie.get_from_proof(trie.root_hash, b"hey", proof) == b""


def test_get_from_proof_invalid():
    from .sample_proof_key_exists import (
        key,
        proof,
        state_root,
    )

    proof[5][3] = b""
    with pytest.raises(BadTrieProof):
        HexaryTrie.get_from_proof(state_root, key, proof)


def test_get_from_proof_empty():
    state_root = keccak(b"state root")
    key = keccak(b"some key")
    proof = []
    with pytest.raises(BadTrieProof):
        HexaryTrie.get_from_proof(state_root, key, proof)
