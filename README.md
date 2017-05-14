
# Papis

## Description

Papis is a command-line based document and bibliography manager.  Its
command-line interface (*CLI*) is heavily tailored after
[Git](http://git-scm.com).


## Quick start

You have installed everything, then you can do

```
papis -h
```

To see the help, the first time that papis is run it will create a
configuration folder anf a configuration file in

```
~/.papis/config
```

There you will have already a library called papers defined with directory path
`~/Documents/papers/`. Therefore in principle you could now do the following:

```
papis -v add --from-url https://arxiv.org/abs/1211.1036
```

And this will download the paper in `https://arxiv.org/abs/1211.1036`
and also copy the relevant information of its bibliography.

You can know more about each command doing

```
papis -h
papis add -h
```

etc..

## Configuration file

Papis uses a configuration file in *INI* format. You can then have several libraries
which work independently from each other.

For example, maybe you want to have one library for papers
and the other for some miscellaneous documents.
An example for that is given below


```ini
[papers]
dir = ~/Documents/papers

[settings]
opentool = rifle
editor = vim
default = papers

[books]
dir = ~/Documents/books
gagp = git add . && git commit && git push origin master

```

## Create new library

To create a new library you just simply add to the configuration file:

```ini
#
#  Other sutff
#

[library-name]
dir = path/to/the/library/folder

#
#  Other sutff
#
```

you can then work with the library by doing

```
papis -l library-name open
```

and so on...


## Custom scripts

### General scripts

As in [git](http://git-scm.com), you can write custom scripts to include them
in the command spectrum of papis.

Imagine you want to write a script to send papers to someone via `mutt`,
you could write the following script caled `papis-mail`:

```sh
#! /usr/bin/env bash

if [[ $1 = "-h" ]]; then
  echo "Email a paper to my friend"
  exit 0
fi

folder_name=$1
zip_name="${folder_name}.zip"

papis -l ${PAPIS_LIB} export --folder --out ${folder_name}
zip -r ${zip_name} ${folder_name}

mutt -a ${zip_name}

```

Papis defines environment variables such as `PAPIS_LIB` so that external
scripts can make use of the user input.

If you have the script above in your path you can run

```
papis -h
```

and you will see that there is another command besides the default called
`mail`. Then if you type

```
papis -l mylib mail this_paper
```

this will create a folder called `this_paper` with a selection of a document,
zip it, and send it to whoever you choose to.

### Python scripts

If you use python is also very easy to control the library using the `papis`
library. The following is an example illustrating the basics.
The script below gets all the documents from the `papers` library
and deletes the `url` from the document information:

```python
#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import papis.utils

# Get the user configuration, where all the libraries are defined
# You can access then for example the "papers" library path like a pythonic
# dict, i.e., config["papers"]["dir"]
#
config = papis.utils.getConfiguration()

# Get the documents. This returns a list of Document objects, which
# are also similar to python's dicts but with more methods.
#
docs = papis.utils.getFilteredDocuments(config["papers"]["dir"])

for doc in docs:
    if "url" in doc.keys():
        #
        # You can access the info of the document by either
        # doing doc.title or doc["title"].
        #
        print(doc.title)
        del doc["url"]
        print(doc.keys())
        print(doc.toDict())
        # Save the doc
        doc.save()
```

## Installation

### Through pip

Probably the easiest way of installing the package is using `pip`:

```
pip3 install git+git://github.com/alejandrogallo/papis.git
```

or if you want to install it locally

```
pip3 install --user git+git://github.com/alejandrogallo/papis.git
```

### Using the `Makefile`

If you want to install it globally, just hit

```
sudo make install-deps
sudo make install
```

If you want to install it locally:
```
make install-deps-local
make install-local
```

If you want to install it locally and have the development version:
```
make install-deps-local
make install-dev-local
```

And to see the available targets hit:

```
make help
```

Also you need the following packages:
```
python3-readline
python3-ncurses
```
