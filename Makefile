all: help

help: 								## Show this help
	@echo -e "Specify a command. The choices are:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[m %s\n", $$1, $$2}'
	@echo ""
.PHONY: help

shell-completion:					## Generate shell completion scripts
	make -C scripts/shell_completion
.PHONY: shell_completion

update-authors:						## Generate AUTHORS file from git commits
	git shortlog -s -e -n | \
		sed -e "s/\t/  /" | \
		sed -e "s/^\s*//" > \
		AUTHORS
.PHONY: update-authors

tags:								## Generate ctags for main codebase
	ctags -f tags \
		--recurse=yes \
		--tag-relative=yes \
		--fields=+l \
		--kinds-python=-i \
		--language-force=python \
		papis
.PHONY: tags

doc:								## Generate the documentation in doc/
	cd doc && make html SPHINXOPTS="-W --keep-going -n"
	@echo ""
	@echo -e "\e[1;32mRun '$$BROWSER doc/build/html/index.html' to see the docs\e[0m"
	@echo ""
.PHONY: doc

pytest:								## Run pytest tests and doctests
	python -m pytest papis tests

flake8:								## Run flake8 (style checks)
	python -m flake8 papis tests examples

mypy:								## Run mypy (type annotations)
	python -m mypy papis

ci-install:							## Install dependencies like on the CI
	bash tools/ci-install.sh
.PHONY: ci-install

ci-test:							## Run tests like on the CI
	bash tools/ci-run-test.sh
.PHONY: ci-test

ci-lint:							## Run linting like on the CI
	bash tools/ci-run-lint.sh
.PHONY: ci-lint
