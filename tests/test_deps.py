def test_pygments():
    # This function exists after version 2.2.0 only
    from pygments.lexers import find_lexer_class_by_name
    yaml = find_lexer_class_by_name('yaml')
    assert(yaml is not None)

def test_colorama():
    import colorama
    assert(colorama.Back)
    assert(colorama.Fore)
