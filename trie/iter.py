from trie.constants import (
    NODE_TYPE_BLANK,
    NODE_TYPE_LEAF,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_BRANCH,
)
from trie.exceptions import (
    InvalidNode,
)
from trie.utils.nibbles import (
    bytes_to_nibbles,
    nibbles_to_bytes,
    remove_nibbles_terminator,
)
from trie.utils.nodes import (
    get_node_type,
    extract_key,
    key_starts_with,
)


# FIXME: This is probably very inneficient and the code itself is quite convoluted. We should
# either look into refactoring or rewriting it from scratch eventually.
class NodeIterator:
    """Iterate over all nodes of a trie, ensuring its consistency."""

    def __init__(self, trie):
        self.trie = trie

    def next(self, key):
        key = bytes_to_nibbles(key)
        nibbles = self._iter(self.trie.root_node, key)
        if nibbles is None:
            return None
        return nibbles_to_bytes(remove_nibbles_terminator(nibbles))

    def _get_next(self, node):
        node_type = get_node_type(node)
        if node_type == NODE_TYPE_BLANK:
            return None
        elif node_type == NODE_TYPE_LEAF:
            curr_key = extract_key(node)
            return curr_key
        elif node_type == NODE_TYPE_EXTENSION:
            curr_key = extract_key(node)
            sub_node = self.trie.get_node(node[1])
            return curr_key + self._get_next(sub_node)
        elif node_type == NODE_TYPE_BRANCH:
            if node[16]:
                return (16,)
            for i in range(16):
                sub_node = self.trie.get_node(node[i])
                nibbles = self._get_next(sub_node)
                if nibbles is not None:
                    return (i,) + nibbles
            raise Exception("Invariant: this means we have an empty branch node")
        else:
            raise InvalidNode("Unexpected node type: %s" % node_type)

    def _iter(self, node, key):
        node_type = get_node_type(node)
        if node_type == NODE_TYPE_BLANK:
            return None
        elif node_type == NODE_TYPE_LEAF:
            descend_key = extract_key(node)
            if descend_key > key:
                return descend_key
            return None
        elif node_type == NODE_TYPE_BRANCH:
            scan_range = range(16)
            if len(key):
                sub_node = self.trie.get_node(node[key[0]])
                nibbles = self._iter(sub_node, key[1:])
                if nibbles is not None:
                    return (key[0],) + nibbles
                scan_range = range(key[0] + 1, 16)

            for i in scan_range:
                sub_node = self.trie.get_node(node[i])
                nibbles = self._get_next(sub_node)
                if nibbles is not None:
                    return (i,) + nibbles
            return None
        elif node_type == NODE_TYPE_EXTENSION:
            descend_key = extract_key(node)
            sub_node = self.trie.get_node(node[1])
            sub_key = key[len(descend_key):]
            if key_starts_with(key, descend_key):
                nibbles = self._iter(sub_node, sub_key)
                if nibbles is not None:
                    return descend_key + nibbles
            return None
