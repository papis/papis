import dominate.tags as t


def navbar(libname: str) -> t.html_tag:

    def _li(title: str, href: str, active: bool = False) -> t.html_tag:
        with t.li(cls="nav-item") as result:
            t.a(title,
                cls="nav-link" + (" active" if active else ""),
                aria_current="page",
                href=href)
        return result

    with t.nav(cls="navbar navbar-expand-md navbar-light bg-light") as nav:
        with t.div(cls="container-fluid"):

            t.a("Papis", href="#", cls="navbar-brand")

            but = t.button(cls="navbar-toggler",
                           type="button",
                           data_bs_toggle="collapse",
                           data_bs_target="#navbarNav",
                           aria_controls="navbarNav",
                           aria_expanded="false",
                           aria_label="Toggle navigation")
            with but:
                t.span(cls="navbar-toggler-icon")

            with t.div(id="navbarNav"):
                t.attr(cls="collapse navbar-collapse")
                with t.ul(cls="navbar-nav"):
                    _li("Search", "/library/{libname}".format(libname=libname),
                        active=True)
                    _li("All",
                        "/library/{libname}/all".format(libname=libname))
                    _li("Tags",
                        "/library/{libname}/tags".format(libname=libname))
                    _li("Libraries", "/libraries")

    return nav
