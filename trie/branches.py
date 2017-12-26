from trie.trie import (
    BinaryTrie,
)
from trie.exceptions import (
    InvalidKeyError,
)
from trie.constants import (
    BLANK_HASH,
    KV_TYPE,
    BRANCH_TYPE,
    LEAF_TYPE,
    BYTE_0,
)
from trie.validation import (
    validate_is_bytes,
)

from trie.utils.sha3 import (
    keccak,
)
from trie.utils.binaries import (
    encode_to_bin,
)
from trie.utils.nodes import (
    parse_node,
)


def if_branch_exist(db, root_hash, key_prefix):
    """
    Given a key prefix, return whether this prefix is
    the prefix of an existing key in the trie.
    """
    validate_is_bytes(key_prefix)

    return _if_branch_exist(db, root_hash, encode_to_bin(key_prefix))


def _if_branch_exist(db, node_hash, key_prefix):
    # Empty trie
    if node_hash == BLANK_HASH:
        return False
    nodetype, left_child, right_child = parse_node(db[node_hash])
    if nodetype == LEAF_TYPE:
        if key_prefix:
            return False
        return True
    elif nodetype == KV_TYPE:
        if not key_prefix:
            return True
        if len(key_prefix) < len(left_child):
            if key_prefix == left_child[:len(key_prefix)]:
                return True
            return False
        else:
            if key_prefix[:len(left_child)] == left_child:
                return _if_branch_exist(db, right_child, key_prefix[len(left_child):])
            return False
    elif nodetype == BRANCH_TYPE:
        if not key_prefix:
            return True
        if key_prefix[:1] == BYTE_0:
            return _if_branch_exist(db, left_child, key_prefix[1:])
        else:
            return _if_branch_exist(db, right_child, key_prefix[1:])


def get_branch(db, root_hash, key):
    """
    Get a long-format Merkle branch
    """
    validate_is_bytes(key)

    return _get_branch(db, root_hash, encode_to_bin(key))


def _get_branch(db, node_hash, keypath):
    if node_hash == BLANK_HASH:
        return []
    node = db[node_hash]
    nodetype, left_child, right_child = parse_node(node)
    if nodetype == LEAF_TYPE:
        if not keypath:
            return [node]
        else:
            raise InvalidKeyError("Key too long")
    elif nodetype == KV_TYPE:
        if not keypath:
            raise InvalidKeyError("Key too short")
        if keypath[:len(left_child)] == left_child:
            return [node] + _get_branch(
                db,
                right_child,
                keypath[len(left_child):]
            )
        else:
            raise InvalidKeyError("Key does not exist")
    elif nodetype == BRANCH_TYPE:
        if not keypath:
            raise InvalidKeyError("Key too short")
        if keypath[:1] == BYTE_0:
            return [node] + _get_branch(db, left_child, keypath[1:])
        else:
            return [node] + _get_branch(db, right_child, keypath[1:])


def verify_branch(branch, root_hash, key, value):
    validate_is_bytes(key)

    db = {keccak(node): node for node in branch}
    assert BinaryTrie(db=db, root_hash=root_hash).get(key) == value
    return True


def get_trie_nodes(db, node_hash):
    """
    Get full trie of a given root node
    """
    if node_hash in db:
        node = db[node_hash]
    else:
        return []
    nodetype, left_child, right_child = parse_node(node)
    if nodetype == KV_TYPE:
        return [node] + get_trie_nodes(db, right_child)
    elif nodetype == BRANCH_TYPE:
        return [node] + get_trie_nodes(db, left_child) + get_trie_nodes(db, right_child)
    elif nodetype == LEAF_TYPE:
        return [node]


def get_witness(db, node_hash, key):
    """
    Get all witness given a keypath prefix.
    Include

    1. witness along the keypath and
    2. witness in the subtrie of the last node in keypath
    """
    validate_is_bytes(key)

    return _get_witness(db, node_hash, encode_to_bin(key))


def _get_witness(db, node_hash, keypath):
    if not keypath:
        return get_trie_nodes(db, node_hash)
    if node_hash in db:
        node = db[node_hash]
    else:
        return []
    nodetype, left_child, right_child = parse_node(node)
    if nodetype == LEAF_TYPE:
        if keypath:
            raise InvalidKeyError("Key too long")
    elif nodetype == KV_TYPE:
        if len(keypath) < len(left_child) and left_child[:len(keypath)] == keypath:
            return [node] + get_trie_nodes(db, right_child)
        if keypath[:len(left_child)] == left_child:
            return [node] + _get_witness(db, right_child, keypath[len(left_child):])
        else:
            raise InvalidKeyError("Key does not exist")
    elif nodetype == BRANCH_TYPE:
        if keypath[:1] == BYTE_0:
            return [node] + _get_witness(db, left_child, keypath[1:])
        else:
            return [node] + _get_witness(db, right_child, keypath[1:])
