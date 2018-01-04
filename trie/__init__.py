import pkg_resources
import warnings

from .binary import (  # noqa: F401
    BinaryTrie,
)
from .hexary import (  # noqa: F401
    HexaryTrie,
)


class Trie(HexaryTrie):
    def __init__(self, *args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)
        warnings.warn(DeprecationWarning(
            "The `trie.Trie` class has been renamed to `trie.HexaryTrie`. "
            "Please update your code as the `trie.Trie` class will be removed in "
            "a subsequent release"
        ))
        warnings.resetwarnings()
        super().__init__(*args, **kwargs)


__version__ = pkg_resources.get_distribution("trie").version
