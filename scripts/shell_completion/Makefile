
all: dist/bash-completion.sh

dist/bash-completion.sh:
	./tools/bash.sh

zsh:
	# run from a zsh shell
	echo "#compdef papis" > click/papis.zsh
	_PAPIS_COMPLETE=source_zsh papis >> click/papis.zsh

clean:
	rm -rf dist
