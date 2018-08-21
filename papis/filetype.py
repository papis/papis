import sys
import os
import re


def is_pdf(filepath):

    if not os.path.exists(filepath):
        return False

    with open(filepath, 'rb') as fd:
        magic = fd.read(8)
    return re.match(r'%PDF-.\..', magic.decode()) is not None


