import itertools

import rlp

from eth_utils import (
    keccak,
)

from trie.constants import (
    BLANK_NODE,
    BLANK_NODE_HASH,
    NODE_TYPE_BLANK,
    NODE_TYPE_LEAF,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_BRANCH,
    BLANK_HASH,
)
from trie.exceptions import (
    BadTrieProof,
)
from trie.utils.nibbles import (
    bytes_to_nibbles,
    decode_nibbles,
    encode_nibbles,
)
from trie.utils.nodes import (
    decode_node,
    get_node_type,
    extract_key,
    compute_leaf_key,
    compute_extension_key,
    is_blank_node,
    is_extension_node,
    is_leaf_node,
    consume_common_prefix,
    key_starts_with,
)
from trie.validation import (
    validate_is_node,
    validate_is_bytes,
)


# sanity check
assert BLANK_NODE_HASH == keccak(rlp.encode(b''))
assert BLANK_HASH == keccak(b'')


class HexaryTrie(object):
    db = None
    root_hash = None

    # Shortcuts
    BLANK_NODE_HASH = BLANK_NODE_HASH
    BLANK_NODE = BLANK_NODE

    def __init__(self, db, root_hash=BLANK_NODE_HASH):
        self.db = db
        validate_is_bytes(root_hash)
        self.root_hash = root_hash

    def get(self, key):
        validate_is_bytes(key)

        trie_key = bytes_to_nibbles(key)
        root_node = self.get_node(self.root_hash)

        return self._get(root_node, trie_key)

    def _get(self, node, trie_key):
        node_type = get_node_type(node)

        if node_type == NODE_TYPE_BLANK:
            return BLANK_NODE
        elif node_type in {NODE_TYPE_LEAF, NODE_TYPE_EXTENSION}:
            return self._get_kv_node(node, trie_key)
        elif node_type == NODE_TYPE_BRANCH:
            return self._get_branch_node(node, trie_key)
        else:
            raise Exception("Invariant: This shouldn't ever happen")

    def set(self, key, value):
        validate_is_bytes(key)
        validate_is_bytes(value)

        trie_key = bytes_to_nibbles(key)
        root_node = self.get_node(self.root_hash)

        new_node = self._set(root_node, trie_key, value)
        self._set_root_node(new_node)

    def _set(self, node, trie_key, value):
        node_type = get_node_type(node)

        if node_type == NODE_TYPE_BLANK:
            return [
                compute_leaf_key(trie_key),
                value,
            ]
        elif node_type in {NODE_TYPE_LEAF, NODE_TYPE_EXTENSION}:
            return self._set_kv_node(node, trie_key, value)
        elif node_type == NODE_TYPE_BRANCH:
            return self._set_branch_node(node, trie_key, value)
        else:
            raise Exception("Invariant: This shouldn't ever happen")

    def exists(self, key):
        validate_is_bytes(key)

        return self.get(key) != BLANK_NODE

    def delete(self, key):
        validate_is_bytes(key)

        trie_key = bytes_to_nibbles(key)
        root_node = self.get_node(self.root_hash)

        new_node = self._delete(root_node, trie_key)
        self._set_root_node(new_node)

    def _delete(self, node, trie_key):
        node_type = get_node_type(node)

        if node_type == NODE_TYPE_BLANK:
            return BLANK_NODE
        elif node_type in {NODE_TYPE_LEAF, NODE_TYPE_EXTENSION}:
            return self._delete_kv_node(node, trie_key)
        elif node_type == NODE_TYPE_BRANCH:
            return self._delete_branch_node(node, trie_key)
        else:
            raise Exception("Invariant: This shouldn't ever happen")

    #
    # Trie Proofs
    #
    @classmethod
    def get_from_proof(cls, root_hash, key, proof):
        trie = cls({})

        for node in proof:
            trie._persist_node(node)
        trie.root_hash = root_hash
        try:
            return trie.get(key)
        except KeyError as e:
            raise BadTrieProof("Missing proof node with hash {}".format(e.args))

    #
    # Convenience
    #
    @property
    def root_node(self):
        return self.get_node(self.root_hash)

    @root_node.setter
    def root_node(self, value):
        self._set_root_node(value)

    #
    # Utils
    #
    def _set_root_node(self, root_node):
        validate_is_node(root_node)
        encoded_root_node = rlp.encode(root_node)
        self.root_hash = keccak(encoded_root_node)
        self.db[self.root_hash] = encoded_root_node

    def get_node(self, node_hash):
        if node_hash == BLANK_NODE:
            return BLANK_NODE
        elif node_hash == BLANK_NODE_HASH:
            return BLANK_NODE

        if len(node_hash) < 32:
            encoded_node = node_hash
        else:
            encoded_node = self.db[node_hash]
        node = decode_node(encoded_node)

        return node

    def _persist_node(self, node):
        validate_is_node(node)
        if is_blank_node(node):
            return BLANK_NODE
        encoded_node = rlp.encode(node)
        if len(encoded_node) < 32:
            return node

        encoded_node_hash = keccak(encoded_node)
        self.db[encoded_node_hash] = encoded_node
        return encoded_node_hash

    #
    # Node Operation Helpers
    def _normalize_branch_node(self, node):
        """
        A branch node which is left with only a single non-blank item should be
        turned into either a leaf or extension node.
        """
        iter_node = iter(node)
        if any(iter_node) and any(iter_node):
            return node

        if node[16]:
            return [compute_leaf_key([]), node[16]]

        sub_node_idx, sub_node_hash = next(
            (idx, v)
            for idx, v
            in enumerate(node[:16])
            if v
        )
        sub_node = self.get_node(sub_node_hash)
        sub_node_type = get_node_type(sub_node)

        if sub_node_type in {NODE_TYPE_LEAF, NODE_TYPE_EXTENSION}:
            new_subnode_key = encode_nibbles(tuple(itertools.chain(
                [sub_node_idx],
                decode_nibbles(sub_node[0]),
            )))
            return [new_subnode_key, sub_node[1]]
        elif sub_node_type == NODE_TYPE_BRANCH:
            subnode_hash = self._persist_node(sub_node)
            return [encode_nibbles([sub_node_idx]), subnode_hash]
        else:
            raise Exception("Invariant: this code block should be unreachable")

    #
    # Node Operations
    #
    def _delete_branch_node(self, node, trie_key):
        if not trie_key:
            node[-1] = BLANK_NODE
            return self._normalize_branch_node(node)

        node_to_delete = self.get_node(node[trie_key[0]])

        sub_node = self._delete(node_to_delete, trie_key[1:])
        encoded_sub_node = self._persist_node(sub_node)

        if encoded_sub_node == node[trie_key[0]]:
            return node

        node[trie_key[0]] = encoded_sub_node
        if encoded_sub_node == BLANK_NODE:
            return self._normalize_branch_node(node)

        return node

    def _delete_kv_node(self, node, trie_key):
        current_key = extract_key(node)

        if not key_starts_with(trie_key, current_key):
            # key not present?....
            return node

        node_type = get_node_type(node)

        if node_type == NODE_TYPE_LEAF:
            if trie_key == current_key:
                return BLANK_NODE
            else:
                return node

        sub_node_key = trie_key[len(current_key):]
        sub_node = self.get_node(node[1])

        new_sub_node = self._delete(sub_node, sub_node_key)
        encoded_new_sub_node = self._persist_node(new_sub_node)

        if encoded_new_sub_node == node[1]:
            return node

        if new_sub_node == BLANK_NODE:
            return BLANK_NODE

        new_sub_node_type = get_node_type(new_sub_node)
        if new_sub_node_type in {NODE_TYPE_LEAF, NODE_TYPE_EXTENSION}:
            new_key = current_key + decode_nibbles(new_sub_node[0])
            return [encode_nibbles(new_key), new_sub_node[1]]

        if new_sub_node_type == NODE_TYPE_BRANCH:
            return [encode_nibbles(current_key), encoded_new_sub_node]

        raise Exception("Invariant, this code path should not be reachable")

    def _set_branch_node(self, node, trie_key, value):
        if trie_key:
            sub_node = self.get_node(node[trie_key[0]])

            new_node = self._set(sub_node, trie_key[1:], value)
            node[trie_key[0]] = self._persist_node(new_node)
        else:
            node[-1] = value
        return node

    def _set_kv_node(self, node, trie_key, value):
        current_key = extract_key(node)
        common_prefix, current_key_remainder, trie_key_remainder = consume_common_prefix(
            current_key,
            trie_key,
        )
        is_extension = is_extension_node(node)

        if not current_key_remainder and not trie_key_remainder:
            if is_leaf_node(node):
                return [node[0], value]
            else:
                sub_node = self.get_node(node[1])
                # TODO: this needs to cleanup old storage.
                new_node = self._set(sub_node, trie_key_remainder, value)
        elif not current_key_remainder:
            if is_extension:
                sub_node = self.get_node(node[1])
                # TODO: this needs to cleanup old storage.
                new_node = self._set(sub_node, trie_key_remainder, value)
            else:
                subnode_position = trie_key_remainder[0]
                subnode_key = compute_leaf_key(trie_key_remainder[1:])
                sub_node = [subnode_key, value]

                new_node = [BLANK_NODE] * 16 + [node[1]]
                new_node[subnode_position] = self._persist_node(sub_node)
        else:
            new_node = [BLANK_NODE] * 17

            if len(current_key_remainder) == 1 and is_extension:
                new_node[current_key_remainder[0]] = node[1]
            else:
                if is_extension:
                    compute_key_fn = compute_extension_key
                else:
                    compute_key_fn = compute_leaf_key

                new_node[current_key_remainder[0]] = self._persist_node([
                    compute_key_fn(current_key_remainder[1:]),
                    node[1],
                ])

            if trie_key_remainder:
                new_node[trie_key_remainder[0]] = self._persist_node([
                    compute_leaf_key(trie_key_remainder[1:]),
                    value,
                ])
            else:
                new_node[-1] = value

        if common_prefix:
            new_node_key = self._persist_node(new_node)
            return [compute_extension_key(common_prefix), new_node_key]
        else:
            return new_node

    def _get_branch_node(self, node, trie_key):
        if not trie_key:
            return node[16]
        else:
            sub_node = self.get_node(node[trie_key[0]])
            return self._get(sub_node, trie_key[1:])

    def _get_kv_node(self, node, trie_key):
        current_key = extract_key(node)
        node_type = get_node_type(node)

        if node_type == NODE_TYPE_LEAF:
            if trie_key == current_key:
                return node[1]
            else:
                return BLANK_NODE
        elif node_type == NODE_TYPE_EXTENSION:
            if key_starts_with(trie_key, current_key):
                sub_node = self.get_node(node[1])
                return self._get(sub_node, trie_key[len(current_key):])
            else:
                return BLANK_NODE
        else:
            raise Exception("Invariant: unreachable code path")

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
