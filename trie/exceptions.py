from eth_utils import (
    encode_hex,
)


class InvalidNibbles(Exception):
    pass


class InvalidNode(Exception):
    pass


class ValidationError(Exception):
    pass


class BadTrieProof(Exception):
    pass


class NodeOverrideError(Exception):
    pass


class InvalidKeyError(Exception):
    pass


class SyncRequestAlreadyProcessed(Exception):
    pass


class MissingTrieNode(KeyError):
    """
    Raised when a node of the trie is not available in the database,
    for the given key in the current state root.

    Subclasses KeyError for backwards compatibility.
    """
    def __init__(self, missing_node_hash, root_hash, requested_key, *args):
        if not isinstance(missing_node_hash, bytes):
            raise TypeError("Missing node hash must be bytes, was: %r" % missing_node_hash)
        elif not isinstance(root_hash, bytes):
            raise TypeError("Root hash must be bytes, was: %r" % root_hash)
        elif not isinstance(requested_key, bytes):
            raise TypeError("Requested key must be bytes, was: %r" % requested_key)

        super().__init__(missing_node_hash, root_hash, requested_key, *args)

    def __repr__(self):
        return "MissingTrieNode: {}".format(self)

    def __str__(self):
        return "Trie database is missing hash {} needed to look up key {} at root hash {}".format(
            encode_hex(self.missing_node_hash),
            encode_hex(self.requested_key),
            encode_hex(self.root_hash),
        )

    @property
    def missing_node_hash(self):
        return self.args[0]

    @property
    def root_hash(self):
        return self.args[1]

    @property
    def requested_key(self):
        return self.args[2]
