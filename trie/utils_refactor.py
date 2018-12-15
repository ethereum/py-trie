def get_common_prefix(current_key, trie_key):
    """
    This function finds the common prefix(tuple of nibbles) among
    current_key and trie_key, which are both in nibbles format.
    """
    if not current_key or not trie_key:
        raise Exception("Can't find prefix between empty or undefined objects")

    i = 0
    while i < len(current_key) and i < len(trie_key) and (current_key[i] == trie_key[i]):
        i += 1

    return current_key[:i], current_key[i:], trie_key[i:]
