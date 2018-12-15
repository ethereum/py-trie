from trie.exceptions import (
    ValidationError,
)


def validate_is_bytes(value):
    if not isinstance(value, bytes):
        raise ValidationError("Value is not of type `bytes`: got '{0}'".format(type(value)))
