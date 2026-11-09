import sys,json,hashlib
from pathlib import Path
P=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r361-provenance-qualified-source-ready")
O=Path(__file__).resolve().parent
cp=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/checkpoint.json")
assert hashlib.sha256(cp.read_bytes()).hexdigest()=="685545935a0da0bf576eb28ada59f453beb9d26628af4f656faf18f94d336d56"
cleanup=json.loads((P/"source_guard.cleanup.actual.json").read_bytes())
assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
old=(P/"checkpoint_provenance_qualification.atomic.py").read_text(encoding="utf-8")
a='  assert x["origin_key"]==original["origin_key"] and x["evidence_ref"]==original["evidence_ref"] and x["counted_once"]==original["counted_once"]\n  if i not in corrected:assert x==original'
b='  if i in corrected:\n   assert {k:v for k,v in x.items() if k!="original_payload"}=={k:v for k,v in original.items() if k!="original_payload"}\n  else:assert x==original'
assert old.count(a)==1
new=old.replace(a,b);assert new.replace(b,a)==old
with (O/"checkpoint_provenance_qualification_revision.atomic.py").open("xb") as f:f.write(new.encode())
fp=P/"checkpoint.execution.facts.json";facts=json.loads(fp.read_bytes())
assert hashlib.sha256(fp.read_bytes()).hexdigest()=="df3f97ae249b0f478d32cfb530226a4e8e9d679411e7b8d643187fea26d06187"
op=P/"failure-origin.847.json";raw=op.read_bytes();ref=dict(path=str(op),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
facts["diagnostics"].append(dict(ordinal=847,origin_ref=ref,actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,description="Root CP361 transform imposed evidence_ref on heterogeneous old counters; KeyError before any canonical write, all guards closed. Immutable old writer and original marked1 IO preserved; distinct invariant compares unqualified whole records and outer fields on only two corrections. No counter reset."))
facts["checkpoint_note"]=facts["checkpoint_note"].replace("eight distinct originals839..846 once: registered844/highest846","nine distinct originals839..847 once: registered845/highest847")
with (O/"checkpoint.execution.facts.json").open("xb") as f:f.write((json.dumps(facts,ensure_ascii=True,indent=2)+"\n").encode())
writer=O/"checkpoint_provenance_qualification_revision.atomic.py"
v=writer.read_text(encoding="utf-8")
for a,b in (("list(range(839,847))","list(range(839,848))"),('==844','==845'),('failure_count=844','failure_count=845'),('registered_failures=844','registered_failures=845'),('ordinal=846','ordinal=847'),('next_failure_ordinal=847','next_failure_ordinal=848')):
 v=v.replace(a,b)
writer.write_text(v,encoding="utf-8",newline="\n")
for p in (writer,O/"checkpoint.execution.facts.json"):
 raw=p.read_bytes();print(json.dumps(dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))),flush=True)
