import pytest
import warnings


@pytest.fixture(autouse=True)
def show_all_warnings():
    warnings.simplefilter("always")
