import logging

from hypothesis import (
    given,
    settings,
    strategies,
)

from trie import HexaryTrie
from trie.sync import HexaryTrieSync
from .utils import make_random_trie


logger = logging.getLogger()


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
            results.append([request.node_key, src_trie._read_db[request.node_key]])
        scheduler.process(results)
        requests = scheduler.next_batch(10)
    dest_trie = HexaryTrie(dest_db, src_trie.root_hash)
    for key, value in contents.items():
        assert dest_trie[key] == value
