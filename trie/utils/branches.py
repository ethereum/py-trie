from trie.constants import (
    BLANK_HASH,
    KV_TYPE,
    BRANCH_TYPE,
    LEAF_TYPE,
    BYTE_0,
)
from trie.utils.binaries import (
    encode_to_bin,
)
from trie.utils.nodes import (
    parse_node,
)


def if_branch_exist(db, node_hash, key_prefix):
    return _if_branch_exist(db, node_hash, encode_to_bin(key_prefix))


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
