# NOTE: the Hayagriva YAML format is described at
#   https://github.com/typst/hayagriva/blob/main/docs/file-format.md

HAYAGRIVA_TYPES = frozenset({
    "article", "chapter", "entry", "anthos", "report", "thesis", "web",
    "scene", "artwork", "patent", "case", "newspaper", "legislation",
    "manuscript", "tweet", "misc", "periodical", "proceedings",
    "book", "blog", "reference", "conference", "anthology", "repository",
    "thread", "video", "audio", "exhibition",
})

HAYAGRIVA_PARENT_TYPES = {
    "article": "periodical",
    "chapter": "book",
    "entry": "reference",
    "anthos": "anthology",
    "web": "web",
    "scene": "video",
    "artwork": "exhibition",
    "legislation": "anthology",
    "tweet": "tweet",
    "video": "video",
    "audio": "audio",
}

# NOTE: these are mostly taken from
#   https://github.com/typst/hayagriva/blob/main/tests/data/basic.yml
# as there does not seem to be any official list of what goes in the entry and
# what goes in the parent (some fields can even repeat, which is not supported
# by papis)

HAYAGRIVA_TYPE_PARENT_KEYS = {
    "article": frozenset({
        "date", "edition", "isbn", "issn", "issue", "journal", "location",
        "organization", "publisher", "volume",
    }),
    "chapter": frozenset({
        "journal", "author", "volume", "volume-total", "isbn", "issn",
        "page-total", "date",
    }),
    "entry": frozenset({"journal"}),
    "anthos": frozenset({
        "journal", "volume", "date", "isbn", "location", "publisher",
        "editor",
    }),
}

# NOTE: only types that are different are stored
# NOTE: keep in sync with papis.bibtex.bibtex_types
BIBTEX_TO_HAYAGRIVA_TYPE_MAP = {
    # regular types (Section 2.1.1)
    # "article": "article",
    # "book": "book",
    "mvbook": "book",
    "inbook": "chapter",
    "bookinbook": "anthos",
    "suppbook": "chapter",
    "booklet": "book",
    "collection": "anthology",
    "mvcollection": "anthology",
    "incollection": "anthos",
    "suppcollection": "anthos",
    "dataset": "misc",
    "manual": "report",
    # "misc": "misc",
    "online": "web",
    # "patent": "patent",
    # "periodical": "periodical",
    "suppperiodical": "periodical",
    # "proceedings": "proceedings",
    "mvproceedings": "article",
    "inproceedings": "article",
    "reference": "reference",
    "mvreference": "reference",
    "inreference": "reference",
    "report": "report",
    # "set": "misc",
    "software": "misc",
    # "thesis": "thesis",
    "unpublished": "manuscript",
    # "xdata",
    # "custom[a-f]",
    # non-standard types (Section 2.1.3)
    # "artwork": "artwork",
    # "audio": "audio",
    # "bibnote": "misc",
    "commentary": "misc",
    "image": "misc",
    "jurisdiction": "case",
    # "legislation": "legislation",
    "legal": "legislation",
    "letter": "misc",
    "movie": "video",
    "music": "audio",
    "performance": "scene",
    "review": "article",
    "standard": "article",
    # "video": "video",
    # type aliases (Section 2.1.2)
    "conference": "conference",
    "electronic": "web",
    "mastersthesis": "thesis",
    "phdthesis": "thesis",
    "techreport": "report",
    "www": "web",
}
