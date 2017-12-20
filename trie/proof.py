from __future__ import absolute_import

from trie import Trie

from trie.exceptions import BadTrieProof


# TODO: This function needs to be audited to ensure the approach used here to verify a trie proof
# is correct.
def verify_proof(root_hash, key, proof):
    """Verify that the given proof contains a value for key on a trie with the given root hash.

    Returns the value for the key when it is present, an empty bytes when the key is not present,
    or raises BadTrieProof if the proof is not valid.
    """
    trie = Trie({})
    for node in proof:
        trie._persist_node(node)
    trie.root_hash = root_hash
    try:
        return trie.get(key)
    except KeyError as e:
        raise BadTrieProof("Missing proof node with hash {}".format(e.args))
