from typing import (
    Iterable,
    Optional,
)

from trie.exceptions import (
    PerfectVisibility,
)
from trie.fog import (
    HexaryTrieFog,
    TrieFrontierCache,
)
from trie.hexary import (
    HexaryTrie,
)
from trie.typing import (
    HexaryTrieNode,
    Nibbles,
)
from trie.utils.nibbles import (
    bytes_to_nibbles,
    nibbles_to_bytes,
)
from trie.utils.nodes import (
    consume_common_prefix,
)


class NodeIterator:
    """Iterate over all nodes of a trie, ensuring its consistency."""

    def __init__(self, trie: HexaryTrie) -> None:
        self._trie = trie

    def next(self, key_bytes: bytes) -> Optional[bytes]:
        """
        Find the next key to the right from the given key, or None if there is
        no key to the right.

        .. NOTE:: If you plan to iterate the full trie, use all() instead, for performance.

        :return: key in bytes to the right of key_bytes, or None
        """
        root = self._trie.root_node
        key = bytes_to_nibbles(key_bytes)
        none_traversed = Nibbles(())
        next_key = self._get_key_after(root, key, none_traversed)
        if next_key is None:
            return None
        else:
            return nibbles_to_bytes(next_key)

    def _get_key_after(
            self,
            node: HexaryTrieNode,
            key: Nibbles,
            traversed: Nibbles) -> Optional[Nibbles]:
        """
        Find the next key in the trie after key

        :param node: the source node to search for the next key after `key`
        :param key: the starting key used to seek the nearest key on the right
        :param traversed: the nibbles already traversed to get down to `node`

        :return: the complete key that is immediately to the right of `key` or None,
            if no key is immediately to the right (under `node`)
        """
        for next_segment in node.sub_segments:
            if key[:len(next_segment)] > next_segment:
                # This segment is to the left of the key, keep looking...
                continue
            else:
                # Either: found the exact match, or the next result to the right
                # Either way, we'll want to take a look
                next_node = self._trie.traverse_from(node, next_segment)

                common, key_remaining, segment_remaining = consume_common_prefix(key, next_segment)
                if len(segment_remaining) == 0:
                    # Found a perfect match! Keep looking for keys to the right of the target
                    next_key = self._get_key_after(
                        next_node,
                        key_remaining,
                        traversed + next_segment,
                    )
                    if next_key is None:
                        # Could not find a key to the right in any sub-node.
                        # In other words, *only* the target key is in this sub-trie
                        # So keep looking to the right...
                        continue
                    else:
                        # We successfully found a key to the right in a subtree, return it up
                        return next_key
                else:
                    # Found no exact match, and are now looking for the next possible key
                    return self._get_next_key(next_node, traversed + next_segment)

        if node.suffix > key:
            # This leaf node is to the right of the target key
            return traversed + node.suffix
        else:
            # Nothing found in any sub-segments
            return None

    def _get_next_key(self, node: HexaryTrieNode, traversed: Nibbles) -> Optional[Nibbles]:
        """
        Find the next possible key within the given node

        :param node: the parent node to search (plus all of its children)
        :param traversed: the key used to traverse down to `node`

        :return: the complete key that is the furthest left within `node`
        """
        if node.value:
            # This is either a leaf node, or a branch node with a value.
            # The value in a branch node comes before all the child values
            return traversed + node.suffix
        elif len(node.sub_segments) == 0:
            # Only leaves should have 0 sub-segments, and should have a value.
            # There shouldn't be any way to navigate to a blank node, as long as
            # the trie hasn't changed during iteration. If it has... I guess return None here.
            return None
        else:
            # This is a branch node with no value, or an extension node.
            # Either way, take the left-most child and repeat the search within it
            next_segment = node.sub_segments[0]
            next_node = self._trie.traverse_from(node, next_segment)
            return self._get_next_key(next_node, traversed + next_segment)

    def all(self) -> Iterable[bytes]:
        """
        Iterate over all values from left to right. Some performance benefit over
        using :meth:`next` repeatedly, by caching node accesses between yielded values.
        """
        next_fog = HexaryTrieFog()
        cache = TrieFrontierCache()

        while True:
            try:
                # Always get the furthest left unexplored value
                nearest_prefix = next_fog.nearest_right(())
            except PerfectVisibility:
                # No more unexplored nodes
                return

            try:
                cached_node, uncached_key = cache.get(nearest_prefix)
            except KeyError:
                node = self._trie.traverse(nearest_prefix)
            else:
                node = self._trie.traverse_from(cached_node, uncached_key)

            next_fog = next_fog.explore(nearest_prefix, node.sub_segments)

            if node.sub_segments:
                cache.add(nearest_prefix, node, node.sub_segments)
            else:
                cache.delete(nearest_prefix)

            if node.value:
                full_key = nearest_prefix + node.suffix
                yield nibbles_to_bytes(full_key)
