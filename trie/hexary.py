from trie.BaseNode import (
    LeafNode,
)

from trie.utils.nibbles import (
    bytes_to_nibbles,
)

from trie.validation import (
    validate_is_bytes,
)


class HexaryTrie:
    rootNode = None

    def insert(self, key, value):
        validate_is_bytes(key)
        validate_is_bytes(value)

        key_nibbles = bytes_to_nibbles(key)

        if self.rootNode is None:
            self.rootNode = LeafNode(key_nibbles, value)
        else:
            self.rootNode = self.rootNode.insert_child(key_nibbles, value)

    def get(self, key):
        validate_is_bytes(key)
        key_nibbles = bytes_to_nibbles(key)

        if self.rootNode is None:
            raise Exception("Key not found in trie")

        return self.rootNode.get_value(key_nibbles)

    def delete(self, key):
        validate_is_bytes(key)
        key_nibbles = bytes_to_nibbles(key)

        if self.rootNode is None:
            raise Exception("Key not found in trie")

        self.rootNode = self.rootNode.delete(key_nibbles)
