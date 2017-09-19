import codecs
import itertools

from eth_utils import (
    to_tuple,
)

from trie.constants import (
    NIBBLES_LOOKUP,
    NIBBLE_TERMINATOR,
    HP_FLAG_2,
    HP_FLAG_0,
)
from trie.exceptions import (
    InvalidNibbles,
)


def bytes_to_nibbles(value):
    """
    Convert a byte string to nibbles
    """
    return tuple(NIBBLES_LOOKUP[nibble] for nibble in codecs.encode(value, 'hex'))


@to_tuple
def pairwise(iterable):
    if len(iterable) % 2:
        raise ValueError("Odd length value.  Cannot apply pairwise operation")

    for left, right in zip(*[iter(iterable)] * 2):
        yield left, right


def nibbles_to_bytes(nibbles):
    if any(nibble > 15 or nibble < 0 for nibble in nibbles):
        raise InvalidNibbles(
            "Nibbles contained invalid value.  Must be constrained between [0, 15]"
        )

    if len(nibbles) % 2:
        raise InvalidNibbles("Nibbles must be even in length")

    value = bytes(bytearray(tuple(
        16 * left + right
        for left, right in pairwise(nibbles)
    )))
    return value


def is_nibbles_terminated(nibbles):
    return nibbles and nibbles[-1] == NIBBLE_TERMINATOR


@to_tuple
def add_nibbles_terminator(nibbles):
    if is_nibbles_terminated(nibbles):
        return nibbles
    return itertools.chain(nibbles, (NIBBLE_TERMINATOR,))


@to_tuple
def remove_nibbles_terminator(nibbles):
    if is_nibbles_terminated(nibbles):
        return nibbles[:-1]
    return nibbles


def encode_nibbles(nibbles):
    """
    The Hex Prefix function
    """
    if is_nibbles_terminated(nibbles):
        flag = HP_FLAG_2
    else:
        flag = HP_FLAG_0

    raw_nibbles = remove_nibbles_terminator(nibbles)

    is_odd = len(raw_nibbles) % 2

    if is_odd:
        flagged_nibbles = tuple(itertools.chain(
            (flag + 1,),
            raw_nibbles,
        ))
    else:
        flagged_nibbles = tuple(itertools.chain(
            (flag, 0),
            raw_nibbles,
        ))

    prefixed_value = nibbles_to_bytes(flagged_nibbles)

    return prefixed_value


def decode_nibbles(value):
    """
    The inverse of the Hex Prefix function
    """
    nibbles_with_flag = bytes_to_nibbles(value)
    flag = nibbles_with_flag[0]

    needs_terminator = flag in {HP_FLAG_2, HP_FLAG_2 + 1}
    is_odd_length = flag in {HP_FLAG_0 + 1, HP_FLAG_2 + 1}

    if is_odd_length:
        raw_nibbles = nibbles_with_flag[1:]
    else:
        raw_nibbles = nibbles_with_flag[2:]

    if needs_terminator:
        nibbles = add_nibbles_terminator(raw_nibbles)
    else:
        nibbles = raw_nibbles

    return nibbles
