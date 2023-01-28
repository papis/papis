all: bash fish zsh

help: 			## Show this help
	@echo -e "Specify a command. The choices are:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-12s\033[m %s\n", $$1, $$2}'
	@echo ""
.PHONY: help

bash:			## Generate bash completions
	@mkdir -p click/bash
	_PAPIS_COMPLETE=bash_source papis >| click/bash/papis.bash
.PHONY: bash

fish:			## Generate fish completions
	@mkdir -p click/fish
	_PAPIS_COMPLETE=fish_source papis >| click/fish/papis.fish
.PHONY: fish

zsh:			## Generate zsh completions
	@mkdir -p click/zsh
	_PAPIS_COMPLETE=zsh_source papis >| click/zsh/_papis
.PHONY: zsh
