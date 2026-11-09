"""Retain actual new metadata diagnostics without changing their exit facts."""
from pathlib import Path
S=Path(__file__).resolve().parent;raw=(S/'capture_original1233.root.py').read_bytes()
old=b"SPECS = {1233: ('root','caacd8',0,0)}"
new=b"SPECS = {1247: ('root','1d15d5',1,1),1248: ('root','9b4b37',0,0),1249: ('root','8c2fe7',0,None),1250: ('backup','f86464',1,None)}"
assert raw.count(old)==1;fixed=raw.replace(old,new);assert fixed.replace(new,old)==raw
exec(compile(fixed,str(S/'capture_original1233.root.py'),'exec'),dict(__name__='__main__',__file__=str(S/'capture_original1233.root.py')))
