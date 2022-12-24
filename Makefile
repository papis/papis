.PHONY: bash-autocomplete update-authors tags doc test ci-install ci-tests

bash-autocomplete:
	make -C scripts/shell_completion/

update-authors:
	git shortlog -s -e -n | \
		sed -e "s/\t/  /" | \
		sed -e "s/^\s*//" > \
		AUTHORS

tags:
	ctags -f tags \
		--recurse=yes \
		--tag-relative=yes \
		--fields=+l \
		--kinds-python=-i \
		--language-force=python \
		papis

doc:
	cd doc && make html SPHINXOPTS="-W --keep-going -n"
	@echo ""
	@echo -e "\e[1;32mRun '$$BROWSER doc/build/html/index.html' to see the docs\e[0m"
	@echo ""

test:
	python -m pytest -rswx --cov=papis -v -s papis tests

ci-install:
	bash tools/ci-install.sh

ci-test:
	bash tools/ci-run-tests.sh
