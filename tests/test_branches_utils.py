import pytest

from trie.trie import (
    BinaryTrie,
)
from trie.exceptions import (
    InvalidKeyError,
)

from trie.branches import (
    check_if_branch_exist,
    get_branch,
    if_branch_valid,
    get_trie_nodes,
    get_witness,
)

@pytest.fixture
def test_trie():
    trie = BinaryTrie(db={})
    trie.set(b'\x12\x34\x56\x78\x9a', b'9a')
    trie.set(b'\x12\x34\x56\x78\x9b', b'9b')
    trie.set(b'\x12\x34\x56\xff', b'ff')

    return trie


@pytest.mark.parametrize(
    'key_prefix,if_exist',
    (
        (b'\x12\x34', True),
        (b'\x12\x34\x56\x78\x9b', True),
        (b'\x12\x56', False),
        (b'\x12\x34\x56\xff\xff', False),
        (b'\x12\x34\x56', True),
        (b'\x12\x34\x56\x78', True),
    ),
)
def test_branch_exist(test_trie, key_prefix, if_exist):
    assert check_if_branch_exist(test_trie.db, test_trie.root_hash, key_prefix) == if_exist


@pytest.mark.parametrize(
    'key,key_valid',
    (
        (b'\x12\x34', True),
        (b'\x12\x34\x56\xff', True),
        (b'\x12\x34\x56\x78\x9b', True),
        (b'\x12\x56', True),
        (b'\x12\x34\x56\xff\xff', False),
        (b'', False),
    ),
)
def test_branch(test_trie, key, key_valid):
    if key_valid:
        branch = get_branch(test_trie.db, test_trie.root_hash, key)
        assert if_branch_valid(branch, test_trie.root_hash, key, test_trie.get(key))
    else:
        with pytest.raises(InvalidKeyError):
            get_branch(test_trie.db, test_trie.root_hash, key)


