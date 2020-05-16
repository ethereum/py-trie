from typing import Optional

from hexbytes import HexBytes

from trie.typing import (
    Nibbles,
    HexaryTrieNode,
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
    def __init__(
            self,
            missing_node_hash: 'Hash32',
            root_hash: 'Hash32',
            requested_key: bytes,
            prefix: Nibbles = None,
            *args):

        if not isinstance(missing_node_hash, bytes):
            raise TypeError("Missing node hash must be bytes, was: %r" % missing_node_hash)
        elif not isinstance(root_hash, bytes):
            raise TypeError("Root hash must be bytes, was: %r" % root_hash)
        elif not isinstance(requested_key, bytes):
            raise TypeError("Requested key must be bytes, was: %r" % requested_key)

        if prefix is not None:
            prefix_nibbles = Nibbles(prefix)
        else:
            prefix_nibbles = None

        super().__init__(
            HexBytes(missing_node_hash),
            HexBytes(root_hash),
            HexBytes(requested_key),
            prefix_nibbles,
            *args,
        )

    def __repr__(self) -> str:
        return (
            f"MissingTrieNode({self.missing_node_hash}, {self.root_hash}, "
            f"{self.requested_key}, prefix={self.prefix})"
        )

    def __str__(self) -> str:
        return (
            f"Trie database is missing hash {self.missing_node_hash!r} needed to look up node at"
            f" prefix {self.prefix}, when searching for key {self.requested_key!r} at root"
            f" hash {self.root_hash!r}"
        )

    @property
    def missing_node_hash(self) -> HexBytes:
        return self.args[0]

    @property
    def root_hash(self) -> HexBytes:
        return self.args[1]

    @property
    def requested_key(self) -> HexBytes:
        return self.args[2]

    @property
    def prefix(self) -> Optional[Nibbles]:
        """
        The tuple of nibbles that navigate to the missing node. For example, a missing
        root would have a prefix of (), and a missing left-most child of the
        root would have a prefix of (0, ).
        """
        return self.args[3]


class MissingTraversalNode(Exception):
    """
    Raised when a node of the trie is not available in the database,
    during HexaryTrie.traverse() or .traverse_from().

    This is triggered in the same situation as MissingTrieNode, but with less
    information available, because traversal can start from the middle of a trie.
        - traverse_from() ignore's the trie's root, so the root hash is unknown
        - the requested_key and prefix are unavailable because only the suffix of the key is known
    """
    def __init__(self, missing_node_hash: 'Hash32', nibbles_traversed: Nibbles, *args) -> None:
        if not isinstance(missing_node_hash, bytes):
            raise TypeError("Missing node hash must be bytes, was: %r" % missing_node_hash)

        super().__init__(HexBytes(missing_node_hash), Nibbles(nibbles_traversed), *args)

    def __repr__(self) -> str:
        return f"MissingTraversalNode({self.missing_node_hash}, {self.nibbles_traversed})"

    def __str__(self) -> str:
        return (
            f"Trie database is missing hash {self.missing_node_hash!r}, found when traversing "
            f"down {self.nibbles_traversed}."
        )

    @property
    def missing_node_hash(self) -> HexBytes:
        return self.args[0]

    @property
    def nibbles_traversed(self) -> Nibbles:
        """
        Nibbles traversed down from the starting node to the missing node.
        """
        return self.args[1]


class TraversedPartialPath(Exception):
    """
    Raised when a traversal key ends in the middle of a partial path. It might be in
    an extension node or a leaf node.
    """
    def __init__(self, nibbles_traversed: Nibbles, node: HexaryTrieNode, *args) -> None:
        # TODO drop Nibbles() cast when type checking is turned on
        super().__init__(Nibbles(nibbles_traversed), node, *args)

    def __repr__(self) -> str:
        return f"TraversedPartialPath({self.nibbles_traversed}, {self.node})"

    def __str__(self) -> str:
        return f"Could not traverse through {self.node} at {self.nibbles_traversed}"

    @property
    def nibbles_traversed(self) -> Nibbles:
        """
        The nibbles traversed until the attached node, which could not be traversed into.
        """
        return self.args[0]

    @property
    def node(self) -> HexaryTrieNode:
        """
        The node which could not be traversed into. This is any leaf, or an extension node
        where traversal went part-way into the path. It must not be a branch node.
        """
        return self.args[1]
