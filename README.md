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
>>> assert t.traverse_from(root_node, root_node.sub_segments[0]) == prefix6d792d6

# Embedded nodes can be traversed to the same way as nodes stored in the database:

>>> t.traverse(root_node.sub_segments[0] + (0xb,))
HexaryTrieNode(sub_segments=(), value=b'some-value', suffix=(0x6, 0x5, 0x7, 0x9), raw=[b' ey', b'some-value'])

# This leaf node includes the suffix (the rest of the key, in nibbles, that haven't been traversed,
# just b'ey': 0x6579

```

### Walking a full trie

To walk through the full trie (for example, to verify that all node bodies are present in the database),
use HexaryTrieFog and the traversal API above.

For example:

```python

>>> from trie import HexaryTrie
>>> t = HexaryTrie(db={})
>>> t.root_hash
b'V\xe8\x1f\x17\x1b\xccU\xa6\xff\x83E\xe6\x92\xc0\xf8n[H\xe0\x1b\x99l\xad\xc0\x01b/\xb5\xe3c\xb4!'
>>> t[b'my-key'] = b'some-value'
>>> t[b'my-other-key']  = b'another-value'
>>> t[b'your-key'] = b'your-value'
>>> t[b'your-other-key'] = b'your-other-value'
>>> t.root_hash
b'\xf8\xdd\xe4\x0f\xaa\xf4P7\xfa$\xfde>\xec\xb4i\x00N\xa3)\xcf\xef\x80\xc4YU\xe8\xe7\xbf\xa89\xd5'

# Initialize a fog object to track unexplored prefixes in a trie walk
>>> from from trie.fog import HexaryTrieFog
>>> empty_fog = HexaryTrieFog()
# At the beginning, the unexplored prefix is (), which means that none of the trie has been explored
>>> prefix = empty_fog.nearest_unknown()
()

# So we start by exploring the node at prefix () -- which is the root node:
>>> node = t.traverse(prefix)
HexaryTrieNode(sub_segments=((0x6,), (0x7,)), value=b'', suffix=(), raw=[b'', b'', b'', b'', b'', b'', b"\x03\xd2vk\x85\xce\xe1\xa8\xdb'F\x8c\xe5\x15\xc6\n+M:th\xa1\\\xb13\xcc\xe8\xd0\x1d\xa7\xa8U", b"\x1b\x8d'\xb3\x99(yX\xaa\x96C!\xba'X \xbb|\xa6,\xb5V!\xd3\x1a\x05\xe5\xbf\x02\xa3fR", b'', b'', b'', b'', b'', b'', b'', b'', b''])
# and mark the root as explored, while defining the unexplored children:
>>> level1fog = empty_fog.explore(prefix, node.sub_segments)
# Now the unexplored prefixes are the keys starting with the four bits 6 and the four bits 7.
# All other keys are known to not exist (and so have been explored)
>>> level1fog
HexaryTrieFog<SortedSet([(0x6,), (0x7,)])>

# So we continue exploring. The fog helps choose which prefix to explore next:
>>> level1fog.nearest_unknown()
(0x6,)
# We can also look for the nearest unknown key to a particular target
>>> prefix = level1fog.nearest_unknown((8, 1))
(0x7,)
>>> node7 = node.traverse(prefix)
HexaryTrieNode(sub_segments=((0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6),), value=b'', suffix=(), raw=[b'\x00\x96\xf7W"\xd6', b"\xe2\xe2oN\xe1\xf8\xda\xc1\x8c\x03\x92'\x93\x805\xad-\xef\x07_\x0ePV\x1f\xb5/lVZ\xc6\xc1\xf9"])
# We found an extension node, and mark it in the fog
# For simpliticy, we'll start clobbering the `fog` variable
>>> fog = level1fog.explore(prefix, node7.sub_segments)
HexaryTrieFog<SortedSet([(0x6,), (0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6)])>

# Let's explore the next branch node and see what's left
>>> prefix = fog.nearest_unknown((7,))
(0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6)
>>> node796f75722d6 = t.traverse(prefix)
HexaryTrieNode(sub_segments=((0xb,), (0xf,)), value=b'', suffix=(), raw=[b'', b'', b'', b'', b'', b'', b'', b'', b'', b'', b'', [b' ey', b'your-value'], b'', b'', b'', [b' ther-key', b'your-other-value'], b''])
# Notice that the branch node inlines the values, but the fog and annotated node ignore them for now
>>> fog = fog.explore(prefix, node796f75722d6.sub_segments)
HexaryTrieFog<SortedSet([(0x6,), (0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb), (0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xf)])>

