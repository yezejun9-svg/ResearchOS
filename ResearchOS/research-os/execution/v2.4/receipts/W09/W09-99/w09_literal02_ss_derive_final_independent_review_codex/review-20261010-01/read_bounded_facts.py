import hashlib
import json
from pathlib import Path
R = Path("D:/作品集/ResearchOS/research-os")
HERE = Path(__file__).resolve().parent
records = json.loads((HERE / "input-shapes.json").read_text(encoding="utf-8"))
facts = {"refs": {name: record["ref"] for name, record in records.items()}}
def load(name):
    return json.loads(Path(records[name]["ref"]["path"]).read_bytes())
derive = load("derive")
precheck = load("precheck")
facts["derive_summary"] = {key: derive.get(key) for key in ("schema", "integrity", "required_formal_cases", "accepted_case_ids", "formal_cases_accepted", "reasons", "bridge_CAS")}
facts["derive_top_keys"] = list(derive)
facts["derived_case_rows"] = [row for row in derive["cases"] if row["case_id"] in ("C19", "A06")]
facts["derived_owner_rows"] = [row for row in derive["owners"] if row["task_id"] in ("W04", "W07", "W09")]
facts["precheck_top_keys"] = list(precheck)
facts["precheck_simple_fields"] = {key: value for key, value in precheck.items() if type(value) in (str, int, bool) or value is None}
facts["derive_Main_python_pins"] = {path: sha for path, sha in derive["input_hashes"].items() if str(R / "execution/v2.4").replace("/", "\\") in path and Path(path).suffix == ".py"}
facts["cp_top_keys"] = list(load("cp"))
def docs(value):
    if type(value) is dict:
        yield value
        for item in value.values():
            yield from docs(item)
    elif type(value) is list:
        for item in value:
            yield from docs(item)
    elif type(value) is str:
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError):
            return
        if type(parsed) in (dict, list):
            yield from docs(parsed)
for name, target in (("append_audit", "bc9a81"), ("derive_audit", "bc5257")):
    audit = load(name)
    lines = Path(audit["original_capture_ref"]["path"]).read_bytes().splitlines(keepends=True)
    entries = [json.loads(line) for line in lines]
    hosts = [doc for doc in docs(entries[-1]["payload"]["output"]) if doc.get("chunk_id") == target]
    facts[name] = {"original_ref": audit["original_capture_ref"], "matched_host_count": len(hosts), "line_hashes_match": audit["original_line_sha256"] == [hashlib.sha256(line).hexdigest() for line in lines]}
    facts[name]["hosts"] = [{"chunk_id": host["chunk_id"], "exit_code": host.get("exit_code"), "session_id": host.get("session_id"), "output_prefix": host.get("output", "")[:1000], "output_tail": host.get("output", "")[-2500:], "published_document_shapes": [{"keys": list(doc), "refs": {key: value for key, value in doc.items() if type(value) is dict and set(value) == {"path", "sha256", "bytes"}}} for doc in docs(host.get("output", ""))]} for host in hosts]
raw = (json.dumps(facts, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
with (HERE / "bounded-facts.json").open("xb") as stream:
    stream.write(raw)
print(json.dumps({"facts_ref": {"path": str(HERE / "bounded-facts.json"), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}, "facts": facts}, ensure_ascii=False))
print("ROOT_PYTHON_EXIT=0")
