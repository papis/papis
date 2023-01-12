.PHONY: bash zsh fish

all: bash fish zsh

bash:
	mkdir -p click/bash
	_PAPIS_COMPLETE=bash_source papis >| click/bash/papis.bash

fish:
	mkdir -p click/fish
	_PAPIS_COMPLETE=fish_source papis >| click/fish/papis.fish

zsh:
	mkdir -p click/zsh
	_PAPIS_COMPLETE=zsh_source papis >| click/zsh/_papis
