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
>>> t = Trie(db={})
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
>>> from trie import Trie
>>> t = Trie(db={})
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

