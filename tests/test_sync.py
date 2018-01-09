import logging

from hypothesis import (
    given,
    settings,
    strategies,
)

from trie import HexaryTrie
from trie.sync import HexaryTrieSync


logger = logging.getLogger()

def make_random_trie(random):
    trie = HexaryTrie({})
    contents = {}
    for _ in range(1000):
        key_length = random.randint(2, 32)
        key = bytes([random.randint(0,255) for _ in range(key_length)])
        value_length = random.randint(2, 64)
        value = bytes([random.randint(0,255) for _ in range(value_length)])
        trie[key] = value
        contents[key] = value
    return trie, contents


@given(random=strategies.randoms())
@settings(max_examples=10)
def test_trie_sync(random):
    src_trie, contents = make_random_trie(random)

    dest_db = {}
    scheduler = HexaryTrieSync(src_trie.root_hash, dest_db, logger)
    requests = scheduler.next_batch()
    while len(requests) > 0:
        results = []
        for request in requests:
            results.append([request.node_key, src_trie.db[request.node_key]])
        scheduler.process(results)
        requests = scheduler.next_batch(10)
    dest_trie = HexaryTrie(dest_db, src_trie.root_hash)
    for key, value in contents.items():
        assert dest_trie[key] == value
