#!/usr/bin/env bash
#vim-run: bash %

tag=$(git tag | sort -V | tail -1)
echo "What happened since last tag ($tag)"

git log --pretty=format:'- %s' $tag..main
