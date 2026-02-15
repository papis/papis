#!/usr/bin/env bash

set -e

if [[ "$PAPIS_CI_RUN" -ne 42 ]]; then
  echo "WARNING: this script destroys your local files! Use only in throw-away environments like containers or virtual machines."
  echo "If you are unsure about this. Don't run it."
  exit 1
fi

mkdir -p "$PAPIS_DEFAULT_LIBRARY_PATH/"{papers,books} || true
mkdir -p "$XDG_CONFIG_HOME/papis" || true
cat >"$XDG_CONFIG_HOME/papis/config" <<EOF

[settings]
editor = /bin/true
file-browser = /bin/true
opentool = /bin/true

[papers]
dir = $PAPIS_DEFAULT_LIBRARY_PATH/papers/

[books]
dir = $PAPIS_DEFAULT_LIBRARY_PATH/books/

EOF

set -x

printf "0\ny\n" | papis add --no-confirm https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.124.171801/
printf "n\nn\n" | papis add --from doi 10.1103/PhysRevLett.124.171801/
papis list Crescini
papis list --all --format '{doc[year]} {doc[title]}'

# TODO: do we want to check other usecases here?