@pytest.mark.parametrize(
    'root,nodes',
    (
        (b'#\xf037,w\xb9()\x0e4\x92\xdf\x11\xca\xea\xa5\x13/\x10\x1bJ\xa7\x16\x07\x07G\xb1\x01_\x16\xca', [b'\x029a']),  # noqa: E501 
        (
            b'\x84\x97\xc1\xf7S\xf5\xa2\xbb>\xbd\xe9\xc3t\x0f\xac/\xad\xa8\x01\xff\x9aE\t\xc1\xab\x9e\xa3|\xc7Z\xb0v',  # noqa: E501 
            [
                b'\x01#\xf037,w\xb9()\x0e4\x92\xdf\x11\xca\xea\xa5\x13/\x10\x1bJ\xa7\x16\x07\x07G\xb1\x01_\x16\xcaG\xe9\xb6\xa1\xfa\xd5\x82\xf4k\x04\x9c\x8e\xc8\x17\xb4G\xe1c*n\xf4o\x02\x85\xf1\x19\xa8\x83`\xfb\xf8\xa2',  # noqa: E501 
                b'\x029a',
                b'\x029b',
            ]
        ),
        (
            b'\x13\x07<\xa0w6\xd5O\x91\x93\xb1\xde,0}\xe7\xee\x82\xd7\xf6\xce\x1b^\xb7}"\n\xe4&\xe2\xd7v',  # noqa: E501 
            [
                b'\x00\x82<M\x84\x97\xc1\xf7S\xf5\xa2\xbb>\xbd\xe9\xc3t\x0f\xac/\xad\xa8\x01\xff\x9aE\t\xc1\xab\x9e\xa3|\xc7Z\xb0v',  # noqa: E501 
                b'\x01#\xf037,w\xb9()\x0e4\x92\xdf\x11\xca\xea\xa5\x13/\x10\x1bJ\xa7\x16\x07\x07G\xb1\x01_\x16\xcaG\xe9\xb6\xa1\xfa\xd5\x82\xf4k\x04\x9c\x8e\xc8\x17\xb4G\xe1c*n\xf4o\x02\x85\xf1\x19\xa8\x83`\xfb\xf8\xa2',  # noqa: E501 
                b'\x029a',
                b'\x029b',
            ]
        ),
        (
            b'X\x99\x8f\x13\xeb\x9bF\x08\xec|\x8b\xd8}\xca\xed\xda\xbb4\tl\xc8\x9bJ;J\xed\x11\x86\xc2\xd7+\xca',  # noqa: E501 
            [
                b'\x00\x80\x124V\xde\xb5\x8f\xdb\x98\xc0\xe8\xed\x10\xde\x84\x89\xe1\xc3\x90\xbeoi7y$sJ\x07\xa1h\xf5t\x1c\xac\r+',  # noqa: E501 
                b'\x01\x13\x07<\xa0w6\xd5O\x91\x93\xb1\xde,0}\xe7\xee\x82\xd7\xf6\xce\x1b^\xb7}"\n\xe4&\xe2\xd7v7\x94\x07\x18\xc9\x96E\xf1\x9bS1sv\xa2\x8b\x9a\x88\xfd/>5\xcb3\x9e\x03\x08\r\xe2\xe1\xd5\xaaq',  # noqa: E501 
                b'\x00\x82<M\x84\x97\xc1\xf7S\xf5\xa2\xbb>\xbd\xe9\xc3t\x0f\xac/\xad\xa8\x01\xff\x9aE\t\xc1\xab\x9e\xa3|\xc7Z\xb0v',  # noqa: E501 
                b'\x00\x83\x7fR\xce\xe1\xe1 +\x96\xde\xae\xcdV\x13\x9a \x90.7H\xb6\x80\t\x10\xe1(\x03\x15\xde\x94\x17X\xee\xe1',  # noqa: E501 
                b'\x01#\xf037,w\xb9()\x0e4\x92\xdf\x11\xca\xea\xa5\x13/\x10\x1bJ\xa7\x16\x07\x07G\xb1\x01_\x16\xcaG\xe9\xb6\xa1\xfa\xd5\x82\xf4k\x04\x9c\x8e\xc8\x17\xb4G\xe1c*n\xf4o\x02\x85\xf1\x19\xa8\x83`\xfb\xf8\xa2',  # noqa: E501 
                b'\x02ff',
                b'\x029a',
                b'\x029b',
            ]
        ),
        (b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p", []),
        (32 * b'\x00', []),
    ),
)
def test_get_trie_nodes(test_trie, root, nodes):
    assert set(nodes) == set(get_trie_nodes(test_trie.db, root))


@pytest.mark.parametrize(
    'key,nodes',
    (
        (
            b'\x12\x34\x56\x78\x9b',
            [
                b'\x00\x80\x124V\xde\xb5\x8f\xdb\x98\xc0\xe8\xed\x10\xde\x84\x89\xe1\xc3\x90\xbeoi7y$sJ\x07\xa1h\xf5t\x1c\xac\r+',  # noqa: E501 
                b'\x01\x13\x07<\xa0w6\xd5O\x91\x93\xb1\xde,0}\xe7\xee\x82\xd7\xf6\xce\x1b^\xb7}"\n\xe4&\xe2\xd7v7\x94\x07\x18\xc9\x96E\xf1\x9bS1sv\xa2\x8b\x9a\x88\xfd/>5\xcb3\x9e\x03\x08\r\xe2\xe1\xd5\xaaq',  # noqa: E501 
                b'\x00\x82<M\x84\x97\xc1\xf7S\xf5\xa2\xbb>\xbd\xe9\xc3t\x0f\xac/\xad\xa8\x01\xff\x9aE\t\xc1\xab\x9e\xa3|\xc7Z\xb0v',  # noqa: E501 
                b'\x01#\xf037,w\xb9()\x0e4\x92\xdf\x11\xca\xea\xa5\x13/\x10\x1bJ\xa7\x16\x07\x07G\xb1\x01_\x16\xcaG\xe9\xb6\xa1\xfa\xd5\x82\xf4k\x04\x9c\x8e\xc8\x17\xb4G\xe1c*n\xf4o\x02\x85\xf1\x19\xa8\x83`\xfb\xf8\xa2',  # noqa: E501 
                b'\x029b'
            ]),
        (
            b'\x12\x34\x56\x78',
            [
                b'\x00\x80\x124V\xde\xb5\x8f\xdb\x98\xc0\xe8\xed\x10\xde\x84\x89\xe1\xc3\x90\xbeoi7y$sJ\x07\xa1h\xf5t\x1c\xac\r+',  # noqa: E501 
                b'\x01\x13\x07<\xa0w6\xd5O\x91\x93\xb1\xde,0}\xe7\xee\x82\xd7\xf6\xce\x1b^\xb7}"\n\xe4&\xe2\xd7v7\x94\x07\x18\xc9\x96E\xf1\x9bS1sv\xa2\x8b\x9a\x88\xfd/>5\xcb3\x9e\x03\x08\r\xe2\xe1\xd5\xaaq',  # noqa: E501 
                b'\x00\x82<M\x84\x97\xc1\xf7S\xf5\xa2\xbb>\xbd\xe9\xc3t\x0f\xac/\xad\xa8\x01\xff\x9aE\t\xc1\xab\x9e\xa3|\xc7Z\xb0v',  # noqa: E501 
                b'\x01#\xf037,w\xb9()\x0e4\x92\xdf\x11\xca\xea\xa5\x13/\x10\x1bJ\xa7\x16\x07\x07G\xb1\x01_\x16\xcaG\xe9\xb6\xa1\xfa\xd5\x82\xf4k\x04\x9c\x8e\xc8\x17\xb4G\xe1c*n\xf4o\x02\x85\xf1\x19\xa8\x83`\xfb\xf8\xa2',  # noqa: E501 
                b'\x029a',
                b'\x029b',
            ]
        ),
        (
            b'\x12\x34\x56',
            [
                b'\x00\x80\x124V\xde\xb5\x8f\xdb\x98\xc0\xe8\xed\x10\xde\x84\x89\xe1\xc3\x90\xbeoi7y$sJ\x07\xa1h\xf5t\x1c\xac\r+',  # noqa: E501 
                b'\x01\x13\x07<\xa0w6\xd5O\x91\x93\xb1\xde,0}\xe7\xee\x82\xd7\xf6\xce\x1b^\xb7}"\n\xe4&\xe2\xd7v7\x94\x07\x18\xc9\x96E\xf1\x9bS1sv\xa2\x8b\x9a\x88\xfd/>5\xcb3\x9e\x03\x08\r\xe2\xe1\xd5\xaaq',  # noqa: E501 
                b'\x00\x82<M\x84\x97\xc1\xf7S\xf5\xa2\xbb>\xbd\xe9\xc3t\x0f\xac/\xad\xa8\x01\xff\x9aE\t\xc1\xab\x9e\xa3|\xc7Z\xb0v',  # noqa: E501 
                b'\x00\x83\x7fR\xce\xe1\xe1 +\x96\xde\xae\xcdV\x13\x9a \x90.7H\xb6\x80\t\x10\xe1(\x03\x15\xde\x94\x17X\xee\xe1',  # noqa: E501 
                b'\x01#\xf037,w\xb9()\x0e4\x92\xdf\x11\xca\xea\xa5\x13/\x10\x1bJ\xa7\x16\x07\x07G\xb1\x01_\x16\xcaG\xe9\xb6\xa1\xfa\xd5\x82\xf4k\x04\x9c\x8e\xc8\x17\xb4G\xe1c*n\xf4o\x02\x85\xf1\x19\xa8\x83`\xfb\xf8\xa2',  # noqa: E501 
                b'\x02ff',
                b'\x029a',
                b'\x029b',
            ]
        ),
        (
            b'\x12',
            [
                b'\x00\x80\x124V\xde\xb5\x8f\xdb\x98\xc0\xe8\xed\x10\xde\x84\x89\xe1\xc3\x90\xbeoi7y$sJ\x07\xa1h\xf5t\x1c\xac\r+',  # noqa: E501 
                b'\x01\x13\x07<\xa0w6\xd5O\x91\x93\xb1\xde,0}\xe7\xee\x82\xd7\xf6\xce\x1b^\xb7}"\n\xe4&\xe2\xd7v7\x94\x07\x18\xc9\x96E\xf1\x9bS1sv\xa2\x8b\x9a\x88\xfd/>5\xcb3\x9e\x03\x08\r\xe2\xe1\xd5\xaaq',  # noqa: E501 
                b'\x00\x82<M\x84\x97\xc1\xf7S\xf5\xa2\xbb>\xbd\xe9\xc3t\x0f\xac/\xad\xa8\x01\xff\x9aE\t\xc1\xab\x9e\xa3|\xc7Z\xb0v',  # noqa: E501 
                b'\x00\x83\x7fR\xce\xe1\xe1 +\x96\xde\xae\xcdV\x13\x9a \x90.7H\xb6\x80\t\x10\xe1(\x03\x15\xde\x94\x17X\xee\xe1',  # noqa: E501 
                b'\x01#\xf037,w\xb9()\x0e4\x92\xdf\x11\xca\xea\xa5\x13/\x10\x1bJ\xa7\x16\x07\x07G\xb1\x01_\x16\xcaG\xe9\xb6\xa1\xfa\xd5\x82\xf4k\x04\x9c\x8e\xc8\x17\xb4G\xe1c*n\xf4o\x02\x85\xf1\x19\xa8\x83`\xfb\xf8\xa2',  # noqa: E501 
                b'\x02ff',
                b'\x029a',
                b'\x029b',
            ]
        ),
        (
            32 * b'\x00',
            [
                b'\x00\x80\x124V\xde\xb5\x8f\xdb\x98\xc0\xe8\xed\x10\xde\x84\x89\xe1\xc3\x90\xbeoi7y$sJ\x07\xa1h\xf5t\x1c\xac\r+',  # noqa: E501 
            ]
        ),
    ),
)
def test_get_witness(test_trie, key, nodes):
    if nodes:
        assert set(nodes) == set(get_witness(test_trie.db, test_trie.root_hash, key))
    else:
        with pytest.raises(InvalidKeyError):
            get_witness(test_trie.db, test_trie.root_hash, key)
