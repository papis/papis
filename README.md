
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

# Quick start #

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

# Create new library #

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

Also you need the following packages:
```
python3-readline
python3-ncurses
```
