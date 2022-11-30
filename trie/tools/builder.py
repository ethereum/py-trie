from trie import HexaryTrie


def trie_from_keys(keys, minimum_value_length=0, prune=False):
    """
    Make a new HexaryTrie, insert all the given keys, with the value equal to the key.
    Return the raw database and the HexaryTrie.
    """
    # Create trie
    node_db = {}
    trie = HexaryTrie(node_db, prune=prune)
    with trie.squash_changes() as trie_batch:
        for k in keys:
            # Flood 3's at the end of the value to make it longer. b'3' is encoded to 0x33,
            #   so the bytes and HexBytes representation look the same. Just a convenience.
            trie_batch[k] = k.ljust(minimum_value_length, b"3")

    return node_db, trie
