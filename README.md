# Python Implementation of the Ethereum Trie structure


```shell
$ pip install trie
```

> Warning: This is an early release and is likely to contain bugs as well as
> breaking API changes.


> This library and repository was previously located at https://github.com/pipermerriam/py-trie.  It was transferred to the Ethereum foundation github in November 2017 and renamed to `py-trie`.

## Installation

```sh
pip install trie
```

## Development

```sh
pip install -e . -r requirements-dev.txt
```


### Running the tests

You can run the tests with:

```sh
py.test tests
```

Or you can install `tox` to run the full test suite.


### Releasing

Pandoc is required for transforming the markdown README to the proper format to
render correctly on pypi.

For Debian-like systems:

```
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
>>> from trie import Trie
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

## BinaryTrie
- Note: One drawback of Binary Trie is that **one key can not be the prefix of another key**. For example,
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
