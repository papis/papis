PYTHON = python3
PIP = pip3
TEST_COMMAND = $(PYTHON) -m pytest papis

test-non-pythonic:
	(cd tests/ ; ./run.sh)

bash-autocomplete:
	make -C scripts/shell_completion/

update-authors:
	git shortlog -s -e -n | \
		sed -e "s/\t/  /" | \
		sed -e "s/^\s*//" > \
		AUTHORS
