"""Bind completed reviewer artifacts and the actual semantic diagnostic."""
from pathlib import Path
import hashlib, json, os
R=Path("D:/作品集/ResearchOS/research-os")
V=R/"execution/v2.4"; W=V/"receipts/W09/W09-99"
N=Path(__file__).resolve().parent
Q=W/"full_w09_nf5_independent_source_review_codex/review-nf5-20261010-01"
def pin(p):
    p=Path(p);data=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
def save(name,data):
    p=N/name
    with p.open("xb") as f:
        f.write((json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode());f.flush();os.fsync(f.fileno())
    return pin(p)
origin=pin(Q/"original1147.failure-origin.json")
assert (origin["sha256"],origin["bytes"])==("0cb85d562686c113e24cd65c62b6a88778d1c654a9d76d3b7f5bc4ffbca851f9",3937)
d=json.loads(Path(origin["path"]).read_bytes())
assert d["original_ordinal"]==1147 and d["actual_outer_exit"]==d["actual_Python_exit"]==0 and d["semantic_failed"]==1
for k,v in d.items():
    if k.endswith("_ref") and isinstance(v,dict):
        assert pin(v["path"])==v
row=dict(ordinal=1147,origin_ref=origin,origin_selector="$",capture_binding_ref=d["actual_host_binding_ref"],
    verification_ref=origin,source_fact_refs=[v for k,v in d.items() if k.endswith("_ref") and isinstance(v,dict)],
    description="Independent NF5 checker traversed prepare's else/run AST branch and falsely counted invoke. Original process exits0/0, successful26 controls and4154 closed resources retained; only the new body traversal predicate corrected. No Native/Go/SQL/model/TP process was started.",
    actual_outer_exit=0,actual_python_exit=0,actual_native_exit=None,actual_Go_exit=None,
    actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
addon=save("pending-additions.original1147.root.json",dict(schema="researchos.root-pending-diagnostic-additions.v1",
    issued_by="codex:/root",pending=[row],next_original_failure_ordinal=1148,counter_reset=False,formal_acceptance=False))
refs={}
for label in ("producer","registrar"):
    h=json.loads((Q/label/"HDF.json").read_bytes())
    refs[label]=dict(hdf=pin(Q/label/"HDF.json"),mf=h["manifest_ref"],decision=h["source_decision_ref"])
    for ref in refs[label].values(): assert pin(ref["path"])==ref
assert refs["producer"]["decision"]["sha256"]=="bd0e6271a9090b6477e6977c31eccdc9ae2ef204e6071456f850647cc304ee2e"
assert refs["registrar"]["decision"]["sha256"]=="fcd4674d5159a28bee6202258f7929f4c6b85e03c73d0cbaa5eb838546690e87"
partial=save("nf5-completed-review-inputs.partial.root.json",dict(
    schema="researchos.root-nf5-preparation-inputs.v1",issued_by="codex:/root",formal_acceptance=False,
    producer_review_refs=refs["producer"],registrar_review_refs=refs["registrar"],
    producer_review_audit_ref=pin(N/"w09.nf5-producer-review.actual-audit.root.json"),
    registrar_review_audit_ref=pin(N/"w09.nf5-registrar-review.actual-audit.root.json")))
print(json.dumps(dict(addon_ref=addon,partial_ref=partial,formal_acceptance=False),ensure_ascii=False))
