#! /usr/bin/env bash
#vim-run: bash %

gg='git log --decorate --oneline --date-order --all'
tag=$(git tag | tail -1)
echo "What happened since last tag ($tag)"

$gg | awk "
{
  print \$NL
}
/tag: $tag/ {
  exit 1
}
" | sed "s/^\S*/-/"
