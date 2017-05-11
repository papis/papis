
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

[settings]
opentool = rifle
editor = vim
default = papers

[books]
dir = ~/Documents/books
gagp = git add . && git commit && git push origin master

```

# Installation #

Just use the Makefile:

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
