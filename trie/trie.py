import itertools

import rlp

from trie.constants import (
    BLANK_NODE,
    BLANK_NODE_HASH,
    NODE_TYPE_BLANK,
    NODE_TYPE_LEAF,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_BRANCH,
    BLANK_HASH,
    KV_TYPE,
    BRANCH_TYPE,
    LEAF_TYPE,
    BYTE_0,
    BYTE_1,
)
from trie.validation import (
    validate_is_node,
    validate_is_bytes,
    validate_is_bin_node,
)
from trie.exceptions import (
    LeafNodeOverrideError,
)

from trie.utils.sha3 import (
    keccak,
)
from trie.utils.nibbles import (
    bytes_to_nibbles,
    decode_nibbles,
    encode_nibbles,
)
from trie.utils.binaries import (
    encode_to_bin,
)
from trie.utils.nodes import (
    get_node_type,
    extract_key,
    compute_leaf_key,
    compute_extension_key,
    is_extension_node,
    is_leaf_node,
    is_blank_node,
    consume_common_prefix,
    key_starts_with,
    parse_node,
    encode_kv_node,
    encode_branch_node,
    encode_leaf_node,
    get_common_prefix_length,
)


# sanity check
assert BLANK_NODE_HASH == keccak(rlp.encode(b''))
assert BLANK_HASH == keccak(b'')


class Trie(object):
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
        root_node = self._get_node(self.root_hash)

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
        root_node = self._get_node(self.root_hash)

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
        root_node = self._get_node(self.root_hash)

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
    # Convenience
    #
    @property
    def root_node(self):
        return self._get_node(self.root_hash)

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

    def _get_node(self, node_hash):
        if node_hash == BLANK_NODE:
            return BLANK_NODE
        elif node_hash == BLANK_NODE_HASH:
            return BLANK_NODE

        if len(node_hash) < 32:
            encoded_node = node_hash
        else:
            encoded_node = self.db[node_hash]
        node = self._decode_node(encoded_node)

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

    def _decode_node(self, encoded_node_or_hash):
        if encoded_node_or_hash == BLANK_NODE:
            return BLANK_NODE
        elif isinstance(encoded_node_or_hash, list):
            return encoded_node_or_hash
        else:
            return rlp.decode(encoded_node_or_hash)

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
        sub_node = self._get_node(sub_node_hash)
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

        node_to_delete = self._get_node(node[trie_key[0]])

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
        sub_node = self._get_node(node[1])

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
            sub_node = self._get_node(node[trie_key[0]])

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
                sub_node = self._get_node(node[1])
                # TODO: this needs to cleanup old storage.
                new_node = self._set(sub_node, trie_key_remainder, value)
        elif not current_key_remainder:
            if is_extension:
                sub_node = self._get_node(node[1])
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
            sub_node = self._get_node(node[trie_key[0]])
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
                sub_node = self._get_node(node[1])
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


