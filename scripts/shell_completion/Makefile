.PHONY: zsh

all: dist/bash-completion.sh

dist/bash-completion.sh:
	./tools/bash.sh

zsh:
	# run from a zsh shell
	mkdir -p click/zsh/
	echo "#compdef papis" > click/zsh/_papis
	_PAPIS_COMPLETE=source_zsh papis >> click/zsh/_papis

clean:
	rm -rf dist
