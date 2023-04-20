import sys
import os
from typing import Dict, Any  # noqa: ignore


def get_default_opener() -> str:
    """Get the default file opener for the current system
    """
    if sys.platform.startswith("darwin"):
        return "open"
    if os.name == "nt":
        return "start"
    return "xdg-open"


settings = {
    "local-config-file": ".papis.config",
    "database-backend": "papis",
    "default-query-string": ".",
    "sort-field": None,
    "sort-reverse": False,

    "opentool": get_default_opener(),
    "dir-umask": 0o755,
    "browser": os.environ.get("BROWSER") or get_default_opener(),
    "picktool": "papis",
    "mvtool": "mv",
    "editor": os.environ.get("EDITOR")
                        or os.environ.get("VISUAL")
                        or get_default_opener(),
    "notes-name": "notes.tex",
    "notes-template": "",
    "use-cache": True,
    "cache-dir": None,
    "use-git": False,

    "add-confirm": False,
    "add-folder-name": "",
    "add-subfolder": "",
    "add-file-name": None,
    "add-interactive": False,
    "add-edit": False,
    "add-open": False,
    "add-fetch-citations": False,

    # papis-doctor configuration
    "doctor-default-checks": ["files", "keys-exist", "duplicated-keys"],
    "doctor-keys-exist-keys": ["title", "author", "ref"],
    "doctor-duplicated-keys-keys": ["ref"],
    "doctor-html-codes-keys": ["title", "author", "abstract", "journal"],
    "doctor-html-tags-keys": ["title", "author", "abstract", "journal"],
    "doctor-key-type-check-keys": [("year", "int"),
                                   ("month", "int"),
                                   ("files", "list"),
                                   ("notes", "str"),
                                   ("author_list", "list")],

    # papis-serve configuration
    "serve-user-css": [],
    "serve-user-js": [],
    "serve-font-awesome-css": [("https://cdnjs.cloudflare.com/ajax/"
                               "libs/font-awesome/6.2.1/css/all.min.css"),
                               ("https://cdnjs.cloudflare.com/ajax/"
                                "libs/font-awesome/6.2.1/css/brands.min.css"),
                               ("https://cdnjs.cloudflare.com/ajax/"
                                "libs/font-awesome/6.2.1/css/solid.min.css"),
                               ],
    "serve-bootstrap-css": ("https://cdn.jsdelivr.net/npm/"
                            "bootstrap@5.1.1/dist/css/bootstrap.min.css"),
    "serve-bootstrap-js": ("https://cdn.jsdelivr.net/npm/"
                           "bootstrap@5.1.1/dist/js/bootstrap.bundle.min.js"),
    "serve-jquery-js": "https://code.jquery.com/jquery-3.6.0.min.js",
    "serve-jquery.dataTables-css": ("https://cdn.datatables.net/"
                                    "v/bs5/dt-1.13.1/kt-2.8.0/"
                                    "sc-2.0.7/sb-1.4.0/datatables.min.css"),
    "serve-jquery.dataTables-js": ("https://cdn.datatables.net/"
                                   "v/bs5/dt-1.13.1/kt-2.8.0/"
                                   "sc-2.0.7/sb-1.4.0/datatables.min.js"),
    "serve-katex-css": ("https://cdn.jsdelivr.net/npm/"
                        "katex@0.16.4/dist/katex.min.css"),
    "serve-katex-js": ("https://cdn.jsdelivr.net/npm/"
                       "katex@0.16.4/dist/katex.min.js"),
    "serve-katex-auto-render-js":
    ("https://cdn.jsdelivr.net/npm/"
     "katex@0.16.4/dist/contrib/auto-render.min.js"),

    "serve-ace-urls": [("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/ace.min.js"),
                       ("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/mode-yaml.min.js"),
                       ("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/mode-bibtex.min.js"),
                       ("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/mode-markdown.min.js"),
                       ("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/mode-latex.min.js"),
                       ("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/ext-textarea.min.js"),
                       ("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/ext-settings_menu.min.js"),
                       ("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/ext-keybinding_menu.min.js"),
                       ("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/keybinding-vim.min.js"),
                       ("https://cdnjs.cloudflare.com/ajax/libs/ace/"
                        "1.14.0/keybinding-emacs.min.js"),
                       ],

    "serve-empty-query-get-all-documents": False,

    # citations configuration
    "citations-file-name": "citations.yaml",
    "cited-by-file-name": "cited-by.yaml",

    # timeline options
    "serve-timeline-max": 500,
    "serve-enable-timeline": False,
    "serve-timeline-js": ("https://cdn.knightlab.com/libs/timeline3/"
                          "latest/js/timeline.js"),
    "serve-timeline-css": ("https://cdn.knightlab.com/libs/timeline3/"
                           "latest/css/timeline.css"),

    "browse-key": "url",
    "browse-query-format": "{doc[title]} {doc[author]}",
    "search-engine": "https://duckduckgo.com",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)",
    "scripts-short-help-regex": ".*papis-short-help: *(.*)",
    "info-name": "info.yaml",
    "doc-url-key-name": "doc_url",

    "open-mark": False,
    "mark-key-name": "marks",
    "mark-format-name": "mark",
    "mark-header-format": "{mark[name]} - {mark[value]}",
    "mark-match-format": "{mark[name]} - {mark[value]}",
    "mark-opener-format": get_default_opener(),

    "file-browser": get_default_opener(),
    "bibtex-unicode": False,
    "bibtex-journal-key": "journal",
    "bibtex-export-zotero-file": False,
    "bibtex-ignore-keys": "[]",
    "extra-bibtex-keys": "[]",
    "extra-bibtex-types": "[]",
    "default-library": "papers",
    "format-doc-name": "doc",
    "match-format":
        "{doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}",
    "header-format-file": None,
    "header-format": (
        "<ansired>{doc.html_escape[title]}</ansired>\n"
        " <ansigreen>{doc.html_escape[author]}</ansigreen>\n"
        "  <ansiblue>({doc.html_escape[year]})</ansiblue> "
        "[<ansiyellow>{doc.html_escape[tags]}</ansiyellow>]"
    ),

    "formater": "python",
    "time-stamp": True,
    "info-allow-unicode": True,
    "ref-format": "{doc[title]:.15} {doc[author]:.6} {doc[year]}",
    "multiple-authors-separator": " and ",
    "multiple-authors-format": "{au[family]}, {au[given]}",
    "document-description-format": "{doc[title]} - {doc[author]}",
    "unique-document-keys": "['doi','ref','isbn','isbn10','url','doc_url']",

    "whoosh-schema-fields": "['doi']",
    "whoosh-schema-prototype":
    "{\n"
    '"author": TEXT(stored=True),\n'
    '"title": TEXT(stored=True),\n'
    '"year": TEXT(stored=True),\n'
    '"tags": TEXT(stored=True),\n'
    "}",

    # fzf options
    "fzf-binary": "fzf",
    "fzf-extra-flags": ["--ansi", "--multi", "-i"],
    "fzf-extra-bindings": ["ctrl-s:jump"],
    "fzf-header-format": ("{c.Fore.MAGENTA}"
                          "{doc[title]:<70.70}"
                          "{c.Style.RESET_ALL}"
                          " :: "
                          "{c.Fore.CYAN}"
                          "{doc[author]:<20.20}"
                          "{c.Style.RESET_ALL}"
                          "{c.Fore.YELLOW}"
                          "«{doc[year]:4}»"
                          "{c.Style.RESET_ALL}"
                          ":{doc[tags]}"),

    # importer / downloader options
    "downloader-proxy": None,
    "isbn-service": "openl",
}  # type: Dict[str, Any]
