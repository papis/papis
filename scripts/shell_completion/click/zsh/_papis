#compdef papis

_papis_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    response=("${(@f)$( env COMP_WORDS="${words[*]}" \
                        COMP_CWORD=$((CURRENT-1)) \
                        _PAPIS_COMPLETE="complete_zsh" \
                        papis )}")

    for key descr in ${(kv)response}; do
      if [[ "$descr" == "_" ]]; then
          completions+=("$key")
      else
          completions_with_descriptions+=("$key":"$descr")
      fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U -Q
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -Q -a completions
    fi
    compstate[insert]="automenu"
}

_papis_completion $@
