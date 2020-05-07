import enum

from eth_utils import (
    is_list_like,
)


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
