import re

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

def bibtexToDict(bibtexFile):
    """
    Convert bibtex file to dict
    { type: "article ...", "ref": "example1960etAl", author:" ..."}

    :bibtexFile: TODO
    :returns: TODO

    """
    fd = open(bibtexFile, "r")
    result = dict()
    text = fd.read()
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\n", "", text)
    type_ref_re = re.compile(r"\s*@(\w+){([\w\-_.]*)\s*,")
    match = re.match(type_ref_re, text)
    text = re.sub(type_ref_re, "", text)
    result["type"] = match.group(1)
    result["ref"]  = match.group(2)
    print("~"*4+"BEGIN"+"~"*4)
    print(match.group(1))
    print(match.group(2))
    key_val_re = re.compile(r"\s*(\w+)\s*=\s*{([^}])}\s*,?")
    while match:
        match = re.match(key_val_re, text)
        text = re.subn(key_val_re, "", text, count=0)[0]
        print("+"*20)
        print(match)
        print("+"*20)
        print(text)
    # for line in fd:
        # m = re.match(r"\s*@([a-zA-Z]+){([0-9a-zA-Z\-_.]*)\s*,\s*", line)
        # if m:
            # result["type"] = m.group(1)
            # result["ref"]  = m.group(2)
        # m = re.match(r"\s*,?\s*([0-9a-zA-Z\-_]*)\s*=\s*{(.*)}\s*,?\s*", line)
        # if m:
            # result[m.group(1)] = m.group(2)
    return result

