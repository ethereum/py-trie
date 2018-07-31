import asyncio
import logging

from hypothesis import (
    given,
    settings,
    strategies,
    example,
)
from hypothesis.types import RandomWithSeed

from trie import HexaryTrie
from trie.sync import HexaryTrieSync
from .utils import make_random_trie


logger = logging.getLogger()


# produces a branch node with an extention node who's encoding is less than 32
# bytes in length so it is inlined.
EXAMPLE_37968 = 37968

# produces an top level extension node who's encoding is less than 32 bytes in
# length so it gets inlined.
EXAMPLE_809368 = 809368


class AsyncDB(dict):

    async def coro_exists(self, key):
        return key in self

    async def coro_set(self, key, val):
        self[key] = val


@given(random=strategies.randoms())
@settings(max_examples=50)
@example(random=RandomWithSeed(EXAMPLE_37968))
@example(random=RandomWithSeed(EXAMPLE_809368))
def test_trie_sync(random):

    # Apparently hypothesis tests cannot be used in conjunction with pytest-asyncio yet, so do it
    # like this for now. https://github.com/HypothesisWorks/hypothesis/pull/1343
    async def _test_trie_sync():
        src_trie, contents = make_random_trie(random)
        dest_db = AsyncDB()
        scheduler = HexaryTrieSync(src_trie.root_hash, dest_db, logger)
        requests = scheduler.next_batch()
        while len(requests) > 0:
            results = []
            for request in requests:
                results.append([request.node_key, src_trie.db[request.node_key]])
            await scheduler.process(results)
            requests = scheduler.next_batch(10)
        dest_trie = HexaryTrie(dest_db, src_trie.root_hash)
        for key, value in contents.items():
            assert dest_trie[key] == value

    asyncio.get_event_loop().run_until_complete(_test_trie_sync())
