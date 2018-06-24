from eth_hash.auto import (
    keccak,
)

from trie.constants import (
    EMPTY_LEAF_NODE_HASH,
    EMPTY_NODE_HASHES,
)
from trie.validation import (
    validate_is_bytes,
    validate_length,
)


# sanity check
assert EMPTY_LEAF_NODE_HASH == keccak(b'')


class SparseMerkleTree:
    def __init__(self, db):
        self.db = db
        # Initialize an empty tree with one branch
        self.root_hash = keccak(EMPTY_NODE_HASHES[0] + EMPTY_NODE_HASHES[0])
        self.db[self.root_hash] = EMPTY_NODE_HASHES[0] + EMPTY_NODE_HASHES[0]
        for i in range(159):
            self.db[EMPTY_NODE_HASHES[i]] = EMPTY_NODE_HASHES[i+1] + EMPTY_NODE_HASHES[i+1]
        self.db[EMPTY_LEAF_NODE_HASH] = b''

    def get(self, key):
        validate_is_bytes(key)
        validate_length(key, 20)

        target_bit = 1 << 159
        path = int.from_bytes(key, byteorder='big')
        node_hash = self.root_hash
        for i in range(160):
            if path & target_bit:
                node_hash = self.db[node_hash][32:]
            else:
                node_hash = self.db[node_hash][:32]
            target_bit >>= 1

        if self.db[node_hash] is b'':
            return None
        else:
            return self.db[node_hash]

    def set(self, key, value):
        validate_is_bytes(key)
        validate_length(key, 20)
        validate_is_bytes(value)

        path = int.from_bytes(key, byteorder='big')
        self.root_hash = self._set(value, path, 0, self.root_hash)
        return

    def _set(self, value, path, depth, node_hash):
        if depth == 160:
            return self._hash_and_save(value)
        else:
            node = self.db[node_hash]
            target_bit = 1 << (159 - depth)
            if (path & target_bit):
                return self._hash_and_save(node[:32] + self._set(value, path, depth+1, node[32:]))
            else:
                return self._hash_and_save(self._set(value, path, depth+1, node[:32]) + node[32:])

    def exists(self, key):
        validate_is_bytes(key)
        validate_length(key, 20)

        return self.get(key) is not None

    def delete(self, key):
        """
        Equals to setting the value to None
        """
        validate_is_bytes(key)
        validate_length(key, 20)

        self.set(key, b'')

    #
    # Utils
    #
    def _hash_and_save(self, node):
        """
        Saves a node into the database and returns its hash
        """

        node_hash = keccak(node)
        self.db[node_hash] = node
        return node_hash

    #
    # Dictionary API
    #
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        return self.delete(key)

    def __contains__(self, key):
        return self.exists(key)
