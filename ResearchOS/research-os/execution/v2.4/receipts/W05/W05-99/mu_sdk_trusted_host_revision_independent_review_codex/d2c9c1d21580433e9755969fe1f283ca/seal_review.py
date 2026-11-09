from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def meta(p):
 raw=p.read_bytes();return dict(path=p.as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
for filename in ["intake.json","compile-evidence-review.json"]:
 d=json.loads((O/filename).read_bytes())
 for ref in d["files"]:
  x=meta(Path(ref["path"]));assert (x["sha256"],x["bytes"])==(ref["sha256"],ref["bytes"]),ref["path"]
  if "snapshot" in ref:
   y=meta(O/ref["snapshot"]);assert (y["sha256"],y["bytes"])==(ref["sha256"],ref["bytes"])
m=dict(schema="researchos.trusted-host-revision-independent-review.v1",decision="PASS_SOURCE_FIX_SCOPE_WITH_OPEN_RUNTIME_GATES",closed=["R1","R2_prepare","R3","R4_with_v9","S1_prepare"],open_nonblocking=["A1_tool_schema_limit"],runtime_gates="OPEN_NOT_AUTHORIZED_BY_THIS_REVIEW",source_and_evidence_recheck="PASS",files=[meta(p) for p in sorted(O.rglob("*")) if p.is_file() and p!=O/"manifest.json"])
(O/"manifest.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(files=len(m["files"]),handoff=meta(O/"HANDOFF.md"),review=meta(O/"REVIEW.md"),manifest=meta(O/"manifest.json"))))

