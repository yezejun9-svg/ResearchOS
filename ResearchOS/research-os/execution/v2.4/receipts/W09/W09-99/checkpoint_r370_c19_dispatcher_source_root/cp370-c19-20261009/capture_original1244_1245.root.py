"""Capture exact Root diagnostic1244 and1255 actual host selectors."""
from pathlib import Path
S=Path(__file__).resolve().parent;raw=(S/'capture_original1233.root.py').read_bytes()
old=b"SPECS = {1233: ('root','caacd8',0,0)}";new=b"SPECS = {1244: ('root','d9e281',1,1),1245: ('root','3ebb2c',1,None)}"
assert raw.count(old)==1;fixed=raw.replace(old,new);assert fixed.replace(new,old)==raw
exec(compile(fixed,str(S/'capture_original1233.root.py'),'exec'),dict(__name__='__main__',__file__=str(S/'capture_original1233.root.py')))
