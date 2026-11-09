from pathlib import Path
root=Path(__file__).resolve().parent
p=root/'stage/ops/experiment_sandbox/sandbox_windows.go'
s=p.read_text(encoding='utf-8')
start=s.index('\tdefer windows.CloseHandle(pi.Process)')
end=s.index('// goEnvironment permits',start)
fragment=(root/'finish_fragment.txt').read_text(encoding='utf-8')
p.write_text(s[:start]+fragment+'\n'+s[end:],encoding='utf-8',newline='\n')
