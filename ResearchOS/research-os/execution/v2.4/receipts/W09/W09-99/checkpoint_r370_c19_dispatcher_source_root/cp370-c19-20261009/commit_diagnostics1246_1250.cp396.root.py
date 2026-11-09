"""Retain the exact contiguous diagnostic suffix while keeping old CP history."""
from pathlib import Path
S=Path(__file__).resolve().parent;raw=(S/'commit_diagnostics1237_1245.cp394.root.py').read_bytes()
start=raw.index(b'descriptions={');stop=raw.index(b'\nrows=[]',start);oldspec=raw[start:stop]
newspec=b"""descriptions={1246:'Read-only final state filename rg had no matches; earlier successful reads retained.',1247:'Root metadata capture stem contained dots outside accepted literal grammar; no event artifacts created.',1248:'Actual Python capture succeeded at exit0; orchestration parser incorrectly tried to parse one pretty JSON line; original event artifacts retained.',1249:'Read-only optional contract filename lookup used nonexistent input-contract.json; actual outer0 and successful Main/source reads retained.',1250:'Backup read-only Main lookup used obsolete ops/ci path; actual outer1 and all unobserved product exits null, later fixed literal lookup separately observed.'}
spec={1246:(S/'original1246.fixed-actual.binding.root.json','704596',1,None),1247:(S/'original1247.fixed-actual.binding.root.json','1d15d5',1,1),1248:(S/'original1248.fixed-actual.binding.root.json','9b4b37',0,0),1249:(S/'original1249.fixed-actual.binding.root.json','8c2fe7',0,None),1250:(S/'original1250.fixed-actual.binding.root.json','f86464',1,None)}"""
changes=[(oldspec,newspec),(b'cp395-diagnostics1245-br8-assembly-closed-live1246',b'cp397-diagnostics1250-capture-literal-repair-pending-live1251'),(b'd397414b9552e6bce821309257d3123d35b9088987fd3fd43c494e1fbaac995b',b'927f8e3d9019e476685073ff622c81bedfb779607e17b2ef6ed7bef6baf21d7e'),(b'source_cutoff_original_failure_ordinal=1236',b'source_cutoff_original_failure_ordinal=1245'),(b'next_original_failure_ordinal=1246',b'next_original_failure_ordinal=1251'),(b"cp['revision']==394",b"cp['revision']==396"),(b'end==1246',b'end==1251'),(b'cp395_diagnostics_and_br8_assembly',b'cp397_diagnostics_and_capture_literal_repair'),(b'registered_through=1245',b'registered_through=1250'),(b'revision=395,expected_previous_revision=394',b'revision=397,expected_previous_revision=396')]
fixed=raw
for old,new in changes:assert fixed.count(old)>=1;fixed=fixed.replace(old,new)
inverse=fixed
for old,new in reversed(changes):assert inverse.count(new)>=1;inverse=inverse.replace(new,old)
assert inverse==raw
exec(compile(fixed,str(Path(__file__).resolve()),'exec'),dict(__name__='__main__',__file__=str(Path(__file__).resolve())))
