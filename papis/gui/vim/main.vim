
let g:papis_help_key = "h"
let g:papis_open_key = "o"

function! PapisOpen()
endfunction

function! PapisHelp()
    echomsg "Help - ".g:papis_help_key
    echomsg "Open - ".g:papis_open_key
endfunction

function! Pick()
    :silent! exe "!echo ".(line(".") - 2)
    :silent! quit!
endfunction

exec "nnoremap ".g:papis_help_key." :call PapisHelp()<cr>"
exec "nnoremap ".g:papis_open_key." :call PapisOpen()<cr>"
nnoremap q :quit<cr>
