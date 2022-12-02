import cProfile
import itertools
import pstats
import random
import time

from trie import (
    HexaryTrie,
)


def mk_random_bytes(n):
    return bytes(bytearray([random.randint(0, 255) for _ in range(n)]))


TEST_DATA = {
    mk_random_bytes(i): mk_random_bytes(j)
    for _ in range(128)
    for i, j in itertools.product(range(1, 33, 4), range(1, 130, 8))
}


def _insert_test():
    trie = HexaryTrie(db={})
    for k, v in sorted(TEST_DATA.items()):
        trie[k] = v
    return trie


def _insert_squash_test():
    trie = HexaryTrie(db={})
    with trie.squash_changes() as memory_trie:
        for k, v in sorted(TEST_DATA.items()):
            memory_trie[k] = v
    return trie


def main(profile=True):
    print("testing %s values" % len(TEST_DATA))
    tests = [
        ("insert", _insert_test),
        ("insert squash", _insert_squash_test),
    ]
    for name, func in tests:
        profiler = cProfile.Profile()
        if profile:
            profiler.enable()

        st = time.time()
        trie = func()
        elapsed = time.time() - st
        print("time to %s %d - %.2f" % (name, len(TEST_DATA), elapsed))

        if profile:
            print("==== Profiling stats for %s test =========" % name)
            profiler.disable()
            stats = pstats.Stats(profiler)
            stats.strip_dirs().sort_stats("cumulative").print_stats(30)
            print("==========================================")

        st = time.time()
        for k in sorted(TEST_DATA.keys()):
            trie[k]
        elapsed = time.time() - st
        print("time to read %d - %.2f" % (len(TEST_DATA), elapsed))


if __name__ == "__main__":
    main()
