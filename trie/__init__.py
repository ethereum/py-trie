from __future__ import absolute_import

import pkg_resources

from .trie import (  # noqa: F401
    Trie,
)


__version__ = pkg_resources.get_distribution("trie").version
