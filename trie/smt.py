from eth_utils import (
        keccak,
        to_int,
    )

from trie.constants import (
    BLANK_NODE,
)

from trie.exceptions import (
        ValidationError,
    )

from trie.validation import (
    validate_is_bytes,
    validate_length,
)


def calc_root(key, value, branch):
    path = to_int(key)
    target_bit = 1
    # traverse the path in leaf->root order
    # branch is in root->leaf order (key is in MSB to LSB order)
    node_hash = keccak(value)
    for sibling in reversed(branch):
        if path & target_bit:
            node_hash = keccak(sibling + node_hash)
        else:
            node_hash = keccak(node_hash + sibling)
        target_bit <<= 1

    return node_hash


class SparseMerkleTree:

    def __init__(self, keysize=32):
        # Ensure we can support the given depth
        if not 1 <= keysize <= 32:
            raise ValidationError("Keysize must be number of bytes in range [0, 32]")

        self.keysize = keysize  # keysize in bytes
        self.depth = keysize * 8  # depth is number of bits in key
        
        # Initialize an empty tree with one branch
        self.db = {}
        node = BLANK_NODE  # Leaf node
        for i in range(self.depth):
            node_hash = keccak(node)
            self.db[node_hash] = node
            node = node_hash + node_hash

        # Finally, write the root hash
        self.root_hash = keccak(node)
        self.db[self.root_hash] = node
    
    @classmethod
    def from_db(cls, db, root_hash, keysize=32):
        smt = cls(keysize=keysize)

        # If db is provided, and is not consistent,
        # there may be a silent error. Can't solve that easily.
        for k, v in db.items():
            validate_is_bytes(k)
            validate_length(k, 32)  # Must be a bytes32 hash
            validate_is_bytes(v)
            smt.db[k] = v

        # Set root_hash, so we know where to start
        validate_is_bytes(root_hash)
        validate_length(root_hash, 32)  # Must be a bytes32 hash

        smt.root_hash = root_hash

        return smt
    
    def get(self, key):
        value, _ = self._get(key)

        # Ensure that it isn't blank!
        if value == BLANK_NODE:
            raise KeyError("Key does not exist")
        
        return value
    
    def branch(self, key):
        value, branch = self._get(key)

        # Ensure that it isn't blank!
        if value == BLANK_NODE:
            raise KeyError("Key does not exist")
        
        return branch

    def _get(self, key):
        """
        Returns db value and branch in root->leaf order
        """
        validate_is_bytes(key)
        validate_length(key, self.keysize)
        branch = []

        target_bit = 1 << (self.depth - 1)
        path = to_int(key)
        node_hash = self.root_hash
        # Append the sibling to the branch
        # Iterate on the parent
        for i in range(self.depth):
            if path & target_bit:
                branch.append(self.db[node_hash][:32])
                node_hash = self.db[node_hash][32:]
            else:
                branch.append(self.db[node_hash][32:])
                node_hash = self.db[node_hash][:32]
            target_bit >>= 1

        # Value is the last hash in the chain
        # NOTE: Didn't do exception here for testing purposes
        return self.db[node_hash], branch

    def set(self, key, value):
        """
        Returns all updated hashes in root->leaf order
        """
        validate_is_bytes(key)
        validate_length(key, self.keysize)
        validate_is_bytes(value)

        path = to_int(key)
        node = value
        _, branch = self._get(key)
        proof_update = []  # Keep track of proof updates

        target_bit = 1
        # branch is in root->leaf order, so flip
        for sibling in reversed(branch):
            # Set
            node_hash = keccak(node)
            proof_update.append(node_hash)
            self.db[node_hash] = node

            # Update
            if (path & target_bit):
                node = sibling + node_hash
            else:
                node = node_hash + sibling

            target_bit <<= 1

        # Finally, update root hash
        self.root_hash = keccak(node)
        self.db[self.root_hash] = node

        # updates need to be in root->leaf order, so flip back
        return list(reversed(proof_update))
    
    def exists(self, key):
        validate_is_bytes(key)
        validate_length(key, self.keysize)

        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def delete(self, key):
        """
        Equals to setting the value to None
        Returns all updated hashes in root->leaf order
        """
        validate_is_bytes(key)
        validate_length(key, self.keysize)

        return self.set(key, BLANK_NODE)
    
    #
    # Dictionary API
    #
    
    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        self.set(key, value)
    
    def __delitem__(self, key):
        self.delete(key)
    
    def __contains__(self, key):
        return self.exists(key)

