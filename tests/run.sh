#! /usr/bin/env bash

cat <<EOF
 _   _               ____        _   _                 _
| \ | | ___  _ __   |  _ \ _   _| |_| |__   ___  _ __ (_) ___
|  \| |/ _ \| '_ \  | |_) | | | | __| '_ \ / _ \| '_ \| |/ __|
| |\  | (_) | | | | |  __/| |_| | |_| | | | (_) | | | | | (__
|_| \_|\___/|_| |_| |_|    \__, |\__|_| |_|\___/|_| |_|_|\___|
 TEST SUITE                |___/
EOF

for i in *; do

  [[ ! -d ${i} ]] && continue

  for test_script in $i/test*; do
    echo ${test_script}
    ./${test_script} || exit 1
  done

done

#vim-run: bash %
