import papis.downloaders

from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource


def test_1():
    url = "https://projecteuclid.org/journals/advances-in-differential-equations/volume-19/issue-3_2f_4/An-analysis-of-the-renormalization-group-method-for-asymptotic-expansions/ade/1391109086.short"      # noqa: E501

    downs = papis.downloaders.get_matching_downloaders(url)
    down, = (d for d in downs if d.name == "projecteuclid")

    # import os
    # with open(os.path.join(
    #         os.path.dirname(__file__),
    #         "resources", "projecteuclid_1.html"), "w") as f:
    #     f.write(down._get_body().decode())

    with patch.object(down, "_get_body",
            lambda: get_resource("projecteuclid_1.html")):
        with patch.object(down, "download_document", lambda: None):
            down.fetch()

            # with open(os.path.join(
            #         os.path.dirname(__file__),
            #         "resources", "projecteuclid_1_out.json"), "w+") as f:
            #     import json
            #     json.dump(down.ctx.data, f)

            ref_data = get_json_resource("projecteuclid_1_out.json")
            assert down.ctx.data == ref_data
