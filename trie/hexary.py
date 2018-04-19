from collections.abc import Mapping
import itertools

from rlp.codec import encode_raw

from cytoolz import merge
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
assert BLANK_NODE_HASH == keccak(encode_raw(b''))
assert BLANK_HASH == keccak(b'')

DELETED = object()


class ScratchDB(Mapping):
    __slots__ = '_read_db', '_write_db'

    def __init__(self, read_db):
        self._read_db = read_db
        self._write_db = {}

    def __setitem__(self, key, value):
        self._write_db[key] = value

    def __delitem__(self, key):
        if key in self._write_db:
            self._write_db[key] = DELETED
        elif key in self._read_db:
            raise NotImplementedError("scratch db can't keep track of deletes in read-only db yet")
        else:
            raise KeyError("key not found")

    def __getitem__(self, key):
        if key in self._write_db:
            return self._write_db[key]
        else:
            return self._read_db[key]

    def __contains__(self, key):
        if key in self._write_db and self._write_db[key] is not DELETED:
            return True
        else:
            return key in self._read_db

    def __iter__(self):
        return itertools.chain(self._write_db, self._read_db)

    def __len__(self):
        return len(self._read_db) + len(self._write_db)

    @property
    def changes(self):
        return dict(self._write_db)


class TrieDelta:
    __slots__ = '_new_root_hash', '_updates'

    def __init__(self, new_root_hash, updates=None):
        '''
        :param dict updates: new key->value mappings, deletions with key->DELETED
        '''
        if updates is None:
            self._updates = {}
        else:
            self._updates = dict(updates)
        self._new_root_hash = new_root_hash

    @property
    def root_hash(self):
        return self._new_root_hash

    @property
    def changes(self):
        '''
        :return: new key->value mappings, deletions with key->DELETED
        :rtype: dict
        '''
        return dict(self._updates)

    def __iter__(self):
        return iter(self._updates)

    @classmethod
    def join(cls, deltas, starting_root=None):
        if deltas is None:
            raise TypeError('must provide an iterable of deltas to join')
        else:
            joint_changes = {}
            root_hash = starting_root
            for delta in deltas:
                joint_changes.update(delta._updates)
                root_hash = delta.root_hash
            if root_hash is None:
                raise ValueError(
                    'You must either supply a non-empty list of changes, '
                    'or provide a starting root hash.'
                )
            return cls(root_hash, joint_changes)

    def apply(self, db):
        for key, value in self._updates.items():
            if value is DELETED:
                del db[key]
            else:
                db[key] = value


