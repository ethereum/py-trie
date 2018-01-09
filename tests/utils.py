from trie import HexaryTrie


def make_random_trie(random):
    trie = HexaryTrie({})
    contents = {}
    for _ in range(1000):
        key_length = random.randint(2, 32)
        key = bytes([random.randint(0, 255) for _ in range(key_length)])
        value_length = random.randint(2, 64)
        value = bytes([random.randint(0, 255) for _ in range(value_length)])
        trie[key] = value
        contents[key] = value
    return trie, contents