class BinaryTrie(object):
    def __init__(self, db, root_hash=BLANK_HASH):
        self.db = db
        validate_is_bytes(root_hash)
        self.root_hash = root_hash

    def get(self, key):
        """
        Fetches the value with a given keypath from the given node.

        Keyp will be encoded into binary array format first
        """
        validate_is_bytes(key)

        return self._get(self.root_hash, encode_to_bin(key))

    def _get(self, node_hash, keypath):
        """
        Note: keypath should be in binary array format, i.e., encoded by encode_to_bin()
        """
        # Empty trie
        if node_hash == BLANK_HASH:
            return None
        nodetype, left_child, right_child = parse_node(self.db[node_hash])
        # Key-value node descend
        if nodetype == LEAF_TYPE:
            return right_child
        elif nodetype == KV_TYPE:
            # Keypath too short
            if not keypath:
                return None
            if keypath[:len(left_child)] == left_child:
                return self._get(right_child, keypath[len(left_child):])
            else:
                return None
        # Branch node descend
        elif nodetype == BRANCH_TYPE:
            # Keypath too short
            if not keypath:
                return None
            if keypath[:1] == BYTE_0:
                return self._get(left_child, keypath[1:])
            else:
                return self._get(right_child, keypath[1:])

    def set(self, key, value):
        """
        Sets the value at the given keypath from the given node

        Keyp will be encoded into binary array format first
        """
        validate_is_bytes(key)
        validate_is_bytes(value)

        self.root_hash = self._set(self.root_hash, encode_to_bin(key), value)

    def _set(self, node_hash, keypath, value):
        """
        Note: keypath should be in binary array format, i.e., encoded by encode_to_bin()
        """
        # Empty trie
        if node_hash == BLANK_HASH:
            if value:
                return self._hash_and_save(
                    encode_kv_node(keypath, self._hash_and_save(encode_leaf_node(value)))
                )
            else:
                return BLANK_HASH
        nodetype, left_child, right_child = parse_node(self.db[node_hash])
        # Node is a leaf node
        if nodetype == LEAF_TYPE:
            # Keypath must match, there should be no remaining keypath
            if keypath:
                raise LeafNodeOverrideError(
                    "Existing kv pair is being effaced because"
                    " it's key is the prefix of the new key")
            return self._hash_and_save(encode_leaf_node(value)) if value else BLANK_HASH
        # node is a key-value node
        elif nodetype == KV_TYPE:
            # Keypath too short
            if not keypath:
                return node_hash
            return self._set_kv_node(keypath, node_hash, nodetype, left_child, right_child, value)
        # node is a branch node
        elif nodetype == BRANCH_TYPE:
            # Keypath too short
            if not keypath:
                return node_hash
            return self._set_branch_node(keypath, nodetype, left_child, right_child, value)
        raise Exception("Invariant: This shouldn't ever happen")

    def _set_kv_node(self, keypath, node_hash, node_type, left_child, right_child, value):
        # Keypath prefixes match
        if keypath[:len(left_child)] == left_child:
            # Recurse into child
            subnode_hash = self._set(right_child, keypath[len(left_child):], value)
            # If child is empty
            if subnode_hash == BLANK_HASH:
                return BLANK_HASH
            subnodetype, sub_left_child, sub_right_child = parse_node(self.db[subnode_hash])
            # If the child is a key-value node, compress together the keypaths
            # into one node
            if subnodetype == KV_TYPE:
                return self._hash_and_save(
                    encode_kv_node(left_child + sub_left_child, sub_right_child)
                )
            else:
                return self._hash_and_save(encode_kv_node(left_child, subnode_hash))
        # Keypath prefixes don't match. Here we will be converting a key-value node
        # of the form (k, CHILD) into a structure of one of the following forms:
        # 1.    (k[:-1], (NEWCHILD, CHILD))
        # 2.    (k[:-1], ((k2, NEWCHILD), CHILD))
        # 3.    (k1, ((k2, CHILD), NEWCHILD))
        # 4.    (k1, ((k2, CHILD), (k2', NEWCHILD))
        # 5.    (CHILD, NEWCHILD)
        # 6.    ((k[1:], CHILD), (k', NEWCHILD))
        # 7.    ((k[1:], CHILD), NEWCHILD)
        # 8.    (CHILD, (k[1:], NEWCHILD))
        else:
            common_prefix_len = get_common_prefix_length(left_child, keypath[:len(left_child)])
            # New key-value pair can not contain empty value
            if not value:
                return node_hash
            # valnode: the child node that has the new value we are adding
            # Case 1: keypath prefixes almost match, so we are in case (1), (2), (5), (6)
            if len(keypath) == common_prefix_len + 1:
                valnode = self._hash_and_save(encode_leaf_node(value))
            # Case 2: keypath prefixes mismatch in the middle, so we need to break
            # the keypath in half. We are in case (3), (4), (7), (8)
            else:
                valnode = self._hash_and_save(
                    encode_kv_node(
                        keypath[common_prefix_len+1:],
                        self._hash_and_save(encode_leaf_node(value)),
                    )
                )
            # oldnode: the child node the has the old child value
            # Case 1: (1), (3), (5), (6)
            if len(left_child) == common_prefix_len + 1:
                oldnode = right_child
            # (2), (4), (6), (8)
            else:
                oldnode = self._hash_and_save(
                    encode_kv_node(left_child[common_prefix_len+1:], right_child)
                )
            # Create the new branch node (because the key paths diverge, there has to
            # be some "first bit" at which they diverge, so there must be a branch
            # node somewhere)
            if keypath[common_prefix_len:common_prefix_len+1] == BYTE_1:
                newsub = self._hash_and_save(encode_branch_node(oldnode, valnode))
            else:
                newsub = self._hash_and_save(encode_branch_node(valnode, oldnode))
            # Case 1: keypath prefixes match in the first bit, so we still need
            # a kv node at the top
            # (1) (2) (3) (4)
            if common_prefix_len:
                return self._hash_and_save(
                    encode_kv_node(left_child[:common_prefix_len], newsub)
                )
            # Case 2: keypath prefixes diverge in the first bit, so we replace the
            # kv node with a branch node
            # (5) (6) (7) (8)
            else:
                return newsub

    def _set_branch_node(self, keypath, node_type, left_child, right_child, value):
        # Which child node to update? Depends on first bit in keypath
        if keypath[:1] == BYTE_0:
            new_left_child = self._set(left_child, keypath[1:], value)
            new_right_child = right_child
        else:
            new_right_child = self._set(right_child, keypath[1:], value)
            new_left_child = left_child
        # Compress branch node into kv node
        if new_left_child == BLANK_HASH or new_right_child == BLANK_HASH:
            subnodetype, sub_left_child, sub_right_child = parse_node(
                self.db[
                    new_left_child
                    if new_left_child != BLANK_HASH
                    else new_right_child]
            )
            first_bit = BYTE_1 if new_right_child != BLANK_HASH else BYTE_0
            # Compress (k1, (k2, NODE)) -> (k1 + k2, NODE)
            if subnodetype == KV_TYPE:
                return self._hash_and_save(
                    encode_kv_node(first_bit + sub_left_child, sub_right_child)
                )
            # kv node pointing to a branch node
            elif subnodetype in (BRANCH_TYPE, LEAF_TYPE):
                return self._hash_and_save(
                    encode_kv_node(
                        first_bit,
                        new_left_child
                        if new_left_child != BLANK_HASH
                        else new_right_child
                    )
                )
        else:
            return self._hash_and_save(encode_branch_node(new_left_child, new_right_child))

    def exists(self, key):
        return self.get(key) != BLANK_NODE

    def delete(self, key):
        """
        Equals to setting the value to None
        """
        self.root_hash = self._set(self.root_hash, encode_to_bin(key), b'')

    #
    # Convenience
    #
    @property
    def root_node(self):
        return self.db[self.root_hash]

    @root_node.setter
    def root_node(self, node):
        validate_is_bin_node(node)
        self.root_hash = self._hash_and_save(node)

    #
    # Utils
    #
    def _hash_and_save(self, node):
        """
        Saves a node into the database and returns its hash
        """
        validate_is_bin_node(node)

        node_hash = keccak(node)
        self.db[node_hash] = node
        return node_hash

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
