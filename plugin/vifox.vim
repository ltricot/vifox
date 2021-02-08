if !has("python3")
  echo "vim has to be compiled with +python3 to run this"
	finish
endif

if exists('g:foxdot_plugin_loaded')
	finish
endif

let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

python3 <<EOF
from os.path import normpath, join
import sys
import vim

d = vim.eval('s:plugin_root_dir')
coded = normpath(join(d, '..', 'python'))
sys.path.insert(0, coded)

import fox
EOF


let g:foxdot_plugin_loaded = 1

function! SendCode()
	python3 fox.sendcode()
endfunction

command! -nargs=0 SendCode call SendCode()
map <leader>sc :SendCode<CR>

function! StartFox()
	python3 fox.start()
endfunction

command! -nargs=0 StartFox call StartFox()
map <leader>sf :StartFox<CR>
