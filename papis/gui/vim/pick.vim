function! Pick()
  exe ":.s/.*/".line(".")
  if line(".") != 1
    :normal! kdgg
  endif
  if line(".") != line("$")
    :normal! jdG
  endif
  :write
  :quit
endfunction

nnoremap <Return> :call Pick()<cr>
syntax match Comment "^#.*$"
