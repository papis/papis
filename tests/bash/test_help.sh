#! /usr/bin/env bash

commands=$(
python3 <<EOF
import papis.commands

for cmd in papis.commands.list_commands():
    print(cmd)

EOF
)

papis -h || exit 1

for cmd in ${commands[@]} ; do
  echo ${cmd}
  papis ${cmd} -h || exit 1
done
