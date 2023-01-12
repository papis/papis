.PHONY: zsh

all: dist/bash-completion.sh

dist/bash-completion.sh:
	./tools/bash.sh

zsh:
	mkdir -p click/zsh
	_PAPIS_COMPLETE=zsh_source papis >| click/zsh/_papis

clean:
	rm -rf dist
