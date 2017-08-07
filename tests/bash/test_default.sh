#! /usr/bin/env bash


{
papis --cc --pick-lib config dir <<EOF

EOF
} || exit 1

{
papis --clear-cache --verbose --pick-lib config dir <<EOF

EOF
} || exit 1

{
papis --clear-cache --verbose --pick-lib --picktool papis.pick config dir <<EOF

EOF
} || exit 1

{
papis -j 1 --clear-cache --verbose --pick-lib \
  --log INFO \
  --picktool papis.pick config dir <<EOF

EOF
} || exit 1

{
papis -j 1 --set dir=hello --pick-lib \
  --log INFO \
  --picktool papis.pick config dir <<EOF

EOF
} || exit 1


#vim-run: bash %
