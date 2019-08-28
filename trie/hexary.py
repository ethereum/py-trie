from collections import defaultdict
import contextlib
import functools
import itertools

from rlp.codec import encode_raw

from eth_hash.auto import (
    keccak,
)

from eth_utils import (
    to_list,
    to_tuple,
)
from eth_utils.toolz import (
    merge,
)

from trie.constants import (
    BLANK_NODE,
    BLANK_NODE_HASH,
    NODE_TYPE_BLANK,
    NODE_TYPE_LEAF,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_BRANCH,
)
from trie.exceptions import (
    BadTrieProof,
    MissingTrieNode,
    ValidationError,
)
from trie.utils.db import (
    ScratchDB,
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


class HexaryTrie:
    __slots__ = ('db', 'root_hash', 'is_pruning', '_ref_count')

    # Shortcuts
    BLANK_NODE_HASH = BLANK_NODE_HASH
    BLANK_NODE = BLANK_NODE

    def __init__(self, db, root_hash=BLANK_NODE_HASH, prune=False):
        """
        Important note about Pruning:

        The prune keyword is not intended for direct usage. It is likely
        to be changed or removed in future versions. If you want to prevent
        storage of unnecessary intermediate nodes, use the :meth:`squash_changes`
        context manager instead.

        Why? Unless working with an empty database, pruning will be overly aggressive,
        and delete nodes that are still used by other parts of the trie. This
        is prevented by squash_changes (by being overly conservative and not
        deleting any pre-existing nodes).
        """
        self.db = db
        validate_is_bytes(root_hash)
        self.root_hash = root_hash
        self.is_pruning = prune
        if prune:
            self._ref_count = defaultdict(int)
        else:
            self._ref_count = None

    def get(self, key):
        validate_is_bytes(key)

        trie_key = bytes_to_nibbles(key)
        try:
            root_node = self.get_node(self.root_hash)

            return self._get(root_node, trie_key)
        except KeyError as exc:
            self._raise_missing_node(exc, key)

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

    def _raise_missing_node(self, exception, key):
        # Indicate more information about which key was requested, which node was missing, etc
        raise MissingTrieNode(exception.args[0], self.root_hash, key) from exception

    def set(self, key, value):
        validate_is_bytes(key)
        validate_is_bytes(value)

        trie_key = bytes_to_nibbles(key)

        try:
            root_node = self.get_node(self.root_hash)

            new_node = self._set(root_node, trie_key, value)
        except KeyError as exc:
            self._raise_missing_node(exc, key)

        self._set_root_node(new_node)

    def _set(self, node, trie_key, value):
        node_type = get_node_type(node)

        with self._prune_node(node):
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

        try:
            return self.get(key) != BLANK_NODE
        except KeyError as exc:
            self._raise_missing_node(exc, key)

    def delete(self, key):
        validate_is_bytes(key)

        trie_key = bytes_to_nibbles(key)

        try:
            root_node = self.get_node(self.root_hash)

            new_node = self._delete(root_node, trie_key)
        except KeyError as exc:
            self._raise_missing_node(exc, key)

        self._set_root_node(new_node)

    def _delete(self, node, trie_key):
        node_type = get_node_type(node)

        with self._prune_node(node):
            if node_type == NODE_TYPE_BLANK:
                # ignore attempt to delete key from empty node
                return BLANK_NODE
            elif node_type in {NODE_TYPE_LEAF, NODE_TYPE_EXTENSION}:
                return self._delete_kv_node(node, trie_key)
            elif node_type == NODE_TYPE_BRANCH:
                return self._delete_branch_node(node, trie_key)
            else:
                raise Exception("Invariant: This shouldn't ever happen")

    @property
    def ref_count(self):
        if self._ref_count is None:
            raise Exception("Trie does not track node usage unless pruning is enabled")
        else:
            return self._ref_count

    #
    # Trie Proofs
    #
    @classmethod
    def get_from_proof(cls, root_hash, key, proof):
        trie = cls({})

        for node in proof:
            trie._set_raw_node(node)

        with trie.at_root(root_hash) as proven_snapshot:
            try:
                return proven_snapshot.get(key)
            except KeyError as e:
                raise BadTrieProof("Missing proof node with hash {}".format(e.args))

    def get_proof(self, key):
        validate_is_bytes(key)

        node = self.get_node(self.root_hash)
        trie_key = bytes_to_nibbles(key)

        return self._get_proof(node, trie_key)

    def _get_proof(self, node, trie_key, proven_len=0, last_proof=tuple()):
        updated_proof = last_proof + (node, )
        unproven_key = trie_key[proven_len:]

        node_type = get_node_type(node)
        if node_type == NODE_TYPE_BLANK:
            return last_proof
        elif node_type == NODE_TYPE_LEAF:
            return updated_proof
        elif node_type == NODE_TYPE_EXTENSION:
            current_key = extract_key(node)
            if key_starts_with(unproven_key, current_key):
                next_node = self.get_node(node[1])
                new_proven_len = proven_len + len(current_key)
                return self._get_proof(next_node, trie_key, new_proven_len, updated_proof)
            else:
                return updated_proof
        elif node_type == NODE_TYPE_BRANCH:
            if not unproven_key:
                return updated_proof
            next_node = self.get_node(node[unproven_key[0]])
            new_proven_len = proven_len + 1
            return self._get_proof(next_node, trie_key, new_proven_len, updated_proof)
        else:
            raise Exception("Invariant: This shouldn't ever happen")

    #
    # Convenience
    #
    @property
    def root_node(self):
        try:
            return self.get_node(self.root_hash)
        except KeyError as exc:
            self._raise_missing_node(exc, b'')

    @root_node.setter
    def root_node(self, value):
        self._set_root_node(value)

    #
    # Utils
    #

    @contextlib.contextmanager
    def _prune_node(self, node):
        """
        Prune the given node if context exits cleanly.
        """
        if self.is_pruning:
            # node is mutable, so capture the key for later pruning now
            prune_key, node_body = self._node_to_db_mapping(node)
            should_prune = (node_body is not None)
        else:
            should_prune = False

        yield

        # Prune only if no exception is raised
        if should_prune:
            self._prune_key(prune_key)

    def _prune_key(self, key):
        new_count = self.ref_count[key] - 1

        if new_count <= 0:
            # Ref count doesn't track keys that are already in the starting database,
            #   so ref count can go negative. Then, detect if key is in underlying:
            #   - If so, delete it and set the refcount down to 0
            #   - If not, raise an exception about trying to prune a node that doesn't exist
            try:
                del self.db[key]
            except KeyError as exc:
                raise ValidationError("Tried to prune key %r that doesn't exist" % key) from exc
            else:
                new_count = 0

        self.ref_count[key] = new_count

    def regenerate_ref_count(self):
        new_ref_count = defaultdict(int)

        keys_to_count = [self.root_hash]
        while keys_to_count:
            key = keys_to_count.pop()
            if key == b'' or isinstance(key, list) or key == BLANK_NODE_HASH:
                continue
            new_ref_count[key] += 1

            node = self.get_node(key)
            node_type = get_node_type(node)

            if node_type == NODE_TYPE_BLANK:
                continue
            if node_type == NODE_TYPE_BRANCH:
                keys_to_count.extend(node[:16])
            elif node_type == NODE_TYPE_EXTENSION:
                keys_to_count.append(node[1])

        return new_ref_count

    def _set_raw_node(self, raw_node):
        key, value = self._node_to_db_mapping(raw_node)
        if key == BLANK_NODE:
            # skip saving the blank node to DB
            return BLANK_NODE_HASH

        if value is None:
            # Some nodes are so small that they are not encoded during _node_to_db_mapping,
            # so we manually encode and hash it here:
            encoded_node = encode_raw(key)
            node_hash = keccak(encoded_node)
        else:
            encoded_node = value
            node_hash = key

        self._set_db_value(node_hash, encoded_node)
        return node_hash

    def _set_db_value(self, key, value):
        self.db[key] = value
        if self.is_pruning:
            self.ref_count[key] += 1

    def _set_root_node(self, root_node):
        validate_is_node(root_node)
        if self.is_pruning:
            old_root_hash = self.root_hash
            if old_root_hash != BLANK_NODE_HASH and old_root_hash in self.db:
                self._prune_key(old_root_hash)

        self.root_hash = self._set_raw_node(root_node)

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

    def _node_to_db_mapping(self, node):
        if self.is_pruning and isinstance(node, list):
            # When self.is_pruning is True, we'll often prune nodes that have been inserted
            # recently, so this hack allows us to use an LRU-cached implementation of
            # _node_to_db_mapping(), which improves the performance of _prune_node()
            # significantly.
            return self._cached_create_node_to_db_mapping(tuplify(node))
        else:
            return self._create_node_to_db_mapping(node)

    @functools.lru_cache(4096)
    def _cached_create_node_to_db_mapping(self, node):
        if isinstance(node, tuple):
            node = listify(node)
        return self._create_node_to_db_mapping(node)

    def _create_node_to_db_mapping(self, node):
        validate_is_node(node)
        if is_blank_node(node):
            return BLANK_NODE, None
        encoded_node = encode_raw(node)
        if len(encoded_node) < 32:
            return node, None

        encoded_node_hash = keccak(encoded_node)
        return encoded_node_hash, encoded_node

    def _persist_node(self, node):
        key, value = self._node_to_db_mapping(node)
        if value is not None:
            self._set_db_value(key, value)
        return key

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
            with self._prune_node(sub_node):
                new_subnode_key = encode_nibbles(tuple(itertools.chain(
                    [sub_node_idx],
                    decode_nibbles(sub_node[0]),
                )))
                return [new_subnode_key, sub_node[1]]
        elif sub_node_type == NODE_TYPE_BRANCH:
            return [encode_nibbles([sub_node_idx]), sub_node_hash]
        else:
            raise Exception("Invariant: this code block should be unreachable")

    #
    # Node Operations
    #
    def _delete_branch_node(self, node, trie_key):
        """
        Delete a key from inside or underneath a branch node
        """
        if not trie_key:
            node[-1] = BLANK_NODE
            return self._normalize_branch_node(node)

        node_to_delete = self.get_node(node[trie_key[0]])

        sub_node = self._delete(node_to_delete, trie_key[1:])
        encoded_sub_node = self._persist_node(sub_node)

        if encoded_sub_node == node[trie_key[0]]:
            # If no change, (value already empty), short-circuit and skip any other work.
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
            with self._prune_node(new_sub_node):
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
                new_node = self._set(sub_node, trie_key_remainder, value)
        elif not current_key_remainder:
            if is_extension:
                sub_node = self.get_node(node[1])
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

    #
    # Context APIs
    #
    @contextlib.contextmanager
    def squash_changes(self):
        scratch_db = ScratchDB(self.db)
        with scratch_db.batch_commit(do_deletes=self.is_pruning):
            memory_trie = type(self)(scratch_db, self.root_hash, prune=True)
            yield memory_trie
        try:
            self.root_node = memory_trie.root_node
        except MissingTrieNode:
            # if the new root node is missing,
            #   (or no changes happened in a squash trie where the old root node was missing),
            #   then we shouldn't crash here
            self.root_hash = memory_trie.root_hash

    @contextlib.contextmanager
    def at_root(self, at_root_hash):
        if self.is_pruning:
            raise ValidationError("Cannot use trie snapshot while pruning")

        snapshot = type(self)(self.db, at_root_hash, prune=False)
        yield snapshot

    #
    # Differ
    #
    @classmethod
    def diff(cls, trie1, trie2):
        diffed = cls._diff_nodes(trie1, trie2, trie1.root_node, trie2.root_node)
        return {
            nibbles_to_bytes(nibbles): valdiff
            for nibbles, valdiff
            in diffed.items()
        }

    @classmethod
    def _diff_nodes(cls, trie1, trie2, node1, node2):
        if node1 == node2:
            return {}
        node1type = get_node_type(node1)
        node2type = get_node_type(node2)

        if node1type == NODE_TYPE_BRANCH:
            if node1[-1]:
                raise NotImplementedError
            elif node2type == NODE_TYPE_BLANK:
                return merge([
                    {
                        (branch_nibble, ) + keytail: val
                        for keytail, val
                        in cls._diff_nodes(trie1, trie2, trie1._get_subnode(subnode), node2).items()
                    }
                    for branch_nibble, subnode in enumerate(node1[:-1])
                ])
            elif node2type == NODE_TYPE_LEAF:
                key2 = extract_key(node2)
                leaf_nibble = key2[0]
                branch_subnode = trie1._get_subnode(node1[leaf_nibble])
                if len(key2) == 1:
                    if not is_leaf_node(branch_subnode):
                        raise NotImplementedError
                    elif branch_subnode[1] != node2[-1]:
                        diff_leaf = {key2: (branch_subnode[1] or None, node2[-1])}
                    else:
                        diff_leaf = {}
                else:
                    trimmed_leaf = [
                        compute_leaf_key(key2[1:]),
                        node2[1],
                    ]
                    diff_leaf = {
                        (leaf_nibble, ) + keytail: val
                        for keytail, val
                        in cls._diff_nodes(trie1, trie2, branch_subnode, trimmed_leaf).items()
                    }

                diff_blanks = [
                    {
                        (branch_nibble, ) + keytail: val
                        for keytail, val
                        in cls._diff_nodes(trie1, trie2, trie1._get_subnode(subnode), BLANK_NODE).items()
                    }
                    for branch_nibble, subnode in enumerate(node1[:-1])
                    if branch_nibble != leaf_nibble
                ]
                return merge(diff_leaf, *diff_blanks)
            elif node2type == NODE_TYPE_BRANCH:
                if node2[-1]:
                    raise NotImplementedError
                return merge([
                    {
                        (branch_nibble, ) + keytail: val
                        for keytail, val
                        in cls._diff_nodes(
                            trie1,
                            trie2,
                            trie1._get_subnode(subnode),
                            trie2._get_subnode(node2[branch_nibble])
                        ).items()
                    }
                    for branch_nibble, subnode in enumerate(node1[:-1])
                    if subnode != node2[branch_nibble]
                ])
            else:
                raise NotImplementedError

        elif node1type == NODE_TYPE_EXTENSION:
            key1 = extract_key(node1)
            subnode = trie1._get_subnode(node1[1])
            if node2type == NODE_TYPE_BLANK:
                return {
                    key1 + keytail: val
                    for keytail, val
                    in cls._diff_nodes(trie1, trie2, subnode, node2)
                }
            elif node2type == NODE_TYPE_LEAF:
                key2 = extract_key(node2)
                common_prefix, key1_remainder, key2_remainder = consume_common_prefix(
                    key1,
                    key2,
                )
                if not common_prefix:
                    return merge(
                        cls._diff_nodes(trie1, trie2, node1, BLANK_NODE),
                        cls._diff_nodes(trie1, trie2, BLANK_NODE, node2),
                    )
                elif not key1_remainder and key2_remainder:
                    trimmed_leaf = [
                        compute_leaf_key(key2_remainder),
                        node2[1],
                    ]
                    return {
                        common_prefix + keytail: val
                        for keytail, val
                        in cls._diff_nodes(trie1, trie2, subnode, trimmed_leaf).items()
                    }
                else:
                    raise NotImplementedError

            else:
                raise NotImplementedError

        elif is_leaf_node(node1):
            key1 = extract_key(node1)
            if is_blank_node(node2):
                return {key1: (node1[1], None)}
            elif is_leaf_node(node2):
                diff = {}
                key2 = extract_key(node2)
                if key2 == key1:
                    diff[key1] = (node1[1], node2[1])
                else:
                    diff[key1] = (node1[1], None)
                    diff[key2] = (None, node2[1])
                return diff
            elif node2type in (NODE_TYPE_EXTENSION, NODE_TYPE_BRANCH):
                return cls._flip_diff(trie1, trie2, node1, node2)
            else:
                raise NotImplementedError
        elif is_blank_node(node1):
            if is_leaf_node(node2):
                return cls._flip_diff(trie1, trie2, node1, node2)
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError
        raise NotImplementedError

    def _get_subnode(self, subnode_ref):
        if len(subnode_ref) == 32:
            return self.get_node(subnode_ref)
        else:
            return subnode_ref

    @classmethod
    def _flip_diff(cls, t1, t2, h1, h2):
        return {k: (diff1, diff2) for k, (diff2, diff1) in cls._diff_nodes(t2, t1, h2, h1).items()}



@to_tuple
def tuplify(node):
    for sub in node:
        if isinstance(sub, list):
            yield tuplify(sub)
        else:
            yield sub


@to_list
def listify(node):
    for sub in node:
        if isinstance(sub, tuple):
            yield listify(sub)
        else:
            yield sub
