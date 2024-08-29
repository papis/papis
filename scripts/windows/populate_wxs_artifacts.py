"""Add all components (files) and directories generated by pyinstaller in
dist/papis/_internal into the XML manifest that is used to create the MSI."""

import hashlib
import os
import uuid
from typing import Optional


def get_id(*path_components: str) -> str:
    """Create an element ID based on the WiX constraints.

    The allowed characters, as of version 4.0.5, can be found
    `here <https://github.com/wixtoolset/wix/blob/289c93dc24ba203903d9c8a6261a68de95d3d911/src/wix/WixToolset.BuildTasks/ToolsCommon.cs#L18>`__.
    Largely, the identifier should be 72 chars or less, contain ``[a-zA-Z0-9_-]``,
    and start with an underscore or a letter.

    This function uses the MD5 hash of the joined *path_components* as the identifier.
    This is guaranteed to be less than 72 characters and only uses letters and
    numbers.
    """  # noqa: E501

    # NOTE: this needs to do an `os.path.join` so that the hash of
    # `get_id("root", "subdir")` matches the hash of `get_id("root/subdir")`
    result = os.path.join(*path_components)

    # NOTE: this uses MD5 instead of the builtin hash to have a stable result
    result = hashlib.md5(result.encode()).hexdigest()

    return f"_{result}"


def render_template(template: str,
                    outfile: str, *,
                    version: Optional[str] = None) -> None:
    from xml.etree import ElementTree

    if version is None:
        from papis import __version__
        version = __version__

    ElementTree.register_namespace("", "http://wixtoolset.org/schemas/v4/wxs")
    ElementTree.register_namespace("ui", "http://wixtoolset.org/schemas/v4/wxs/ui")

    wxs_tree = ElementTree.parse(template)
    wxs_root = wxs_tree.getroot()

    ns = {"main": "http://wixtoolset.org/schemas/v4/wxs"}
    component, = wxs_root.findall(".//main:Directory[@Id='INSTALLFOLDER']",
                                  namespaces=ns)
    package, = wxs_root.findall(".//main:Package", namespaces=ns)

    # NOTE: path is controlled by pyinstaller
    root_dir = os.path.join("dist", "papis", "_internal")
    if not os.path.exists(root_dir):
        print(f"PyInstaller distribution directory does not exist: '{root_dir}'")

    if os.path.isabs(root_dir):
        print(f"Root directory is an absolute path: '{root_dir}'")

    directories = ElementTree.SubElement(
        component, "Directory",
        Name="_internal",
        Id=get_id(root_dir)
    )
    component_group = ElementTree.SubElement(
        package, "ComponentGroup",
        Id="_internal"
    )

    package.attrib["Version"] = version
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            relpath = os.path.relpath(dirpath, root_dir)
            parent_path = os.path.dirname(relpath)
            if parent_path:
                parent_element_id = get_id(root_dir, parent_path)
                parent_element, = directories.findall(
                    f".//Directory[@Id='{parent_element_id}']"
                )
            else:
                parent_element = directories

            ElementTree.SubElement(
                parent_element, "Directory",
                Name=dirname,
                Id=get_id(dirpath, dirname)
            )

        if filenames:
            for filename in filenames:
                component = ElementTree.SubElement(
                    component_group, "Component",
                    Guid=str(uuid.uuid4()),
                    Id=f"c{get_id(dirpath, filename)}",
                    Directory=get_id(dirpath),
                )
                ElementTree.SubElement(
                    component, "File",
                    KeyPath="yes",
                    Source=os.path.join(dirpath, filename)
                )

    wxs_tree.write(outfile, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("template", help="path to a template file")
    parser.add_argument("-o", "--outfile", default=None,
                        help="output file generated from the template")
    parser.add_argument("-v", "--version", default=None,
                        help="Papis version to insert into the template")
    args = parser.parse_args()

    outfile = args.outfile
    if outfile is None:
        outfile = os.path.join(os.path.dirname(args.template), "papis.wxs")

    render_template(args.template, outfile, version=args.version)
