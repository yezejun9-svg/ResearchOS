"""Retain the read-only state filename lookup's actual no-match exit."""
from pathlib import Path
S=Path(__file__).resolve().parent;raw=(S/'capture_original1233.root.py').read_bytes()
old=b"SPECS = {1233: ('root','caacd8',0,0)}";new=b"SPECS = {1246: ('root','704596',1,None)}"
assert raw.count(old)==1;fixed=raw.replace(old,new);assert fixed.replace(new,old)==raw
exec(compile(fixed,str(S/'capture_original1233.root.py'),'exec'),dict(__name__='__main__',__file__=str(S/'capture_original1233.root.py')))
