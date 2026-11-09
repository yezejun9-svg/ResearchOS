from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def meta(p):
 raw=p.read_bytes();return dict(path=p.as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
for ref in json.loads((O/"intake.json").read_bytes())["files"]:
 a=meta(Path(ref["path"]));b=meta(O/ref["snapshot"])
 assert a["sha256"]==b["sha256"]==ref["sha256"] and a["bytes"]==b["bytes"]==ref["bytes"]
manifest=dict(schema="researchos.source-read-guard-independent-review.v1",decision="REQUEST_CHANGES",findings=["R1"],real_winapi_calls=0,provider_requests=0,source_recheck="PASS",files=[meta(p) for p in sorted(O.rglob("*")) if p.is_file() and p!=O/"manifest.json"])
(O/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(files=len(manifest["files"]),handoff=meta(O/"HANDOFF.md"),review=meta(O/"REVIEW.md"),manifest=meta(O/"manifest.json"))))

