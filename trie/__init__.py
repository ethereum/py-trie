from __future__ import absolute_import

import pkg_resources
import sys
import warnings

from .trie import (  # noqa: F401
    Trie,
)


if sys.version_info.major < 3:
    warnings.simplefilter('always', DeprecationWarning)
    warnings.warn(DeprecationWarning(
        "The `trie` library is dropping support for Python 2.  Upgrade to Python 3."
    ))
    warnings.resetwarnings()


__version__ = pkg_resources.get_distribution("trie").version
