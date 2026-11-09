import sys
sys.dont_write_bytecode=True
import json,hashlib,ast
from pathlib import Path
O=Path(__file__).resolve().parent
A=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/historical20_upgrade_source_codex/h20-r1-root-1791519270000")
def pin(p):
 raw=Path(p).read_bytes();return dict(path=str(Path(p).resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
base=A/"prepare_history20_wrong_key_test_correction.actual.py"
raw=base.read_bytes();source=raw.decode("utf-8")
before='assert "RestoreBackup(context.Background(),opt.Snapshot" not in changed'
after='assert "RestoreBackup(context.Background(),opt.Snapshot" not in changed.split("func TestHistory20PublicUpgradePreservesSourceAndRevokesRestoredCredentials",1)[1].split("func TestHistory20RejectsReleaseAndSourceDrift",1)[0]'
assert source.count(before)==1
source=source.replace(before,after);assert source.replace(after,before).encode()==raw;ast.parse(source)
with (O/base.name).open("xb") as f:f.write(source.encode())
guard=json.loads((A/"guard.final.json").read_bytes());assert guard["closed"] and not guard["errors"] and guard["retained_handles_count"]==0
save("scoped-checker-source.provenance.json",dict(old_failed_source_ref=pin(base),old_failed_guard_ref=pin(A/"guard.final.json"),before=before,after=after,one_replacement_full_inverse_equal=True,new_source_ref=pin(O/base.name),native_SQL_Go=False))
print(json.dumps(dict(new_source_ref=pin(O/base.name),previous_failed_guard_closed=True)))

