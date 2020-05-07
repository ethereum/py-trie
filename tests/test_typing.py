import pytest

from trie.typing import (
    Nibbles,
)


@pytest.mark.parametrize(
    'valid_nibbles',
    (
        (),
        (0, 0, 0),
        (0xf, ) * 128,  # no length limit on the nibbles
        [0],  # list is an acceptable input to nibbles, though will be converted to tuple
    ),
)
def test_valid_nibbles(valid_nibbles):
    typed_nibbles = Nibbles(valid_nibbles)
    assert typed_nibbles == tuple(valid_nibbles)


@pytest.mark.parametrize(
    'invalid_nibbles, exception',
    (
        (None, TypeError),
        ({0}, TypeError),  # unordered set is not valid input
        ((b'F', ), ValueError),
        (b'F', TypeError),
        ((b'\x00', ), ValueError),
        ((b'\x0F', ), ValueError),
        (0, TypeError),
        (0xf, TypeError),
        ((0, 0x10), ValueError),
        ((0, -1), ValueError),
    ),
)
def test_invalid_nibbles(invalid_nibbles, exception):
    with pytest.raises(exception):
        Nibbles(invalid_nibbles)
