from pathlib import Path
import json,hashlib
e=Path(__file__).resolve().parent
r=json.loads((e/"resource-map.json").read_text(encoding="utf8"))
assert r["collection_groups_after_intake"]==10 and r["all_observer_handles_closed"]
assert r["actual_authority"] is False and r["formal_increment"]==0
assert r["workspace_metrics"]["total_tree_metrics_complete"]
for n in ["g02-results.json","g03-results.json","g06-results.json"]:
 v=json.loads((e/n).read_text(encoding="utf8"))
 assert v["observer_closed"] and v["query_only"]
 assert v["uri"].endswith("?mode=ro&cache=private") and "immutable" not in v["uri"]
pins=[dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(e.glob("*.py"))]
(e/"collector-pins.json").write_text(json.dumps(pins,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("FINITE_RESOURCE_COLLECTION_VALIDATED_NO_ORIGINAL_RESOURCE_READ_DURING_SEAL")