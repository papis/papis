import re
import os
import tempfile
import unittest
from unittest.mock import patch
import tests
import tests.cli
import papis.config
import papis.crossref
from papis.commands.add import (
    run, cli,
    get_file_name,
    get_hash_folder
)
from tests import (
    create_random_pdf, create_random_file, create_random_epub,
    create_real_document
)
from papis.filetype import get_document_extension


def test_get_hash_folder():
    path = tempfile.mktemp(prefix='papis-get_name-')
    open(path, 'w+').close()
    data = dict(author='don quijote de la mancha')

    hh = get_hash_folder(data, [path])
    assert re.match(r'.*-don-quijote-de-la-ma$', hh) is not None

    three_files_hh = get_hash_folder(data, [path, path, path])
    assert re.match(r'.*-don-quijote-de-la-ma$', three_files_hh) is not None
    assert not three_files_hh == hh

    # Without data
    no_files_hh = get_hash_folder(data, [])
    assert re.match(r'.*-don-quijote-de-la-ma$', no_files_hh) is not None
    assert not no_files_hh == hh

    data = dict()
    hh = get_hash_folder(data, [path])
    assert re.match(r'.*-don-quijote-de-la-ma$', hh) is None

    path = tempfile.mktemp(prefix='papis-get_name-')
    open(path, 'w+').close()
    newhh = get_hash_folder(data, [path])
    assert not hh == newhh

    newnewhh = get_hash_folder(data, [path])
    assert not newnewhh == newhh


class TestGetFileName(unittest.TestCase):
    def setUp(self):
        tests.setup_test_library()

    def test_get_file_name(self):
        pdf = create_random_pdf(suffix='.pdf')
        path = create_random_file(prefix='papis-get_name-')

        assert(papis.config.get('add-file-name') is None)
        filename = get_file_name(dict(title='blah'), path, suffix='3')
        assert(re.match(r'^papis-get-name-.*\.data$', filename) is not None)
        # With suffix
        filename = get_file_name(dict(title='blah'), pdf, suffix='3')
        assert(len(re.split('[.]pdf', filename)) == 2)
        # Without suffix
        filename = get_file_name(dict(title='blah'), pdf)
        assert(len(re.split('[.]pdf', filename)) == 2)

        papis.config.set(
            'add-file-name',
            '{doc[title]} {doc[author]} {doc[yeary]}'
        )

        filename = get_file_name(dict(title='blah'), path, suffix='2')
        assert filename == 'blah-2.data'

        filename = get_file_name(dict(title='b' * 200), path, suffix='2')
        assert filename == 'b' * 150 + '-2.data'

        filename = get_file_name(
            dict(title='blah'), create_random_pdf(suffix='.pdf'), suffix='2'
        )
        assert filename == 'blah-2.pdf'

        filename = get_file_name(
            dict(title='blah'), create_random_pdf(), suffix='2'
        )
        assert filename == 'blah-2.pdf'

        filename = get_file_name(
            dict(title='blah'), create_random_file(suffix='.yaml'), suffix='2'
        )
        assert filename == 'blah-2.yaml'


