import sys
sys.dont_write_bytecode=True
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;P=O.parent
raw=(P/"prepare_sparse_source_revision.actual.py").read_bytes();s=raw.decode("utf-8")
old='old_iso=str(A).replace("root-source","isolation")\nold_out=str(A).replace("root-source","targeted")'
new='old_iso=str(B/"integration_codex/attach-fixture-current-two-parent-isolation-root-t11-1a11e7f5205729390aaee9f47b28ce6")\nold_out=str(B/"integration_codex/attach-fixture-current-two-parent-targeted-root-t11-1a11e7f5205729390aaee9f47b28ce6")'
assert s.count(old)==1;s=s.replace(old,new)
old2='  count=text.count(before)\n  if count:'
new2='  count=text.count(before)\n  expected_count=0 if name.startswith("prepare") and before==old_out.replace("\\\\","/") else 1\n  assert count==expected_count, "exact path replacement count"\n  if count:'
assert s.count(old2)==1;s=s.replace(old2,new2)
ast.parse(s)
inv=s.replace(new2,old2).replace(new,old);assert inv.encode()==raw
with (O/"prepare_sparse_source_revision.actual.py").open("xb") as f:f.write(s.encode())
def pin(p):
 b=Path(p).read_bytes();return dict(path=str(Path(p).resolve()),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
with (O/"path-correction.provenance.json").open("xb") as f:f.write((json.dumps(dict(original_source_ref=pin(P/"prepare_sparse_source_revision.actual.py"),replacement_source_ref=pin(O/"prepare_sparse_source_revision.actual.py"),original_manifest_ref=pin(P/"MF.json"),old_source_preserved=True,exact_inverse=True,actual_ran=False,formal_acceptance=False),ensure_ascii=True,indent=2)+"\n").encode())
exec(compile(s,str(O/"prepare_sparse_source_revision.actual.py"),"exec"),{"__file__":str(O/"prepare_sparse_source_revision.actual.py"),"__name__":"__main__"})

