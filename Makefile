PYTHON = python
VENV_DIR ?= .env
CLEAN_FILES  ?=
REQUIREMENTS = requirements.txt

CLEAN_FILES += \
$(shell find . -name *.pyc) \
$(shell find . -name *.pyo) \
$(shell find . -name __pycache__) \
$(wildcard test_* ) \

dev-install-local:
	python setup.py develop --user

test: ## Run tests
	python -m unittest discover

install-local:
	python setup.py install --user

help: ## Prints help for targets with comments
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

tags:
	ctags --language-force=python $(shell find . | grep py$$)

clean: ## Remove build and temporary files
	@echo Cleaning up...
	@{ for file in $(CLEAN_FILES); do echo "  *  $$file"; done }
	@rm -rf $(CLEAN_FILES)

help: ## Prints help for targets with comments
	@$(or $(AWK),awk) ' \
		BEGIN {FS = ":.*?## "}; \
		/^## *<<HELP/,/^## *HELP/ { \
			help=$$1; \
			gsub("#","",help); \
			if (! match(help, "HELP")) \
				print help ; \
		}; \
		/^[a-zA-Z0-9_\-.]+:.*?## .*$$/{ \
			printf "\033[36m%-30s\033[0m %s\n", $$1, $$2 ; \
		};' \
		$(MAKEFILE_LIST)

