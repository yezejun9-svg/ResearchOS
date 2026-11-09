from qa import run,TREE
raise SystemExit(run('main-full-syntax',['--check',str(TREE/'apps/desktop/main/main.js')]))
