MAKEFILE_VERSION = v0.0.1-1-g513698d
MAKEFILE_DATE = 05-03-2017 12:48

## <<HELP
#
#                            Python Makefile
#
## HELP

# Local configuration
-include config.mk

# Recognise OS
ifeq ($(shell uname),Linux)
LINUX := 1
OSX   :=
else
LINUX :=
OSX   := 1
endif


PYTHON = python
PY_LINTER = flake8

WHICH = which
# sed program version
SED ?= $(if $(OSX),gsed,sed)
# Grep program version
GREP       ?= grep
# Find utility
FIND       ?= find
VENV_DIR ?= .env
CLEAN_FILES  ?=
# For creating tags
CTAGS ?= ctags
REQUIREMENTS = requirements.txt

# For coloring
TPUT       ?= $(shell $(WHICH) tput 2> /dev/null)
# If messages should have color
WITH_COLOR ?= 1
# If secondary programs output is shown
QUIET           ?= 0
# File to be cleaned
CLEAN_FILES     ?=
QQUIET     ?=
DEBUG      ?= @

ifndef QQUIET
ifeq ($(strip $(WITH_COLOR)),1)
COLOR_B         ?= $(if $(TPUT),$(shell $(TPUT) setaf 5),"\033[0;35m")
COLOR_E         ?= $(if $(TPUT),$(shell $(TPUT) sgr0),"\033[0m")
ARROW           ?= @echo "$(COLOR_B)===>$(COLOR_E)"
else
ARROW           ?= @echo "===>"
endif #WITH_COLOR

ECHO            ?= @echo

else
ARROW           := @ > /dev/null echo
ECHO            := @ > /dev/null echo
endif #QQUIET



CLEAN_FILES += \
$(shell find . -name *.pyc) \
$(shell find . -name *.pyo) \
$(shell find . -name __pycache__) \
$(wildcard test_* ) \

ifneq ($(strip $(QUIET)),0)
	FD_OUTPUT = 2>&1 > /dev/null
else
	FD_OUTPUT =
endif

dev-install-local:
	python setup.py develop --user

test:
	python setup.py test

install-local:
	python setup.py install --user

doc:
	make -C doc/ html

update-gh-pages:
	@echo "Warning: Black magic in action"
	git push origin `git subtree split --prefix doc/build/html/ master`:gh-pages --force

# =============
# Main cleaning
# =============
#
# This does a main cleaning of the produced auxiliary files.  Before using it
# check which files are going to be cleaned up.
#
clean: ## Remove build and temporary files
	$(ARROW) Cleaning up...
	$(DEBUG){ for file in $(CLEAN_FILES); do echo "  *  $$file"; done }
	$(DEBUG)rm -rf $(CLEAN_FILES)

# ============
# Check syntax
# ============
#
# It checks the syntax (lints) of all the tex sources using the program in the
# TEX_LINTER variable.
#
lint: ## Check syntax of sources
	$(PY_LINTER)

# ===============================
# Update the makefile from source
# ===============================
#
# You can always get the  last `latex-makefile` version using this target.
# You may override the `GH_REPO_FILE` to  any path where you save your own
# personal makefile
#
update: ## Update the makefile from the repository
	$(ARROW) "Getting makefile from $(GH_REPO_FILE)"
	$(DEBUG)wget $(GH_REPO_FILE) -O Makefile
GH_REPO_FILE ?= https://raw.githubusercontent.com/alejandrogallo/python-makefile/master/dist/Makefile

# ====================================
# Ctags generation for latex documents
# ====================================
#
# Generate a tags  file so that you can navigate  through the tags using
# compatible editors such as emacs or (n)vi(m).
#
tags: ## Create python exhuberant ctags
	$(CTAGS) --language-force=python -R *

# ================
# Print quick help
# ================
#
# It prints a quick help in the terminal
help: ## Prints help for targets with comments
	$(DEBUG)$(or $(AWK),awk) ' \
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
	@echo ""
	@echo "  $(MAKEFILE_VERSION)"
	@echo "  https://github.com/alejandrogallo/python-makefile"
	@echo "  Copyright Alejandro Gallo GPLv3 $(MAKEFILE_DATE)"
	@echo ""

FORCE:
help-%:
	$(DEBUG)sed -n "/[#] [=]\+/,/^$*: / { /"$*":/{q}; p; } " $(MAKEFILE_LIST) \
		| tac \
		| sed -n "1,/===/ {/===/n; s/^# //p}" \
		| tac \
		| sed -n "p; 1s/./=/gp; 1a\ "

# This is used for printing defined variables from Some other scripts. For
# instance if you want to know the value of the PDF_VIEWER defined in the
# Makefile, then you would do
#    make print-PDF_VIEWER
# and this would output PDF_VIEWER=mupdf for instance.
FORCE:
print-%:
	$(DEBUG)echo '$*=$($*)'