# Index keys may not matter for some use cases, so we can leave them out
#   entirely, like nearest_unknown().
# There's one more feature to consider: we can look directionally to the right
#   of an index for the nearest prefix.
>>> prefix = fog.nearest_right((0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xc))
(0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xf)
# That same index key would give a closer prefix to the left if direction didn't matter
#   (See the difference in the very last nibble)
>>> fog.nearest_unknown((0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xc))
(0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb)
# So we traverse to this last embedded leaf node at `prefix`
>>> a_leaf_node = t.traverse(prefix)
HexaryTrieNode(sub_segments=(), value=b'your-other-value', suffix=(0x7, 0x4, 0x6, 0x8, 0x6, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb, 0x6, 0x5, 0x7, 0x9), raw=[b' ther-key', b'your-other-value'])
# we mark the prefix as fully explored like so:
>>> fog = fog.explore(prefix, a_leaf_node.sub_segments)
HexaryTrieFog<SortedSet([(0x6,), (0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb)])>
# Notice that sub_segments was empty, and the prefix has disappeared from our list of unexplored prefixes

# So far we have dealt with an un-changing trie, but what if it is
#   modified while we are working on it?
>>> del t[b'your-other-key']
>>> t[b'your-key-rebranched'] = b'your-value'
>>> t.root_hash
b'"\xc0\xcaQ\xa7X\x08E\xb5"A\xde\xbfY\xeb"XY\xb1O\x034=\x04\x06\xa9li\xd8\x92\xadP'

# The unexplored prefixes we have before might not exist anymore. They might:
#   1. have been deleted entirely, in which case, we will get a blank node, and need no special treatment
#   2. lead us into the middle of a leaf or extension node, which makes things tricky
>>> prefix = fog.nearest_unknown((8,))
(0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb)
>>> t.traverse(prefix)
TraversedPartialPath: Could not traverse through HexaryTrieNode(sub_segments=((0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb, 0x6, 0x5, 0x7, 0x9),), value=b'', suffix=(), raw=[b'\x19our-key', b'f\xbe\x88\x8f#\xd5\x15-8\xc0\x1f\xfb\xf7\x8b=\x98\x86 \xec\xdeK\x07\xc8\xbf\xa7\x93\xfa\x9e\xc1\x89@\x00']) at (0x7,), only partially traversed with: (0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb)

# Let's drill into what this means:
#   - We fully traversed to a node at prefix (7,)
#   - We tried to traverse into the rest of the prefix
#   - We only got part-way through the extension node: (0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb)
#   - The extension node full sub-segment is actually: (0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb, 0x6, 0x5, 0x7, 0x9)

# So what do we do about it? Catch the exception, and explore with the fog slightly differently
>>> from trie.exceptions import TraversedPartialPath
>>> last_exception = None
>>> try:
      t.traverse(prefix)
    except TraversedPartialPath as exc:
      last_exception = exc

# We can now continue exploring the children of the extension node, by using an attribute on the exception:
>>> sub_segments = last_exception.simulated_node.sub_segments
((0x6, 0x5, 0x7, 0x9),)
# Note that this sub-segment now carries us the rest of the way to the child
#   of the node that we only partially traversed into.
# This "simulated_node" is created by slicing the extension node in two: the
#   first extension node having the path that we (partially) traversed, and the second
#   extension node being the child of that parent, which continues on to point to
#   the child of the original extension.
# If the exception is raised on a leaf node, then the leaf node is sliced into
#   an extension and another shorter leaf node.
>>> fog = fog.explore(prefix, sub_segments)
HexaryTrieFog<SortedSet([(0x6,), (0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb, 0x6, 0x5, 0x7, 0x9)])>

# So now we can pick up where we left off, traversing to the child of the extension node, and so on.
>>> prefix = fog.nearest_unknown((8,))
(0x7, 0x9, 0x6, 0xf, 0x7, 0x5, 0x7, 0x2, 0x2, 0xd, 0x6, 0xb, 0x6, 0x5, 0x7, 0x9)
# The following will not raise a TraversedPartialPath exception, because we know that
#   a node was at the path, and the trie hasn't changed:
>>> t.traverse(prefix)
HexaryTrieNode(sub_segments=((0x2,),), value=b'your-value', suffix=(), raw=[b'', b'', [b'=rebranched', b'your-value'], b'', b'', b'', b'', b'', b'', b'', b'', b'', b'', b'', b'', b'', b'your-value'])

# etc...
```

**Note**: `traverse()` will access the database for every node from the root to the target node. If navigating a large trie, consider using `TrieFrontierCache` and `HexaryTrie.traverse_from()` to minimize database lookups. See the tests in `tests/test_hexary_trie_walk.py` for some examples.

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
