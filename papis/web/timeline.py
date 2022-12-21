"""
This file creates a timeline of documents with year and possibly month
information.
"""
from typing import Any, Dict, Sequence

import dominate.tags as t
import dominate.util as tu

import papis.document

import papis.web.paths as wp


def widget(documents: Sequence[Dict[str, Any]],
           libname: str,
           _id: str) -> None:
    """
    Creates a div element and a script with the timeline API used.
    """
    t.div(id=_id, style="width: 100%; height: 300px;")

    def _make_text(_d: Dict[str, Any]) -> str:
        _text = papis.document.describe(_d)
        _href = wp.doc_server_path(libname, _d)
        if _href:
            return (r"<a href='{}'>{}<i class='fa fa-check'></i></a>"
                    .format(_href, _text))
        return _text

    json_data = [{"text": {"text": _make_text(d)},
                  "start_date": {"year": d["year"],
                                 "month": d["month"]
                                 if "month" in d
                                 and isinstance(d["month"], int)
                                 else 1}}
                 for d in documents if "year" in d]
    t.script(tu.raw("""
    new TL.Timeline('{}',
                    {{'events': {} }},
                    {{
                      timenav_height_percentage: 80,
                      width: "100%"
                    }})
    """.format(_id, json_data)))
