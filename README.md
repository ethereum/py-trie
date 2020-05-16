# Python Implementation of the Ethereum Trie structure

[![PyPI](https://img.shields.io/pypi/v/trie.svg)](https://pypi.org/project/trie/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/trie.svg)

> This library and repository was previously located at [pipermerriam/py-trie](https://github.com/pipermerriam/py-trie). It was transferred to the Ethereum foundation GitHub in 
> November 2017 and renamed to `py-trie`.

## Installation

```sh
pip install trie
```

## Development

```sh
pip install -e .[dev]
```

### Running the tests

You can run the tests with:

```sh
pytest tests
```

Or you can install `tox` to run the full test suite.

### Releasing

Pandoc is required for transforming the markdown README to the proper format to
render correctly on pypi.

For Debian-like systems:

```sh
apt install pandoc
```

Or on OSX:

```sh
brew install pandoc
```

To release a new version:

```sh
bumpversion $$VERSION_PART_TO_BUMP$$
git push && git push --tags
make release
```

#### How to bumpversion

The version format for this repo is `{major}.{minor}.{patch}` for stable, and
`{major}.{minor}.{patch}-{stage}.{devnum}` for unstable (`stage` can be alpha or beta).

To issue the next version in line, use bumpversion and specify which part to bump,
like `bumpversion minor` or `bumpversion devnum`.

If you are in a beta version, `bumpversion stage` will switch to a stable.

To issue an unstable version when the current version is stable, specify the
new version explicitly, like `bumpversion --new-version 4.0.0-alpha.1 devnum`

## Usage

```python
>>> from trie import HexaryTrie
>>> t = HexaryTrie(db={})
>>> t.root_hash
b'V\xe8\x1f\x17\x1b\xccU\xa6\xff\x83E\xe6\x92\xc0\xf8n[H\xe0\x1b\x99l\xad\xc0\x01b/\xb5\xe3c\xb4!'
>>> t.set(b'my-key', b'some-value')
>>> t.get(b'my-key')
b'some-value'
>>> t.exists(b'another-key')
False
>>> t.set(b'another-key', b'another-value')
>>> t.exists(b'another-key')
True
>>> t.delete(b'another-key')
>>> t.exists(b'another-key')
False
```

You can also use it like a dictionary.

```python
>>> from trie import HexaryTrie
>>> t = HexaryTrie(db={})
>>> t.root_hash
b'V\xe8\x1f\x17\x1b\xccU\xa6\xff\x83E\xe6\x92\xc0\xf8n[H\xe0\x1b\x99l\xad\xc0\x01b/\xb5\xe3c\xb4!'
>>> t[b'my-key'] = b'some-value'
>>> t[b'my-key']
b'some-value'
>>> b'another-key' in t
False
>>> t[b'another-key']  = b'another-value'
>>> b'another-key' in t
True
>>> del t[b'another-key']
>>> b'another-key' in t
False
```

### Traversing (inspecting trie internals)

```python
>>> from trie import HexaryTrie
>>> t = HexaryTrie(db={})
>>> t.root_hash
b'V\xe8\x1f\x17\x1b\xccU\xa6\xff\x83E\xe6\x92\xc0\xf8n[H\xe0\x1b\x99l\xad\xc0\x01b/\xb5\xe3c\xb4!'
>>> t[b'my-key'] = b'some-value'
>>> t[b'my-other-key']  = b'another-value'

# Look at the root node:
>>> root_node = t.traverse(())
>>> root_node
HexaryTrieNode(sub_segments=((0x6, 0xd, 0x7, 0x9, 0x2, 0xd, 0x6),), value=b'', suffix=(), raw=[b'\x16\xd7\x92\xd6', b'\xb4q\xb8h\xec\x1c\xe1\xf4\\\x88\xda\xb4\xc1\xc2n\xbaw\xd0\x9c\xf1\xacV\xb4Dk\xa7\xe6\xd7qf\xc2\x82'])

# the root node is an extension down, because the first 7 nibbles are the same between the two keys

# Let's walk down to the child of that extension 
>>> prefix6d792d6 = t.traverse(root_node.sub_segments[0])
>>> prefix6d792d6
HexaryTrieNode(sub_segments=((0xb,), (0xf,)), value=b'', suffix=(), raw=[b'', b'', b'', b'', b'', b'', b'', b'', b'', b'', b'', [b' ey', b'some-value'], b'', b'', b'', [b' ther-key', b'another-value'], b''])

# A branch node separates the second nibbles of b'k' and b'o': 0xb and 0xf
# Notice the position of the children in the 11th and 15th index

# Another way to get there without loading the root node from the database is using traverse_from:
>>> assert t.traverse_from(root_node.raw, root_node.sub_segments[0]) == prefix6d792d6

# Embedded nodes can be traversed to the same way as nodes stored in the database:

>>> t.traverse(root_node.sub_segments[0] + (0xb,))
HexaryTrieNode(sub_segments=(), value=b'some-value', suffix=(0x6, 0x5, 0x7, 0x9), raw=[b' ey', b'some-value'])

# This leaf node includes the suffix (the rest of the key, in nibbles, that haven't been traversed,
# just b'ey': 0x6579

```

## BinaryTrie

**Note:** One drawback of Binary Trie is that **one key can not be the prefix of another key**. For example,
if you already set the value `value1` with key `key1`, you can not set another value with key `key` or `key11`
and the like.

### BinaryTrie branch and witness helper functions

```python
>>> from trie import BinaryTrie
>>> from trie.branches import (
>>>     check_if_branch_exist,
>>>     get_branch,
>>>     if_branch_valid,
>>>     get_witness_for_key_prefix,
>>> )
>>> t = BinaryTrie(db={})
>>> t.root_hash
b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p"
>>> t.set(b'key1', b'value1')
>>> t.set(b'key2', b'value2')
```

Now Trie looks like this:
```
    root --->  (kvnode, *common key prefix*)
                         |
                         |
                         |
                    (branchnode)
                     /         \
                    /           \
                   /             \
(kvnode, *remain kepath*)(kvnode, *remain kepath*)
            |                           |
            |                           |
            |                           |
  (leafnode, b'value1')       (leafnode, b'value2')
```

```python
>>> # check_if_branch_exist function
>>> check_if_branch_exist(t.db, t.root_hash, b'key')
True
>>> check_if_branch_exist(t.db, t.root_hash, b'key1')
True
>>> check_if_branch_exist(t.db, t.root_hash, b'ken')
False
>>> check_if_branch_exist(t.db, t.root_hash, b'key123')
False
>>> # get_branch function
>>> get_branch(t.db, t.root_hash, b'key1')
(b'\x00\x82\x1a\xd9^L|38J\xed\xf31S\xb2\x97A\x8dy\x91RJ\x92\xf5ZC\xb4\x99T&;!\x9f\xa9!\xa2\xfe;', b"\x01*\xaccxH\x89\x08}\x93|\xda\xb9\r\x9b\x82\x8b\xb2Y\xbc\x10\xb9\x88\xf40\xef\xed\x8b'\x13\xbc\xa5\xccYGb\xc2\x8db\x88lPs@)\x86v\xd7B\xf7\xd3X\x93\xc9\xf0\xfd\xae\xe0`j#\x0b\xca;\xf8", b'\x00\x11\x8aEL3\x839E\xbd\xc4G\xd1xj\x0fxWu\xcb\xf6\xf3\xf2\x8e7!M\xca\x1c/\xd7\x7f\xed\xc6', b'\x02value1')
```

Node started with `b'\x00'`, `b'\x01'` and `b'\x02'` are kvnode, branchnode and leafnode respectively.

```python
>>> get_branch(t.db, t.root_hash, b'key')
(b'\x00\x82\x1a\xd9^L|38J\xed\xf31S\xb2\x97A\x8dy\x91RJ\x92\xf5ZC\xb4\x99T&;!\x9f\xa9!\xa2\xfe;',)
>>> get_branch(t.db, t.root_hash, b'key123') # InvalidKeyError
>>> get_branch(t.db, t.root_hash, b'key5') # there is still branch for non-exist key
(b'\x00\x82\x1a\xd9^L|38J\xed\xf31S\xb2\x97A\x8dy\x91RJ\x92\xf5ZC\xb4\x99T&;!\x9f\xa9!\xa2\xfe;',)
>>> # if_branch_valid function
>>> v = t.get(b'key1')
>>> b = get_branch(t.db, t.root_hash, b'key1')
>>> if_branch_valid(b, t.root_hash, b'key1', v)
True
>>> v = t.get(b'key5') # v should be None
>>> b = get_branch(t.db, t.root_hash, b'key5')
>>> if_branch_valid(b, t.root_hash, b'key5', v)
True
>>> v = t.get(b'key1')
>>> b = get_branch(t.db, t.root_hash, b'key2')
>>> if_branch_valid(b, t.root_hash, b'key1', v) # KeyError
>>> if_branch_valid([], t.root_hash, b'key1', v) # AssertionError
>>> # get_witness_for_key_prefix function
>>> get_witness_for_key_prefix(t.db, t.root_hash, b'key1') # equivalent to `get_branch(t.db, t.root_hash, b'key1')`
(b'\x00\x82\x1a\xd9^L|38J\xed\xf31S\xb2\x97A\x8dy\x91RJ\x92\xf5ZC\xb4\x99T&;!\x9f\xa9!\xa2\xfe;', b"\x01*\xaccxH\x89\x08}\x93|\xda\xb9\r\x9b\x82\x8b\xb2Y\xbc\x10\xb9\x88\xf40\xef\xed\x8b'\x13\xbc\xa5\xccYGb\xc2\x8db\x88lPs@)\x86v\xd7B\xf7\xd3X\x93\xc9\xf0\xfd\xae\xe0`j#\x0b\xca;\xf8", b'\x00\x11\x8aEL3\x839E\xbd\xc4G\xd1xj\x0fxWu\xcb\xf6\xf3\xf2\x8e7!M\xca\x1c/\xd7\x7f\xed\xc6', b'\x02value1')
>>> get_witness_for_key_prefix(t.db, t.root_hash, b'key') # this will include additional nodes of b'key2'
(b'\x00\x82\x1a\xd9^L|38J\xed\xf31S\xb2\x97A\x8dy\x91RJ\x92\xf5ZC\xb4\x99T&;!\x9f\xa9!\xa2\xfe;', b"\x01*\xaccxH\x89\x08}\x93|\xda\xb9\r\x9b\x82\x8b\xb2Y\xbc\x10\xb9\x88\xf40\xef\xed\x8b'\x13\xbc\xa5\xccYGb\xc2\x8db\x88lPs@)\x86v\xd7B\xf7\xd3X\x93\xc9\xf0\xfd\xae\xe0`j#\x0b\xca;\xf8", b'\x00\x11\x8aEL3\x839E\xbd\xc4G\xd1xj\x0fxWu\xcb\xf6\xf3\xf2\x8e7!M\xca\x1c/\xd7\x7f\xed\xc6', b'\x02value1', b'\x00\x10O\xa9\x0b\x1c!_`<\xb5^\x98D\x89\x17\x148\xac\xda&\xb3P\xf6\x06[\x1b9\xc09\xbas\x85\xf5', b'\x02value2')
>>> get_witness_for_key_prefix(t.db, t.root_hash, b'') # this will return the whole trie
```
