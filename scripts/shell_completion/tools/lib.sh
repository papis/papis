#! /usr/bin/env bash

get_papis_commands(){
  local cmd=$1
  papis ${cmd} -h                                 |
  awk '
    /positional arguments/,/optional arguments/ {
    print $1
  }'                                              |
  sed "1d; 2d"                                    | # Remove two first rows
  tac                                             | # Reverse ouput
  sed "1d; 2d"                                    | # Remove two last rows
  tac
}

get_papis_flags(){
  local cmd=$1
  papis ${cmd} -h     |
  grep -o -E '\s-\S*' |
  tr -d "[,']"        |
  sort                |
  uniq
}