class FrozenHexaryTrie:
    __slots__ = '_read_db', '_root_hash', '_scratch_db'

    # Shortcuts
    BLANK_ROOT_HASH = BLANK_NODE_HASH
    BLANK_NODE = BLANK_NODE
    Delta = TrieDelta

    def __init__(self, db, root_hash=BLANK_NODE_HASH):
        self._read_db = db
        validate_is_bytes(root_hash)
        self._root_hash = root_hash
        # initialize this before every write op, and reset it after
        self._scratch_db = None

    @property
    def root_hash(self):
        return self._root_hash

    def get(self, key):
        validate_is_bytes(key)

        trie_key = bytes_to_nibbles(key)
        root_node = self.get_node(self.root_hash)

        return self._get(root_node, trie_key, self._read_db)

    def _get(self, node, trie_key, db):
        node_type = get_node_type(node)

        if node_type == NODE_TYPE_BLANK:
            return BLANK_NODE
        elif node_type in {NODE_TYPE_LEAF, NODE_TYPE_EXTENSION}:
            return self._get_kv_node(node, trie_key, db)
        elif node_type == NODE_TYPE_BRANCH:
            return self._get_branch_node(node, trie_key, db)
        else:
            raise Exception("Invariant: This shouldn't ever happen")

    def after(self, trie_delta):
        '''
        Note that this method does *not* commit any trie_delta changes
        to the database.
        '''
        return (type(self))(db=self._read_db, root_hash=trie_delta.root_hash)

    def set(self, key, value):
        return self._store_key(key, value)

    def _store_key(self, key, value):
        validate_is_bytes(key)
        validate_is_bytes(value)
        self._scratch_db = ScratchDB(self._read_db)

        trie_key = bytes_to_nibbles(key)
        root_node = self._get_node(self.root_hash, self._scratch_db)

        new_node = self._set(root_node, trie_key, value)
        root_delta = self._set_root_node(new_node)
        return self._scratch_delta(root_delta)

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
        return self._remove_key(key)

    def _remove_key(self, key):
        validate_is_bytes(key)
        self._scratch_db = ScratchDB(self._read_db)

        trie_key = bytes_to_nibbles(key)
        root_node = self._get_node(self.root_hash, self._scratch_db)

        new_node = self._delete(root_node, trie_key)
        root_delta = self._set_root_node(new_node)
        return self._scratch_delta(root_delta)

    def _scratch_delta(self, root_delta):
        db_changes = merge(self._scratch_db.changes, root_delta.changes)
        self._scratch_db = None
        return TrieDelta(root_delta.root_hash, db_changes)

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
        db = {}
        trie = cls(db, root_hash=root_hash)

        # We know the database is empty at the beginning, and we aren't returning the trie,
        # so we can read and write to same db.
        trie._scratch_db = db

        for node in proof:
            trie._persist_node(node)
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

    #
    # Utils
    #
    def _set_root_node(self, root_node):
        validate_is_node(root_node)
        encoded_root_node = encode_raw(root_node)
        new_root_hash = keccak(encoded_root_node)
        return TrieDelta(new_root_hash, {new_root_hash: encoded_root_node})

    def get_node(self, node_hash):
        return self._get_node(node_hash, self._read_db)

    def _get_node(self, node_hash, db):
        if node_hash == BLANK_NODE:
            return BLANK_NODE
        elif node_hash == BLANK_NODE_HASH:
            return BLANK_NODE

        if len(node_hash) < 32:
            encoded_node = node_hash
        else:
            encoded_node = db[node_hash]
        node = decode_node(encoded_node)

        return node

    def _persist_node(self, node):
        validate_is_node(node)
        if is_blank_node(node):
            return BLANK_NODE
        encoded_node = encode_raw(node)
        if len(encoded_node) < 32:
            return node

        encoded_node_hash = keccak(encoded_node)
        self._scratch_db[encoded_node_hash] = encoded_node
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
        sub_node = self._get_node(sub_node_hash, self._scratch_db)
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

        node_to_delete = self._get_node(node[trie_key[0]], self._scratch_db)

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
        sub_node = self._get_node(node[1], self._scratch_db)

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
            sub_node = self._get_node(node[trie_key[0]], self._scratch_db)

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
                sub_node = self._get_node(node[1], self._scratch_db)
                # TODO: this needs to cleanup old storage.
                new_node = self._set(sub_node, trie_key_remainder, value)
        elif not current_key_remainder:
            if is_extension:
                sub_node = self._get_node(node[1], self._scratch_db)
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

    def _get_branch_node(self, node, trie_key, db):
        if not trie_key:
            return node[16]
        else:
            sub_node = self._get_node(node[trie_key[0]], db)
            return self._get(sub_node, trie_key[1:], db)

    def _get_kv_node(self, node, trie_key, db):
        current_key = extract_key(node)
        node_type = get_node_type(node)

        if node_type == NODE_TYPE_LEAF:
            if trie_key == current_key:
                return node[1]
            else:
                return BLANK_NODE
        elif node_type == NODE_TYPE_EXTENSION:
            if key_starts_with(trie_key, current_key):
                sub_node = self._get_node(node[1], db)
                return self._get(sub_node, trie_key[len(current_key):], db)
            else:
                return BLANK_NODE
        else:
            raise Exception("Invariant: unreachable code path")

    #
    # Dictionary API
    #
    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        return self.exists(key)


class HexaryTrie(FrozenHexaryTrie):
    @FrozenHexaryTrie.root_hash.setter
    def root_hash(self, value):
        self._root_hash = value

    @FrozenHexaryTrie.root_node.setter
    def root_node(self, value):
        delta = self._set_root_node(value)
        delta.apply(self._read_db)
        self._root_hash = delta.root_hash

    def set(self, key, value):
        delta = super().set(key, value)
        delta.apply(self._read_db)
        self.root_hash = delta.root_hash
        return delta

    def delete(self, key):
        delta = super().delete(key)
        delta.apply(self._read_db)
        self.root_hash = delta.root_hash
        return delta

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        return self.delete(key)


assert FrozenHexaryTrie.BLANK_ROOT_HASH == BLANK_NODE_HASH
assert HexaryTrie.BLANK_ROOT_HASH == BLANK_NODE_HASH
