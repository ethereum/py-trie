from trie import HexaryTrie


def trie_from_keys(keys, prune=False):
    """
    Make a new HexaryTrie, insert all the given keys, with the value equal to the key.
    Return the raw database and the HexaryTrie.
    """
    # Create trie
    node_db = {}
    trie = HexaryTrie(node_db, prune=prune)
    with trie.squash_changes() as trie_batch:
        for k in keys:
            trie_batch[k] = k

    return node_db, trie
