def test_import_and_version():
    import trie

    assert isinstance(trie.__version__, str)
