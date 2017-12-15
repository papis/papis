#! /usr/bin/env bash

source tools/lib.sh

COMMANDS=($(get_papis_commands))

out=build/bash/papis
mkdir -p build/bash

echo > ${out}

cat >> ${out} <<EOF

_papis (){
local cur
# Pointer to current completion word.
# By convention, it's named "cur" but this isn't strictly necessary.

COMPREPLY=()   # Array variable storing the possible completions.
cur=\${COMP_WORDS[COMP_CWORD]}
prev=\${COMP_WORDS[COMP_CWORD-1]}

case "\$cur" in
  -*)
  COMPREPLY=( \$( compgen -W "$(get_papis_flags | paste -s )" -- \$cur ) );;
  * )
  COMPREPLY=( \$( compgen -W "$(get_papis_commands | paste -s )" -- \$cur ) );;
esac

case "\$prev" in

  config)
    COMPREPLY=( \$( compgen -W "$(get_papis_flags config | paste -s ) $(get_config_keys | paste -s )" -- \$cur ) )
    ;;

EOF

for cmd in ${COMMANDS[@]}; do

echo ${cmd}

cat >> ${out} <<EOF
  ${cmd})
    COMPREPLY=( \$( compgen -W "$(get_papis_flags ${cmd} | paste -s )" -- \$cur ) )
    ;;

EOF

done

cat >> ${out} <<EOF

  --picktool)
    COMPREPLY=( \$( compgen -W "papis.pick vim rofi" -- \$cur ) )
    ;;

  --log)
    COMPREPLY=( \$( compgen -W "INFO DEBUG WARNING ERROR CRITICAL" -- \$cur ) )
    ;;

  --out|-o)
    COMPREPLY=( \$( compgen -f -- \$cur ) )
    ;;

  --from-*)
    COMPREPLY=( \$( compgen -f -- \$cur ) )
    ;;

  --lib|-l|--from-lib)
    COMPREPLY=( \$( compgen -f -W "\$(papis list --libraries)" -- \$cur ) )
    ;;

  --set)
    COMPREPLY=( \$( compgen -W "$(get_config_keys | sed s/$/=/ | paste -s )" -- \$cur ) )
    ;;

esac

return 0
}


complete -F _papis papis
EOF
