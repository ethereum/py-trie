from hypothesis import (
    given,
    strategies as st,
)

from trie.utils.binaries import (
    decode_from_bin,
    decode_to_bin_keypath,
    encode_from_bin_keypath,
    encode_to_bin,
)


@given(value=st.binary(min_size=0, max_size=1024))
def test_round_trip_bin_encoding(value):
    value_as_binaries = encode_to_bin(value)
    result = decode_from_bin(value_as_binaries)
    assert result == value


@given(value=st.lists(elements=st.integers(0, 1), min_size=0, max_size=1024))
def test_round_trip_bin_keypath_encoding(value):
    value_as_bin_keypath = encode_from_bin_keypath(bytes(value))
    result = decode_to_bin_keypath(value_as_bin_keypath)
    assert result == bytes(value)
