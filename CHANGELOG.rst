py-trie v2.2.0 (2023-10-31)
---------------------------

Improved Documentation
~~~~~~~~~~~~~~~~~~~~~~

- Remove typo in README (`#139 <https://github.com/ethereum/py-trie/issues/139>`__)


Internal Changes - for py-trie Contributors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add upper pin to ``hexbytes`` dependency to due incoming breaking change (`#141 <https://github.com/ethereum/py-trie/issues/141>`__)
- Update `ethereum/tests` fixture to ``v12.4``. (`#143 <https://github.com/ethereum/py-trie/issues/143>`__)
- Merge python project template updates, including move to pre-commit for linting (`#144 <https://github.com/ethereum/py-trie/issues/144>`__)


py-trie v2.1.1 (2023-06-08)
---------------------------

Internal Changes - for py-trie Contributors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- merged updates from the ethereum python project template (`#137 <https://github.com/ethereum/py-trie/issues/137>`__)
- convert old-style `format` strings to f-strings, additional cleanup (`#138 <https://github.com/ethereum/py-trie/issues/138>`__)


v2.1.0
------

Features
~~~~~~~~

- Support Python 3.11

Misc
~~~~

- Merged py-trie with the ethereum python project template

v2.0.2
------

Misc
~~~~

- Remove upper pin on hexbytes dependency

v2.0.1
------

Misc
~~~~

- Make typing_extensions an optional dependency

v2.0.0
------

Breaking Changes
~~~~~~~~~~~~~~~~

- Drop python 3.6 support
- Require rlp dependency to be >=3,<4
- Require eth-utils dependency to be >=2,<3

Features
~~~~~~~~

- Added node_type field to HexaryTrieNode so that users can easily inspect the type
  of a node.
- Add support for python 3.9 and 3.10

Misc
~~~~

- Upgrade typing_extensions dependency

v2.0.0-alpha.4
---------------

Released 2020-08-31

Breaking Changes
~~~~~~~~~~~~~~~~

- Dropped pypy support, upgrade to faster py-rlp v2-alpha.1
  https://github.com/ethereum/py-trie/pull/118

v2.0.0-alpha.3
---------------

Released 2020-08-24

Bugfixes
~~~~~~~~

- Relax the version constraint on typing-extensions, which was causing downstream conflicts.
  https://github.com/ethereum/py-trie/pull/117

v2.0.0-alpha.2
---------------

Released 2020-06-19

Features
~~~~~~~~

- Added NodeIterator.keys(), .items(), .values() (mimicking the dict version of these), as well
  as NodeIterator.nodes(), which yields all of the annotated trie nodes.
  https://github.com/ethereum/py-trie/pull/112
- Improved repr(HexaryTrie)
  https://github.com/ethereum/py-trie/pull/112
- Can now use NodeIterator to navigate to the empty key b'', using NodeIterator.next(key=None) or
  simply NodeIterator.next().
  https://github.com/ethereum/py-trie/pull/110
- TraversedPartialPath has a new simulated_node attribute, which we can treat as a node that
  would have been at the traversed path if the traversal had succeeded. See the readme for more.
  https://github.com/ethereum/py-trie/pull/111

Bugfixes
~~~~~~~~

- In certain cases, deleting key b'short' would actually delete the key at b'short-nope-long'!
  Changed key_starts_with() to fix it
  https://github.com/ethereum/py-trie/pull/109
- HexaryTrie.set(key, b'') would sometimes try to create a leaf node with an
  empty value. Instead, it should act exactly the same as HexaryTrie.delete(key)
  https://github.com/ethereum/py-trie/pull/109
- When a MissingTrieNode is raised during pruning (or using squash_changes()), a node body
  that was pruned before the exception was raised might stay pruned, even though the trie
  wasn't updated.
  https://github.com/ethereum/py-trie/pull/109
- When using squash_changes() on a HexaryTrie with prune=True, doing a no-op change would
  cause the root node to get pruned (deleted even though it was still needed for the current
  root hash!).
  https://github.com/ethereum/py-trie/pull/113
- Only raise a TraversedPartialPath when traversing into a matching leaf node. Instead, return
  an empty node when traversing into a divergent path.
  https://github.com/ethereum/py-trie/pull/114


v2.0.0-alpha.1
---------------

Released 2020-05-27

Breaking Changes
~~~~~~~~~~~~~~~~

- Removed trie.Trie -- use trie.HexaryTrie instead
  https://github.com/ethereum/py-trie/pull/100
- Removed trie.sync (classes: SyncRequest and HexaryTrieSync)
  New syncing helper tools are imminent.
  https://github.com/ethereum/py-trie/pull/100
- MissingTrieNode is no longer a KeyError, paving the way for eventually raising a KeyError instead
  of returning b'' when a key is not present in the trie
  https://github.com/ethereum/py-trie/pull/98
