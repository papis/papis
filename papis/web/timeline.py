from typing import Any, Dict, Sequence

import dominate.tags as t
import dominate.util as tu

import papis.api
import papis.cli
import papis.config
import papis.document
import papis.commands.add
import papis.commands.update
import papis.commands.export
import papis.commands.doctor
import papis.crossref
import papis.notes
import papis.citations

import papis.web.paths as wp


def widget(documents: Sequence[Dict[str, Any]],
           libname: str,
           _id: str) -> None:
    t.div(id=_id, style="width: 100%; height: 300px;")

    def _make_text(d: Dict[str, Any]) -> str:
        _text = papis.document.describe(d)
        _href = wp.doc_server_path(libname, d)
        return r"<a href='{}'>{}</a>".format(_href, _text)

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
