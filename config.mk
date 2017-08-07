PYTHON = python3
PIP = pip3
TEST_COMMAND = $(PYTHON) -m pytest papis

test-non-pythonic:
	(cd tests/ ; ./run.sh)
