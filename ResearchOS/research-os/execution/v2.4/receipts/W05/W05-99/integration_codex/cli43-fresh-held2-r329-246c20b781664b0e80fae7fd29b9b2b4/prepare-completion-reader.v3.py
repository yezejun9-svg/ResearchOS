"""Prepare immutable completion reader; no target or canonical mutation."""
import ast
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).absolute().parent
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
sys.dont_write_bytecode=True
def pin(p):
    p=Path(p).absolute(); b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
oldp=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r328-bf943a8137c74df09e010347615b0eec/close-root-launch-observation.v2.py'
old=oldp.read_bytes()
changes=[
(b"assert args.known_pending_origins >= 4",b"assert args.known_pending_origins >= 3"),
(b'edec4df6c5f4fcce632008517adff4c4b2a82f64bc4715d87c8a53e7fd3e19c3',b'90aec754f429ee9f946ac6943685848b358a33e28ea2f4e7484b03235c6673e0'),
(b'26bda302fbb13193918ff58a2fc271f8e013e85cc8df4d98d2b0cc40a82bc010',b'55efa0fbd05a9776fa2fcf5c12f360c8846cd39695c4c0f34a9fea7813631221'),
(b"'registered_origin_count': 469",b"'registered_origin_count': 481"),
(b"'observed_origin_count_at_closure': 469 +",b"'observed_origin_count_at_closure': 481 +"),
(b"'prepare-root-caller.v3.py'",b"'prepare-root-caller.v4.py'"),
(b"    'close-root-launch-observation.v2.py', 'root-metadata.tool-observations.after-grant.json',\n    'failure-origin.exec-textencoder.json')]",b"    'close-root-launch-observation.v3.py', 'root-metadata.tool-observations.after-grant.json')]")]
new=old
for a,b in changes:
    assert new.count(a)==1,(a,new.count(a))
    new=new.replace(a,b)
inverse=new
for a,b in reversed(changes):
    assert inverse.count(b)==1,(b,inverse.count(b))
    inverse=inverse.replace(b,a)
assert inverse==old
ast.parse(new.decode('utf-8'))
np=OUT/'close-root-launch-observation.v3.py'
with np.open('xb') as h:h.write(new)
record={'actor':'codex:/root','old_ref':pin(oldp),'new_ref':pin(np),
    'changes':[{'old_utf8':a.decode(),'new_utf8':b.decode()} for a,b in changes],
    'whole_byte_inverse':True,'AST_without_execution':True,'target_executions':0,
    'changes_purpose':'Current exact scope/grant, registered481 and known3pending minimum, new preparer ref, exclude old-scope-only TextEncoder origin member. No actual future exit/case/cause is guessed.',
    'formal_increment':0,'counter_reset':False}
with (OUT/'completion-reader-preparation.json').open('xb') as h:h.write((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'completion_reader_ref':pin(np),'preparation_ref':pin(OUT/'completion-reader-preparation.json')},ensure_ascii=False))
