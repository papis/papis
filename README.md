
# Papis

## Description

Papis is a command-line based document and bibliography manager.  Its
command-line interface (*CLI*) is heavily tailored after
[Git](http://git-scm.com).


## Configuration file

Papis uses a configuration file in *INI* format. You can then have several libraries
which work independently from each other.

For example, maybe you want to have one library for papers
and the other for some miscellaneous documents.
An example for that is given below


```ini
[papers]
dir = ~/Documents/papers
sync = cd $dir; git pull origin master

[settings]
viewer = rifle
editor = vim
default = papers

[misc]
dir = ~/Documents/misc
```
