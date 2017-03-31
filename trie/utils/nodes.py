from trie.constants import (
    NODE_TYPE_BLANK,
    NODE_TYPE_LEAF,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_BRANCH,
    BLANK_NODE,
)
from trie.exceptions import (
    InvalidNode,
)

from .nibbles import (
    decode_nibbles,
    encode_nibbles,
    is_nibbles_terminated,
    add_nibbles_terminator,
    remove_nibbles_terminator,
)


def get_node_type(node):
    if node == BLANK_NODE:
        return NODE_TYPE_BLANK
    elif len(node) == 2:
        key, _ = node
        nibbles = decode_nibbles(key)
        if is_nibbles_terminated(nibbles):
            return NODE_TYPE_LEAF
        else:
            return NODE_TYPE_EXTENSION
    elif len(node) == 17:
        return NODE_TYPE_BRANCH
    else:
        raise InvalidNode("Unable to determine node type")


def is_blank_node(node):
    return node == BLANK_NODE


def is_leaf_node(node):
    if len(node) != 2:
        return False
    key, _ = node
    nibbles = decode_nibbles(key)
    return is_nibbles_terminated(nibbles)


def is_extension_node(node):
    if len(node) != 2:
        return False
    key, _ = node
    nibbles = decode_nibbles(key)
    return not is_nibbles_terminated(nibbles)


def is_branch_node(node):
    return len(node) == 17


def extract_key(node):
    prefixed_key, _ = node
    key = remove_nibbles_terminator(decode_nibbles(prefixed_key))
    return key


def compute_leaf_key(nibbles):
    return encode_nibbles(add_nibbles_terminator(nibbles))


def compute_extension_key(nibbles):
    return encode_nibbles(nibbles)


def get_common_prefix_length(left_key, right_key):
    for idx, (left_nibble, right_nibble) in enumerate(zip(left_key, right_key)):
        if left_nibble != right_nibble:
            return idx
    return min(len(left_key), len(right_key))


def consume_common_prefix(left_key, right_key):
    common_prefix_length = get_common_prefix_length(left_key, right_key)
    common_prefix = left_key[:common_prefix_length]
    left_remainder = left_key[common_prefix_length:]
    right_remainder = right_key[common_prefix_length:]
    return common_prefix, left_remainder, right_remainder


def key_starts_with(full_key, partial_key):
    return all(left == right for left, right in zip(full_key, partial_key))
