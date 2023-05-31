from trie.constants import (
    BINARY_TRIE_NODE_TYPES,
    BLANK_HASH,
    BLANK_NODE,
)
from trie.exceptions import (
    ValidationError,
)


def validate_is_bytes(value):
    if not isinstance(value, bytes):
        raise ValidationError(f"Value is not of type `bytes`: got '{type(value)}'")


def validate_length(value, length):
    if len(value) != length:
        raise ValidationError(f"Value is of length {len(value)}.  Must be {length}")


def validate_is_node(node):
    if node == BLANK_NODE:
        return
    elif len(node) == 2:
        key, value = node
        validate_is_bytes(key)
        if isinstance(value, list):
            validate_is_node(value)
        else:
            validate_is_bytes(value)
    elif len(node) == 17:
        validate_is_bytes(node[16])
        for sub_node in node[:16]:
            if sub_node == BLANK_NODE:
                continue
            elif isinstance(sub_node, list):
                validate_is_node(sub_node)
            else:
                validate_is_bytes(sub_node)
                validate_length(sub_node, 32)
    else:
        raise ValidationError(f"Invalid Node: {node}")


def validate_is_bin_node(node):
    if node == BLANK_HASH or node[0] in BINARY_TRIE_NODE_TYPES:
        return
    else:
        raise ValidationError(f"Invalid Node: {node}")
