from trie.constants import (
    NODE_TYPE_BRANCH,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_LEAF,
)
from trie.utils_refactor import (
    get_common_prefix,
)


# NOTE: HERE ALL THE KEYS ARE NIBBLES(ints b/w 0 and 15) AND NOT STRINGS


class BranchNode:
    node_type = NODE_TYPE_BRANCH
    # Keys are ints from 0 to 15, values are the child nodes
    child_nodes = {}
    value = None

    def __init__(self, child_nodes, value):
        if not all(isinstance(key, int) for key in child_nodes):
            raise Exception("Keys in child hashes dict have to be ints")
        if not all(0 <= key <= 15 for key in child_nodes):
            raise Exception("Keys in child hashes dict have to be b/w 0 to 15")
        self.child_nodes = child_nodes
        self.value = value

    def insert_child(self, key, value):
        # Key is consumed and hence value should be stored here
        if len(key) == 0:
            self.value = value
            return self

        if key[0] not in self.child_nodes or self.child_nodes[key[0]] is None:
            # No child node yet with the first nibble of the key
            self.child_nodes[key[0]] = LeafNode(key[1:], value)
        else:
            # Already exists a child node with the first nibble of the key
            self.child_nodes[key[0]] = self.child_nodes[key[0]].insert_child(key[1:], value)

        return self

    def get_value(self, key):
        if len(key) == 0:
            return self.value

        if key[0] not in self.child_nodes or self.child_nodes[key[0]] is None:
            raise Exception("Key not found in trie")

        return self.child_nodes[key[0]].get_value(key[1:])

    def delete_value(self, key):
        if not key:
            self.value = None
        else:
            if key[0] not in self.child_nodes:
                raise Exception("Key not found in trie")
            self.child_nodes[key[0]] = self.child_nodes[key[0]].delete_value(key[1:])

        # If this points to no children nodes, and it stores no value, then delete it
        if self.value is None and all(self.child_nodes[key] is None for key in self.child_nodes):
            return None

        # Convert this to LeafNode
        elif (
            self.value is not None
            and
            all(self.child_nodes[key] is None for key in self.child_nodes)
        ):
            return LeafNode((), self.value)

        else:
            return self


class ExtensionNode:
    node_type = NODE_TYPE_EXTENSION
    trie_key = None
    child_node = None

    def __init__(self, trie_key, child_node):
        self.trie_key = trie_key
        self.child_node = child_node

    def insert_child(self, key, value):
        common_prefix, current_key_remainder, trie_key_remainder = get_common_prefix(
            key,
            self.trie_key
        )

        # No common prefix key found.
        # Hence create a branchnode with children as the current extension node
        # and the new node that would be created for the new key, value pair
        if not common_prefix:
            branch_node = BranchNode({}, None)
            # Removing the first nibble in the key of the extension node
            # so as to connect it to the newly created branch node
            trie_key_first_nibble = self.trie_key[0]
            self.trie_key = self.trie_key[1:]

            if not self.trie_key:
                # There is no point in storing the extension_node, if the extension
                # key is empty. Hence we directly store it's child node
                branch_node.child_nodes[trie_key_first_nibble] = self.child_node
                del(self)
            else:
                branch_node.child_nodes[trie_key_first_nibble] = self

            # Insert the current key, value pair in branch_node
            branch_node.insert_child(key, value)

            return branch_node

        else:
            # Key obtained after removing the trie_key prefix
            current_key_remainder = key[len(self.trie_key):]
            self.child_node = self.child_node.insert_child(current_key_remainder, value)

            return self

    def get_value(self, key):
        # Make sure that the key starts with the extension node's key
        if key[:len(self.trie_key)] != self.trie_key:
            print(key)
            print(self.trie_key)
            raise Exception("Key not found in trie")

        # Key obtained after removing the trie_key prefix
        current_key_remainder = key[len(self.trie_key):]

        return self.child_node.get_value(current_key_remainder)

    def delete_value(self, key):
        # Make sure that the key starts with the extension node's key
        if key[:len(self.trie_key)] != self.trie_key:
            print(key)
            print(self.trie_key)
            raise Exception("Key not found in trie")

        self.child_node = self.child_node.delete_value(key[len(self.trie_key):])
        if self.child_node is None:
            # This node is useless now (no info in it) and can be deleted
            return None

        return self


class LeafNode:
    node_type = NODE_TYPE_LEAF
    trie_key = None
    value = None

    def __init__(self, trie_key, value):
        self.trie_key = trie_key
        self.value = value

    def insert_child(self, key, value):
        common_prefix, current_key_remainder, trie_key_remainder = get_common_prefix(
            key,
            self.trie_key
        )

        # Below condition indicates that for the same key
        # we are trying to insert a different value
        if len(current_key_remainder) == 0:
            self.value = value
            return self

        # Create a branch node to create branches to this new child and the old leaf node
        branch_node = BranchNode({}, None)
        branch_node.insert_child(current_key_remainder, value)
        branch_node.insert_child(trie_key_remainder, self.value)

        if common_prefix:
            # Replace this node with Extension Node which stores the branch node object
            replacement_node = ExtensionNode(common_prefix, branch_node)
        else:
            # No common prefix, and hence we don't need Extension Node
            replacement_node = branch_node

        return replacement_node

    def get_value(self, key):
        if key != self.trie_key:
            raise Exception("Key not found in trie")

        return self.value

    def delete_value(self, key):
        if key != self.trie_key:
            raise Exception("Key not found in trie")

        # Since the object is deleted, return None
        return None
