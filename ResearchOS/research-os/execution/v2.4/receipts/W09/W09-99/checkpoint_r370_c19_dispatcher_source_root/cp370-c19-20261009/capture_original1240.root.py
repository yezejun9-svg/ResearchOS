"""Capture actual metadata failure1240; keep original source and successful prefix."""
from pathlib import Path
S=Path(__file__).resolve().parent
raw=(S/'capture_original1233.root.py').read_bytes()
old=b"SPECS = {1233: ('root','caacd8',0,0)}"
new=b"SPECS = {1240: ('root','ef501d',1,1)}"
assert raw.count(old)==1
fixed=raw.replace(old,new);assert fixed.replace(new,old)==raw
exec(compile(fixed,str(S/'capture_original1233.root.py'),'exec'),dict(__name__='__main__',__file__=str(S/'capture_original1233.root.py')))
