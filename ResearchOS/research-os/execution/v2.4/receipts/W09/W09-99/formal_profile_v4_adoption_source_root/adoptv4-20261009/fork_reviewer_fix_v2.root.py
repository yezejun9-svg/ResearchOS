"""Preserve sealed v1 and fix only the independently reproduced actor gate."""
import ast,hashlib,json,os
from pathlib import Path
N=Path(__file__).resolve().parent
V=N/'v2'
old=N/'adopt_formal_profile.source.py';b=old.read_bytes()
assert len(b)==8759 and hashlib.sha256(b).hexdigest()=='c5a3e4eae036f6468b8a63c3a4e51a082b1182a6a27484f0bc3393b417bfb668'
before=b"a['actor_id']!=ACTOR"
after=b"a['actor_id']=='codex:/root/attach_fixture_source_review'"
assert b.count(before)==1
new=b.replace(before,after,1);ast.parse(new)
V.mkdir(exist_ok=False)
with (V/'adopt_formal_profile.source.py').open('xb') as f:f.write(new);f.flush();os.fsync(f.fileno())
with (V/'adopter.v1.full-byte-inverse.py').open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
with (V/'reviewer-gate.allowed-byte-change.json').open('xb') as f:
    f.write((json.dumps(dict(before_sha256=hashlib.sha256(b).hexdigest(),after_sha256=hashlib.sha256(new).hexdigest(),before_bytes=len(b),after_bytes=len(new),only_replacement=dict(before=before.decode(),after=after.decode()),finding='ADOPTER-F1',canonical_or_main_written=False),indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
print(json.dumps(dict(writer=dict(path=str((V/'adopt_formal_profile.source.py').resolve()),sha256=hashlib.sha256(new).hexdigest(),bytes=len(new)),Main_written=False)),flush=True)
