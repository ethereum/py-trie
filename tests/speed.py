import time
import random

import itertools

from trie import HexaryTrie


def mk_random_bytes(n):
    return bytes(bytearray([random.randint(0, 255) for _ in range(n)]))


TEST_DATA = {
    mk_random_bytes(i): mk_random_bytes(j)
    for _ in range(128)
    for i, j in itertools.product(range(1, 33, 4), range(1, 130, 8))
}


def main():
    print('testing %s values' % len(TEST_DATA))
    trie = HexaryTrie(db={})

    st = time.time()
    for k, v in sorted(TEST_DATA.items()):
        trie[k] = v
    elapsed = time.time() - st
    print('time to insert %d - %.2f' % (len(TEST_DATA), elapsed))

    st = time.time()
    for k in sorted(TEST_DATA.keys()):
        v = trie[k]
    elapsed = time.time() - st
    print('time to read %d - %.2f' % (len(TEST_DATA), elapsed))


if __name__ == '__main__':
    main()
