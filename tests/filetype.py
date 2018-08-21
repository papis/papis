from papis.filetype import is_pdf
import tempfile
import os

def test_is_pdf():
    tmp = tempfile.mktemp()

    assert not os.path.exists(tmp)
    assert not is_pdf(tmp)

    with open(tmp, 'w+') as fd:
        fd.write('%PDF-1.8\n')
    assert is_pdf(tmp)