- If a trie body is missing when calling HexaryTrie.root_node, the exception will be
  MissingTraversalNode instead of MissingTrieNode
  https://github.com/ethereum/py-trie/pull/102
- Remove support for setting the trie's raw root node directly, via
  HexaryTrie.root_node = new_raw_root_node
  https://github.com/ethereum/py-trie/pull/106
- Return new annotated HexaryTrieNode from HexaryTrie.root_node property
  https://github.com/ethereum/py-trie/pull/106

Features
~~~~~~~~

- MissingTrieNode now includes the prefix of the key leading to the node body that was missing
  from the database. This is important for other potential database layouts. The prefix may be None,
  if it cannot be determined. For now, it will not be determined when setting or deleting a key.
  https://github.com/ethereum/py-trie/pull/98
- New HexaryTrie.traverse(tuple_of_nibbles) returns an annotated trie node found at the
  given path of nibbles, starting from the root.
  https://github.com/ethereum/py-trie/pull/102
- New HexaryTrie.traverse_from(node, tuple_of_nibbles) returns an annotated trie node found
  when navigating from the given node_body down through the given path of nibbles. Useful for
  avoiding database reads when the parent node body is known. Otherwise, navigating down from
  the root would be required every time.
  https://github.com/ethereum/py-trie/pull/102
- New MissingTraversalNode exception, analogous to MissingTrieNode, but when traversing
  (because key is not available, and root_hash not available during traverse_from())
  https://github.com/ethereum/py-trie/pull/102
- New TraversedPartialPath exception, raised when you try to navigate to a node, but end up
  part-way inside an extension node, or try to navigate into a leaf node.
  https://github.com/ethereum/py-trie/pull/102
- New HexaryTrieFog to help track unexplored prefixes, when walking a trie. Serializeable to bytes.
  New exceptions PerfectVisibility or FullDirectionalVisibility when no prefixes are unexplored.
  New TrieFrontierCache to reduce duplicate database accesses on a full trie walk.
  https://github.com/ethereum/py-trie/pull/95

Bugfixes
~~~~~~~~

- Pruning Bugfix: with duplicate values at multiple keys, pruning would sometimes incorrectly
  prune out a node that was still required. This is fixed for fresh databases, and unfixable
  for existing databases. (Prune is not designed for on-disk/existing DBs anyhow)
  https://github.com/ethereum/py-trie/pull/93
- Avoid reading root node when unnecessary during squash_changes(). This can be important when
  building a witness, if the witness is supposed to be empty. (for example, in storage tries)
  https://github.com/ethereum/py-trie/pull/101

Misc
~~~~

- Type annotation cleanups & upgrades flake8/eth-utils
  https://github.com/ethereum/py-trie/pull/95

1.4.0
----------

Released 2019-04-24

- Python 3.7 support
  https://github.com/ethereum/py-trie/pull/73
- Several proof (aka witness) updates
  - Added HexaryTrie.get_proof for proving a key exists https://github.com/ethereum/py-trie/pull/80
  - Prove a key is missing with get_proof https://github.com/ethereum/py-trie/pull/91
  - Bugfix getting a key from a proof with short nodes https://github.com/ethereum/py-trie/pull/82
- Raise MissingTrieNode with extra info, when an expected trie node is missing from the database
  (includes update so that pruning old nodes waits until set/delete succeeds)
  https://github.com/ethereum/py-trie/pull/83
  https://github.com/ethereum/py-trie/pull/86 (minor cleanup of 83)
  https://github.com/ethereum/py-trie/pull/90 (squash_changes() support for missing nodes)
- New `with trie.at_root(hash) as snapshot:` API, to read trie at a different root hash
  https://github.com/ethereum/py-trie/pull/84
- EXPERIMENTAL Sparse Merkle Trie in trie.smt (unstable API: could change at minor version)
  https://github.com/ethereum/py-trie/pull/77
- Dropped support for rlp v0.x
  https://github.com/ethereum/py-trie/pull/75
- Doc updates
  - https://github.com/ethereum/py-trie/pull/62
  - https://github.com/ethereum/py-trie/pull/64
  - https://github.com/ethereum/py-trie/pull/72 (plus other maintenance)

1.3.8
--------

* Speed optimization for `HexaryTrie._prune_node` (https://github.com/ethereum/py-trie/pull/60)

1.1.0
--------

* Add trie syncing
* Witness helper functions for binary trie

1.0.1
--------

* Fix broken deprecated `Trie` class.

1.0.0
--------

* Rename `Trie` to `HexaryTrie`
* Add new `BinaryTrie` class

0.3.2
--------

* Add `Trie.get_from_proof` for verification of trie proofs.

0.3.0
--------

* Remove snapshot and revert API

0.1.0
--------

* Initial Release
