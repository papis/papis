PYTHON?=python -X dev
NIX?=nix --extra-experimental-features nix-command --extra-experimental-features flakes

all: help

help: 								## Show this help
	@echo -e "Specify a command. The choices are:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-18s\033[m %s\n", $$1, $$2}'
	@echo ""
.PHONY: help

shell-completion:					## Generate shell completion scripts
	make -C contrib/shell_completion
.PHONY: shell-completion

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
	cd doc && rm -rf build && make html SPHINXOPTS="-W --keep-going -n" || true
	@echo ""
	@echo -e "\e[1;32mRun '$$BROWSER doc/build/html/index.html' to see the docs\e[0m"
	@echo ""
.PHONY: doc

pytest:								## Run pytest tests and doctests
	$(PYTHON) -m pytest papis tests
.PHONY: pytest

ruff:								## Run ruff check (linting checks)
	ruff check
	@echo -e "\e[1;32mruff clean!\e[0m"
.PHONY: ruff

mypy:								## Run mypy (type annotations)
	$(PYTHON) -m mypy papis tools
	@echo -e "\e[1;32mmypy clean!\e[0m"
.PHONY: mypy

typos:								## Run typos (spellchecking)
	typos --sort
	@echo -e "\e[1;32mtypos clean!\e[0m"
.PHONY: codespell

ci-install:							## Install dependencies like on the CI
	bash tools/ci-install.sh
.PHONY: ci-install

ci-test:							## Run tests like on the CI
	bash tools/ci-run-test.sh
.PHONY: ci-test

ci-lint:							## Run linting like on the CI
	bash tools/ci-run-lint.sh
.PHONY: ci-lint

nix-build: 							## Build using nix
	$(NIX) build
.PHONY: nix-build

nix-update: 						## Update the nix flake.lock file
	$(NIX) flake update
.PHONY: nix-update

nix-test: 							## Run the tests within nix
	$(NIX) develop --command bash -c "source .venv/bin/activate; python -m pytest -v papis tests"
.PHONY: nix-update

nix-install: 						## Install nix flake to local profile
	$(NIX) profile install '.#papis'
.PHONY: nix-install
