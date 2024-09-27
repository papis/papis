#!/usr/bin/env bash
#vim-run: bash %

set -o errexit -o noglob -o pipefail

tag=$(git tag | sort -V | tail -1)
echo "What happened since last tag ($tag)"

git log --pretty=format:'- %s' $tag..main
