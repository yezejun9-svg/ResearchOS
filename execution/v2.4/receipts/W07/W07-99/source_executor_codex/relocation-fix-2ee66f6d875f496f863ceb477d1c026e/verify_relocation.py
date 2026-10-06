import importlib.util, json, sys
from pathlib import Path
source, target, collection = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3])
spec = importlib.util.spec_from_file_location("w07_relocation_gate", source)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
gate.ROOT = target
evidence = (target / collection).resolve()
proof = json.loads((evidence / "proof.json").read_text(encoding="utf-8"))
refs = proof["h07_invocations"][0]["db_snapshots"]
before = {ref["path"]: gate.sha256(target / ref["path"]) for ref in refs}
opened = []
connect = gate.sqlite3.connect
def local_only(database, **kwargs):
    assert database.startswith(evidence.as_uri() + "/h07-db/")
    assert database.endswith("?mode=ro&immutable=1")
    opened.append(database)
    return connect(database, **kwargs)
gate.sqlite3.connect = local_only
actual = gate.verify_h07_evidence(evidence, proof)
after = {ref["path"]: gate.sha256(target / ref["path"]) for ref in refs}
print(json.dumps({"mode":"READ_ONLY_H07_RELOCATION_QUALIFICATION", "proof_ref":gate.file_ref(evidence / "proof.json"), "actual":actual,"opened_snapshot_uris":opened,"hashes_before":before,"hashes_after":after,"network_calls":0,"formal_LIVE_acceptance":False}, ensure_ascii=False))
sys.exit(0 if actual and before == after and len(opened) == 13 else 1)
