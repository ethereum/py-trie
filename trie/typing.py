import enum
from typing import (
    List,
    NamedTuple,
    Tuple,
    Union,
)
from typing_extensions import (
    Literal,
)

from eth_utils import (
    is_list_like,
)


# The RLP-decoded node is either blank, or a list, full of bytes or recursive nodes
# Recursive definitions don't seem supported at the moment, follow:
#   https://github.com/python/mypy/issues/731
# Another option is to manually declare a few levels of the type. It should be possible
#   to determine the maximum number of embeds with single-nibble keys and single byte values.
RawHexaryNode = Union[
    # Blank node
    Literal[b''],

    # Leaf or extension node are length 2
    # Branch node is length 17
    List[Union[
        # keys, hashes to next nodes, and values
        bytes,

        # embedded subnodes
        "RawHexaryNode",
    ]],
]


class Nibble(enum.IntEnum):
    Hex0 = 0
    Hex1 = 1
    Hex2 = 2
    Hex3 = 3
    Hex4 = 4
    Hex5 = 5
    Hex6 = 6
    Hex7 = 7
    Hex8 = 8
    Hex9 = 9
    HexA = 0xA
    HexB = 0xB
    HexC = 0xC
    HexD = 0xD
    HexE = 0xE
    HexF = 0xF

    def __repr__(self):
        return hex(self.value)


class Nibbles(tuple):
    def __new__(cls, nibbles):
        if not is_list_like(nibbles):
            raise TypeError(f"Must pass in a tuple of nibbles, but got {nibbles!r}")
        else:
            return tuple.__new__(cls, (Nibble(maybe_nibble) for maybe_nibble in nibbles))


class HexaryTrieNode(NamedTuple):
    """
    Public API for a node of a trie, it is pre-processed a bit for simplicity.
    """

    sub_segments: Tuple[Nibbles, ...]
    """
    Sub segments are the _complete_ list of possible subkeys.
    All sub segments *not* listed can be considered to not exist.

    Each sub segment does not include the trie node prefix. For example:
        - Branch nodes have length-1 tuples as sub_segments.
        - Leaf nodes have no sub_segments
        - Extension nodes have one sub_segment
    """

    value: bytes
    """
    This is the value associated with the key which navigates to this node in
    the trie. If empty, will be set to b''.
    """

    suffix: Nibbles
    """
    In a leaf node, there is a suffix of a key remaining before the value is reached.
    This is that series of nibbles. On a branch node with a value, the suffix will be ().
    """

    raw: RawHexaryNode
    """
    The node body, which is useful for calls to HexaryTrie.traverse_from(...),
    for faster access of sub-nodes.
    """
