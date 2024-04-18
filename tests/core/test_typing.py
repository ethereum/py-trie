import pytest

from hypothesis import (
    example,
    given,
    strategies as st,
)

from trie.typing import (
    Nibbles,
)


@pytest.mark.parametrize(
    "valid_nibbles",
    (
        (),
        (0, 0, 0),
        (0xF,) * 128,  # no length limit on the nibbles
        [
            0
        ],  # list is an acceptable input to nibbles, though will be converted to tuple
    ),
)
def test_valid_nibbles(valid_nibbles):
    typed_nibbles = Nibbles(valid_nibbles)
    assert typed_nibbles == tuple(valid_nibbles)


@pytest.mark.parametrize(
    "invalid_nibbles, exception",
    (
        (None, TypeError),
        ({0}, TypeError),  # unordered set is not valid input
        ((b"F",), ValueError),
        (b"F", TypeError),
        ((b"\x00",), ValueError),
        ((b"\x0F",), ValueError),
        (0, TypeError),
        (0xF, TypeError),
        ((0, 0x10), ValueError),
        ((0, -1), ValueError),
    ),
)
def test_invalid_nibbles(invalid_nibbles, exception):
    with pytest.raises(exception):
        Nibbles(invalid_nibbles)


@given(st.lists(st.integers(min_value=0, max_value=0xF)), st.booleans())
@example([0], True)
def test_nibbles_repr(nibbles_input, as_ipython):
    nibbles = Nibbles(nibbles_input)

    if as_ipython:

        class FakePrinter:
            str_buffer = ""

            def text(self, new_text):
                self.str_buffer += new_text

        p = FakePrinter()
        nibbles._repr_pretty_(p, cycle=False)
        repr_string = p.str_buffer
    else:
        repr_string = repr(nibbles)

    evaluated_repr = eval(repr_string)
    assert evaluated_repr == tuple(nibbles_input)

    re_cast = Nibbles(evaluated_repr)
    assert re_cast == nibbles
