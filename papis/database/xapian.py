import os
import sys
import xapian

from source import Sources
from documents import Documents, Document

import papis.utils
import papis.database.base
import papis.database.cache

class Database(papis.database.base.Database):

    # http://xapian.org/docs/omega/termprefixes.html
    BOOLEAN_PREFIX_INTERNAL = {
        # FIXME: use this for doi?
        #'url': 'U',
        'file': 'P',

        # FIXME: use this for doc mime type
        'type': 'T',
        }

    BOOLEAN_PREFIX_EXTERNAL = {
        'id': 'Q',
        'key': 'XBIB|',
        'source': 'XSOURCE|',
        'tag': 'K',
        'year': 'Y',
        'y': 'Y',
        }

    PROBABILISTIC_PREFIX = {
        'title': 'S',
        't': 'S',
        'author': 'A',
        'a': 'A',
        }

    # http://xapian.org/docs/facets
    NUMBER_VALUE_FACET = {
        'year': 0,
        'y': 0,
        }

    # FIXME: need to set the following value fields:
    # publication date
    # added date
    # modified date

    def get_backend_name(self):
        return 'xapian'

    def _find_prefix(self, name):
        if name in self.BOOLEAN_PREFIX_INTERNAL:
            return self.BOOLEAN_PREFIX_INTERNAL[name]
        if name in self.BOOLEAN_PREFIX_EXTERNAL:
            return self.BOOLEAN_PREFIX_EXTERNAL[name]
        if name in self.PROBABILISTIC_PREFIX:
            return self.PROBABILISTIC_PREFIX[name]

    def _find_facet(self, name):
        if name in self.NUMBER_VALUE_FACET:
            return self.NUMBER_VALUE_FACET[name]

    def _make_source_prefix(self, source):
        return 'X%s|' % (source.upper())

    ########################################

    def __init__(self, library=None, writable=False, create=False, force=False):
        # xapers root
        self.logger = logging.getLogger('db:xapian')
        self.initialize()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.xapian.close()

    def reopen(self):
        self.xapian.reopen()

    def __contains__(self, docid):
        try:
            self.xapian.get_document(docid)
            return True
        except xapian.DocNotFoundError:
            return False

    def __getitem__(self, docid):
        if type(docid) not in [int, long]:
            raise TypeError("docid must be an int")
        xapian_doc = self.xapian.get_document(docid)
        return Document(self, xapian_doc)

    ########################################

    # generate a new doc id, based on the last availabe doc id
    def _generate_docid(self):
        return self.xapian.get_lastdocid() + 1

    ########################################

    # return a list of terms for prefix
    def _term_iter(self, prefix=None):
        term_iter = iter(self.xapian)
        if prefix:
            plen = len(prefix)
            term = term_iter.skip_to(prefix)
            if not term.term.startswith(prefix):
                return
            yield term.term[plen:]
        for term in term_iter:
            if prefix:
                if not term.term.startswith(prefix):
                    break
                yield term.term[plen:]
            else:
                yield term.term

    def term_iter(self, name=None):
        """Iterator over all terms in the database.

        If a prefix is provided, will iterate over only the prefixed
        terms, and the prefix will be removed from the returned terms.

        """
        prefix = None
        if name:
            prefix = self._find_prefix(name)
            if not prefix:
                prefix = name
        return self._term_iter(prefix)

    def get_sids(self):
        """Get all sources in database."""
        sids = []
        # FIXME: do this more efficiently
        for source in self.term_iter('source'):
            for oid in self._term_iter(self._make_source_prefix(source)):
                sids.append('%s:%s' % (source, oid))
        return sids

    ########################################

    # search for documents based on query string
    def _search(self, query_string, limit=None):
        enquire = xapian.Enquire(self.xapian)

        if query_string == "*":
            query = xapian.Query.MatchAll
        else:
            # parse the query string to produce a Xapian::Query object.
            query = self.query_parser.parse_query(query_string)

        if os.getenv('XAPERS_DEBUG_QUERY'):
            print >>sys.stderr, "query string:", query_string
            print >>sys.stderr, "final query:", query

        # FIXME: need to catch Xapian::Error when using enquire
        enquire.set_query(query)

        # set order of returned docs as newest first
        # FIXME: make this user specifiable
        enquire.set_docid_order(xapian.Enquire.DESCENDING)

        if limit:
            mset = enquire.get_mset(0, limit)
        else:
            mset = enquire.get_mset(0, self.xapian.get_doccount())

        return mset

    def search(self, query_string, limit=0):
        """Search for documents in the database."""
        mset = self._search(query_string, limit)
        return Documents(self, mset)

    def count(self, query_string):
        """Count documents matching search terms."""
        return self._search(query_string).get_matches_estimated()

    def _doc_for_term(self, term):
        enquire = xapian.Enquire(self.xapian)
        query = xapian.Query(term)
        enquire.set_query(query)
        mset = enquire.get_mset(0, 2)
        # FIXME: need to throw an exception if more than one match found
        if mset:
            return Document(self, mset[0].document)
        else:
            return None

    def doc_for_path(self, path):
        """Return document for specified path."""
        term = self._find_prefix('file') + path
        return self._doc_for_term(term)

    def doc_for_source(self, sid):
        """Return document for source id string."""
        source, oid = sid.split(':', 1)
        term = self._make_source_prefix(source) + oid
        return self._doc_for_term(term)

    def doc_for_bib(self, bibkey):
        """Return document for bibtex key."""
        term = self._find_prefix('key') + bibkey
        return self._doc_for_term(term)

    ########################################

    def replace_document(self, docid, doc):
        """Replace (sync) document to database."""
        self.xapian.replace_document(docid, doc)

    def delete_document(self, docid):
        """Delete document from database."""
        self.xapian.delete_document(docid)

    def get_id_key(self):
        """Get the unique key identifier name of the documents in the database

        :returns: key identifier
        :rtype:  str
        """
        return 'xapian_id_'

    def get_id_value(self, document):
        """Get the value that is stored in the unique key identifier
        of the documents in the database. In the case of papis this is
        just the path of the documents.

        :param document: Papis document
        :type  document: papis.document.Document
        :returns: Path for the document
        :rtype:  str
        """
        return document.get_main_folder()


    def do_indexing(self):
        """Restore a database from an existing root."""
        log = False
        docdirs = papis.utils.get_folders(self.get_dir())
        docdirs.sort()
        documents = papis.database.cache.folders_to_documents(docdirs)
        for doc in documents:
            self.add(doc)
            doc.sync()

    def add(self, document):
        xdoc = xapian.Document()
        xdoc.add_term("{}{}".format(self._find_prefix('id'), self.docid))

    def get_cache_dir(self):
        """Get general directory to store xapian indexes.

        :returns: Full path to xapian cache home directory
        :rtype:  str
        """
        path = os.path.join(
            papis.database.cache.get_cache_home(),
            'xapian'
        )
        # self.logger.debug('Cache dir %s' % path)
        return path

    def initialize(self):
        """Function to be called everytime a database object is created.
        It checks if an index exists, if not, it creates one and
        indexes the library.
        """
        self.root = self.get_cache_dir()
        # db directory
        index_path = self.get_index_dir()

        # directory initialization
        if not os.path.exists(index_path):
            os.makedirs(index_path)

        #self.xapian = xapian.Database(index_path)
        self.xapian = xapian.WritableDatabase(
            index_path, xapian.DB_CREATE_OR_OPEN
        )
        stemmer = xapian.Stem("english")

        # The Xapian TermGenerator
        # http://trac.xapian.org/wiki/FAQ/TermGenerator
        self.term_gen = xapian.TermGenerator()
        self.term_gen.set_stemmer(stemmer)

        # The Xapian QueryParser
        self.query_parser = xapian.QueryParser()
        self.query_parser.set_database(self.xapian)
        self.query_parser.set_stemmer(stemmer)
        self.query_parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
        self.query_parser.set_default_op(xapian.Query.OP_AND)

        # add boolean internal prefixes
        for name, prefix in self.BOOLEAN_PREFIX_EXTERNAL.iteritems():
            self.query_parser.add_boolean_prefix(name, prefix)

        # add probabalistic prefixes
        for name, prefix in self.PROBABILISTIC_PREFIX.iteritems():
            self.query_parser.add_prefix(name, prefix)

        # add value facets
        for name, facet in self.NUMBER_VALUE_FACET.iteritems():
            self.query_parser.add_valuerangeprocessor(
                xapian.NumberValueRangeProcessor(facet, name+':')
                )

        # register known source prefixes
        # FIXME: can we do this by just finding all XSOURCE terms in
        #        db?  Would elliminate dependence on source modules at
        #        search time.
        for source in Sources():
            name = source.name
            self.query_parser.add_boolean_prefix(name, self._make_source_prefix(name))

    def get_index_dir(self):
        """Get the directory inside `get_cache_dir` to store the index.
        :returns: Full path to index dir
        :rtype:  str
        """
        path = os.path.expanduser(
            os.path.join(
                self.get_cache_dir(),
                papis.database.cache.get_name(self.get_dir())
            )
        )