class TestRun(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def test_nofile_exception(self):
        path = tempfile.mktemp()
        self.assertTrue(not os.path.exists(path))
        try:
            run(
                [path],
                data=dict(author='Bohm', title='My effect')
            )
            self.assertTrue(False)
        except IOError:
            self.assertTrue(True)

    def test_nofile_add(self):
        run(
            [],
            data=dict(author='Evangelista', title='MRCI')
        )
        db = papis.database.get()
        docs = db.query_dict(dict(author="Evangelista"))
        self.assertTrue(len(docs) == 1)
        doc = docs[0]
        self.assertTrue(doc is not None)
        self.assertTrue(len(doc.get_files()) == 0)

    def test_add_with_data(self):
        data = {
            "journal": "International Journal of Quantum Chemistry",
            "language": "en",
            "issue": "15",
            "title": "How many-body perturbation theory has changed qm ",
            "url": "http://doi.wiley.com/10.1002/qua.22384",
            "volume": "109",
            "author": "Kutzelnigg, Werner",
            "type": "article",
            "doi": "10.1002/qua.22384",
            "year": "2009",
            "ref": "2FJT2E3A"
        }
        number_of_files = 10
        paths = [tempfile.mktemp() for i in range(number_of_files)]
        for p in paths:
            open(p, 'w+').close()

        run(paths, data=data)

        db = papis.database.get()
        docs = db.query_dict(dict(author="Kutzelnigg, Werner"))
        self.assertTrue(len(docs) == 1)
        doc = docs[0]
        self.assertTrue(doc is not None)
        self.assertTrue(len(doc.get_files()) == number_of_files)


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_set(self):
        result = self.invoke([
            '-s', 'author', 'Bertrand Russell',
            '-b',
            '--set', 'title', 'Principia'
        ])
        self.assertTrue(result.exit_code == 0)
        db = papis.database.get()
        docs = db.query_dict(dict(author="Bertrand Russell"))
        self.assertTrue(len(docs) == 1)
        self.assertTrue(len(docs[0].get_files()) == 0)

    def test_link(self):
        pdf = create_random_pdf()
        result = self.invoke([
            '-s', 'author', 'Plato',
            '--set', 'title', 'Republic',
            '-b',
            '--link', pdf
        ])
        #self.assertTrue(result.exit_code == 0)
        db = papis.database.get()
        docs = db.query_dict(dict(author="Plato"))
        self.assertTrue(len(docs) == 1)
        doc = docs[0]
        self.assertTrue(len(doc.get_files()) == 1)
        self.assertTrue(os.path.islink(doc.get_files()[0]))

    @patch('papis.utils.open_file', lambda x: None)
    @patch('papis.tui.utils.confirm', lambda x: True)
    @patch(
        'papis.utils.update_doc_from_data_interactively',
        lambda ctxdata, impdata, string: ctxdata.update(impdata))
    @patch('papis.utils.open_file', lambda x: None)
    def test_name_and_from_folder(self):
        pdf = create_random_pdf(suffix='.pdf')
        result = self.invoke([
            '-s', 'author', 'Aristoteles',
            '--set', 'title', '"The apology of socrates"',
            '-b',
            '--folder-name', 'the_apology', pdf
        ])
        self.assertTrue(result.exit_code == 0)
        db = papis.database.get()
        docs = db.query_dict(dict(author="Aristoteles"))
        self.assertTrue(len(docs) == 1)
        doc = docs[0]
        assert(os.path.basename(doc.get_main_folder()) == 'the-apology')
        assert(len(doc.get_files()) == 1)
        gotpdf = doc.get_files()[0]
        assert(len(re.split(r'[.]pdf', pdf)) == 2)
        assert(len(re.split(r'[.]pdf', gotpdf)) == 2)

        result = self.invoke([
            '--from', 'folder', doc.get_main_folder()
        ])
        # FIXME: this is not working I don't know why
        #        I get <Result UnsupportedOperation('fileno')>
        # self.assertTrue(result.exit_code == 0)
        # docs = db.query_dict(dict(author="Aristoteles"))
        # self.assertTrue(len(docs) == 2)

    @patch('papis.utils.open_file', lambda x: None)
    @patch('papis.tui.utils.confirm', lambda x: True)
    @patch(
        'papis.utils.update_doc_from_data_interactively',
        lambda ctxdata, impdata, string: ctxdata.update(impdata))
    def test_with_bibtex(self):
        bibstring = """
        @article{10.1002/andp.19053221004, author = { A. Einstein },
          doi = { 10.1002/andp.19053221004 },
          issue = { 10 }, journal = { Ann. Phys. }, pages = { 891--921 },
          title = { Zur Elektrodynamik bewegter K\"{o}rper },
          type = { article },
          volume = { 322 },
          year = { 1905 },
        }
        """
        bibfile = tempfile.mktemp()
        pdf = create_random_pdf()
        with open(bibfile, 'w+') as fd:
            fd.write(bibstring)

        self.assertTrue(get_document_extension(pdf) == 'pdf')

        result = self.invoke([pdf, '--from', 'bibtex', bibfile])

        db = papis.database.get()
        docs = db.query_dict(
            dict(
                author="einstein",
                title="Elektrodynamik bewegter"
            )
        )
        self.assertTrue(len(docs) == 1)
        doc = docs[0]
        self.assertTrue(len(doc.get_files()) == 1)
        # This is the original pdf file, it should still be there
        self.assertTrue(os.path.exists(pdf))
        # and it should still be apdf
        self.assertTrue(get_document_extension(pdf) == 'pdf')
        self.assertTrue(get_document_extension(doc.get_files()[0]) == 'pdf')

    @patch('papis.utils.open_file', lambda x: None)
    @patch('papis.tui.utils.confirm', lambda x: True)
    @patch(
        'papis.utils.update_doc_from_data_interactively',
        lambda ctxdata, impdata, string: ctxdata.update(impdata))
    def test_from_yaml(self):
        yamlstring = (
            "title: The lord of the rings\n"
            "author: Tolkien\n"
        )
        yamlfile = tempfile.mktemp()
        epub = create_random_epub()
        with open(yamlfile, 'w+') as fd:
            fd.write(yamlstring)

        self.assertTrue(get_document_extension(epub) == 'epub')

        result = self.invoke([
            epub, '--from', 'yaml', yamlfile
        ])

        db = papis.database.get()
        docs = db.query_dict({"author": "Tolkien"})
        self.assertTrue(len(docs) == 1)
        doc = docs[0]
        self.assertTrue(len(doc.get_files()) == 1)
        self.assertTrue(get_document_extension(doc.get_files()[0]) == 'epub')
        # This is the original epub file, it should still be there
        self.assertTrue(os.path.exists(epub))
        # and it should still be an epub
        self.assertTrue(get_document_extension(epub) == 'epub')

    #@patch(
        #'papis.crossref.get_data',
        #lambda **x: [
            #{"author": "Kant", "doi": "1/1", "doc_url": "https://nourl"}])
    #@patch(
        #'papis.downloaders.get_downloader',
        #lambda url, downloader:
            #tests.MockDownloader(
                #bibtex_data=' ',
                #document_data='%PDF-1.5%\n'.encode()))
    #@patch('papis.utils.open_file', lambda x: None)
    #@patch(
        #'papis.utils.update_doc_from_data_interactively',
        #lambda ctxdata, impdata, string: ctxdata.update(impdata))
    #@patch('papis.utils.confirm', lambda x: True)
    #def test_from_doi(self):
        #result = self.invoke([
            #'--from', 'doi', '10.1112/plms/s2-42.1.0',
            #'--confirm', '--open'
        #])
        #self.assertTrue(result.exit_code == 0)
        #db = papis.database.get()
        #docs = db.query_dict({"author": "Kant"})
        #self.assertTrue(len(docs) == 1)
        #doc = docs[0]
        ## one file at least was retrieved
        #self.assertTrue(len(doc.get_files()) == 1)
        ## it has the pdf ending
        #self.assertTrue(len(re.split('.pdf', doc.get_files()[0])) == 2)

    @patch('papis.utils.open_file', lambda x: None)
    @patch('papis.tui.utils.confirm', lambda x: True)
    @patch(
        'papis.utils.update_doc_from_data_interactively',
        lambda ctxdata, impdata, string: ctxdata.update(impdata))
    @patch('papis.tui.utils.text_area', lambda *x, **y: True)
    def test_from_lib(self):
        newdoc = create_real_document({"author": "Lindgren"})
        self.assertEqual(newdoc['author'], 'Lindgren')
        folder = newdoc.get_main_folder()
        self.assertTrue(os.path.exists(folder))
        self.assertTrue(os.path.exists(newdoc.get_info_file()))
        result = self.invoke([
            '--confirm', '--from', 'lib', newdoc.get_main_folder(), '--open' ])
        self.assertTrue(result.exit_code == 0)
