# Python Implementation of the Ethereum Trie structure


```shell
$ pip install trie
```

> Warning: This is an early release and is likely to contain bugs as well as
> breaking API changes.


# Usage

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

