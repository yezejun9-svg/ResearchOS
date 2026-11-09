"""Keep failed metadata prefix immutable; add exact Root audit format support."""
from pathlib import Path
S=Path(__file__).resolve().parent;raw=(S/'prepare_w09_closeout_diagnostics1251_1259.root.py').read_bytes()
changes=[
 (b"O=S/'cp399-w09-closeout-preparation-live1260'",b"O=S/'cp399-w09-closeout-preparation-live1261'"),
 (b"cid=d.get('original_call_id',d.get('call_id'));assert events[1]['payload']['call_id']==events[2]['payload']['call_id']==cid",b"cid=d.get('original_call_id',d.get('call_id'));assert events[1]['payload']['call_id']==events[2]['payload']['call_id']\n if cid is not None:assert cid==events[1]['payload']['call_id']\n if d.get('binding_sha256') is not None:assert d['binding_sha256'] in (lines[1]+lines[2]).decode('utf-8')"),
 (b"'Overall derived formal status PARTIAL yields process1; W09 C19/A06 independently VALID_ACCEPTED, 2/42. No automatic replay.')]",b"'Overall derived formal status PARTIAL yields process1; W09 C19/A06 independently VALID_ACCEPTED, 2/42. No automatic replay.'),\n (1260,S/'original1260.fixed-actual.binding.root.json','4bee64',1,1,'Root pending metadata preparation assumed original_call_id existed in actual-audit schema; no Canon mutation and empty output directory preserved.')]"),
 (b"next_original_failure_ordinal=1260",b"next_original_failure_ordinal=1261"),
 (b"'bc5257':1259",b"'bc5257':1259,'4bee64':1260")
]
fixed=raw
for old,new in changes:assert fixed.count(old)==1;fixed=fixed.replace(old,new)
inverse=fixed
for old,new in reversed(changes):assert inverse.count(new)==1;inverse=inverse.replace(new,old)
assert inverse==raw
exec(compile(fixed,str(Path(__file__).resolve()),'exec'),dict(__name__='__main__',__file__=str(Path(__file__).resolve())))

