import pkg_resources

from .binary import BinaryTrie  # noqa: F401
from .hexary import HexaryTrie  # noqa: F401

__version__ = pkg_resources.get_distribution("trie").version
