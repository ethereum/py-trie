import sys

# remove once trie supports python>=3.8
if sys.version_info >= (3, 8):
    from typing import (
        Literal,
        Protocol,
    )
else:
    from typing_extensions import (  # noqa: F401
        Literal,
        Protocol,
    )
