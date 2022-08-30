import papis.downloaders

from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource


def test_1():
    url = "https://projecteuclid.org/journals/advances-in-differential-equations/volume-19/issue-3_2f_4/An-analysis-of-the-renormalization-group-method-for-asymptotic-expansions/ade/1391109086.short"      # noqa: E501
    # biburl = "https://projecteuclid.org/citation/download/citation-ade19_245.bib"

    downs = papis.downloaders.get_matching_downloaders(url)
    down, = (d for d in downs if d.name == "projecteuclid")

    # import os
    # with open(os.path.join(
    #         os.path.dirname(__file__),
    #         "resources", "projecteuclid_1.bib"), "w") as f:
    #     down.fetch()
    #     f.write(down.get_bibtex_data())

    with patch.object(
            down, "get_bibtex_data",
            lambda: get_resource("projecteuclid_1.bib")):
        down.fetch()

        # with open(os.path.join(
        #         os.path.dirname(__file__),
        #         "resources", "projecteuclid_1_out.json"), "w+") as f:
        #     import json
        #     json.dump(down.ctx.data, f)

        ref_data = get_json_resource("projecteuclid_1_out.json")
        assert down.ctx.data == ref_data
