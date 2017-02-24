import re
import sys
import logging
import os

logger = logging.getLogger("bibtex")

bibtexTypes = [
  "article",
  "book",
  "booklet",
  "conference",
  "inbook",
  "incollection",
  "inproceedings",
  "manual",
  "mastersthesis",
  "misc",
  "phdthesis",
  "proceedings",
  "techreport",
  "unpublished"
]

bibtexKeys = [
  "address",
  "annote",
  "author",
  "booktitle",
  "chapter",
  "crossref",
  "edition",
  "editor",
  "howpublished",
  "institution",
  "journal",
  "key",
  "month",
  "note",
  "number",
  "organization",
  "pages",
  "publisher",
  "school",
  "series",
  "title",
  "volume",
  "year"
  ]

def bibtexToDict(bibtex):
    """
    Convert bibtex file to dict
    { type: "article ...", "ref": "example1960etAl", author:" ..."}

    :bibtex: TODO
    :returns: TODO

    """
    global logger
    result = dict()
    if os.path.exists(bibtex):
        fd = open(bibtex, "r")
        logger.debug("Reading in file %s"%bibtex)
        text = fd.read()
    else:
        text = bibtex
    logger.debug("Removing comments...")
    text = re.sub(r"%.*", "", text)
    logger.debug("Removing empty lines...")
    text = re.sub(r"^\s*$", "", text)
    logger.debug("Removing newlines...")
    text = re.sub(r"\n", "", text)
    logger.debug("Parsing document type and reference")
    type_ref_re = re.compile(r"\s*@(\w+){([^,]+),")
    match = re.match(type_ref_re, text)
    text = re.sub(type_ref_re, "", text)
    if not match:
        logger.error("Type and reference of the bibtex file could not be parsed")
        sys.exit(1)
    result["type"] = match.group(1)
    result["ref"]  = match.group(2)
    for key in result.keys():
        logger.debug(" [%s] = %s"%(key,result[key]))
    key_val_re = re.compile(r"\s*(\w+)\s*=\s*{(.*)\s*,?")
    for line in re.sub(r"}\s*,?", "\n", text).split("\n"):
        match = re.match(key_val_re, line)
        if match:
            key = match.group(1)
            val = re.sub(r"\s+"," ",match.group(2))
            result[key.lower()] = val
            logger.debug(" [%s] = %s"%(key,val))
    return result

