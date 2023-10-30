from importlib.metadata import (
    version as __version,
)

from .binary import (
    BinaryTrie,
)
from .hexary import (
    HexaryTrie,
)

__version__ = __version("trie")
