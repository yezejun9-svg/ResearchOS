"""Correct Root-relative metadata path while preserving failed original1240."""
from pathlib import Path
S=Path(__file__).resolve().parent
original=S/'prepare_roles_br8.cp393.root.py'
raw=original.read_bytes()
old=b'R=S.parents[5]';new=b'R=S.parents[6]'
assert raw.count(old)==1
fixed=raw.replace(old,new)
assert fixed.replace(new,old)==raw
exec(compile(fixed,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))
