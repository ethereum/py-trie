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


class MissingTrieNode(Exception):
    """
    Raised when a node of the trie is not available in the database,
    in the current state root.

    This may happen when trying to read out the value of a key, or when simply
    traversing the trie.
    """
    def __init__(self, missing_node_hash, root_hash, requested_key, prefix=None, *args):
        if not isinstance(missing_node_hash, bytes):
            raise TypeError("Missing node hash must be bytes, was: %r" % missing_node_hash)
        elif not isinstance(root_hash, bytes):
            raise TypeError("Root hash must be bytes, was: %r" % root_hash)
        elif requested_key is not None and not isinstance(requested_key, bytes):
            raise TypeError("Requested key must be bytes or None, was: %r" % requested_key)

        if prefix is not None:
            from trie.validation import validate_is_nibbles
            try:
                validate_is_nibbles(prefix)
            except ValidationError:
                raise TypeError("Key prefix must be tuple of ints 0-15, was: %r" % requested_key)

        super().__init__(missing_node_hash, root_hash, requested_key, prefix, *args)

    def __repr__(self):
        return (
            f"MissingTrieNode({self.missing_node_hash}, {self.root_hash}, "
            f"{self.requested_key}, prefix={self.prefix})"
        )

    def __str__(self):
        return (
            "Trie database is missing hash {} needed to look up node at prefix {}, "
            "when searching for key {} at root hash {}"
        ).format(
            encode_hex(self.missing_node_hash),
            self.prefix if self.prefix is not None else "<NO_PREFIX>",
            encode_hex(self.requested_key) if self.requested_key is not None else "<NO_KEY>",
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

    @property
    def prefix(self):
        """
        The tuple of nibbles that navigate to the missing node. For example, a missing
        root would have a prefix of (), and a missing left-most child of the
        root would have a prefix of (0, ).
        """
        return self.args[3]
