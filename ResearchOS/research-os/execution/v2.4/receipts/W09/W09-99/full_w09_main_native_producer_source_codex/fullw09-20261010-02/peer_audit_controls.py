"""Finite peer-audit Source controls; no prepare/run or product child."""
import copy
import hashlib
import json
from pathlib import Path
import types

N = Path(__file__).resolve().parent
W = N.parent.parent
OLD = N.parent / "fullw09-20261009-01"
REVIEW = W / "full_w09_main_native_producer_independent_source_review_codex" / "review-fullw09-20261009-01"
raw = (N / "full_w09_runtime.source.py").read_bytes()
m = types.ModuleType("full_w09_v2_pure_peer_controls")
m.__file__ = str(N / "full_w09_runtime.source.py")
exec(compile(raw, m.__file__, "exec"), m.__dict__)

def pin(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

rows = []
def check(name, predicate):
    ok = bool(predicate)
    rows.append({"name": name, "passed": ok, "scope": "SOURCE_ONLY_NO_AUTHORITY"})
    if not ok: raise AssertionError(name)

def reject(name, action, expected):
    try: action()
    except ValueError as exc: check(name, str(exc) == expected)
    else: check(name, False)

peer_binding_path = REVIEW / "actual-Source-author-real-Root-peer.binding.json"
peer_ref = pin(peer_binding_path)
peer = json.loads(peer_binding_path.read_bytes())
old_actor = "codex:/root/native_temp_independent_review"
new_actor = m.AUTHOR
check("old-real-peer-all-pins-and-Root-log-positive", m.actual_audit(peer_ref, old_actor, peer["binding_sha256"]) == [peer_ref, peer["original_capture_ref"]])
check("canonical-old-actor-exact-host-map", m.exact_host_peer_author(old_actor) == "/root/native_temp_independent_review")
check("canonical-new-actor-exact-host-map", new_actor == "codex:/root/w09_formal_profile_source_impl" and m.exact_host_peer_author(new_actor) == "/root/w09_formal_profile_source_impl")
reject("noncanonical-host-actor-rejected", lambda: m.exact_host_peer_author("/root/native_temp_independent_review"), "CANONICAL_PEER_ACTOR")
reject("forged-canonical-path-rejected", lambda: m.exact_host_peer_author("codex:/root/../native_temp_independent_review"), "CANONICAL_PEER_ACTOR")
root_binding_path = OLD / "real-Root-audit.control.binding.json"
root_binding = json.loads(root_binding_path.read_bytes())
root_ref = pin(root_binding_path)
check("real-Root-tool-pair-still-positive", m.actual_audit(root_ref, m.ROOT_ACTOR, root_binding["binding_sha256"]) == [root_ref, root_binding["original_capture_ref"]])

original_read = m.read_ref
original_raw = Path(peer["original_capture_ref"]["path"]).read_bytes()
original_lines = original_raw.splitlines(keepends=True)
assert len(original_lines) == 3

def fake_ref(label, raw):
    return {"path": str(N / ("synthetic-" + label + ".json")), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def synthetic(label, mutate_record=None, mutate_capture=None):
    record = copy.deepcopy(peer)
    if mutate_record: mutate_record(record)
    captured = original_raw
    if mutate_capture:
        parts = [json.loads(line) for line in original_lines]
        mutate_capture(parts)
        captured = b"".join((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode() for row in parts)
        record["original_capture_ref"] = fake_ref(label + "-capture", captured)
    ref = fake_ref(label + "-binding", (json.dumps(record, ensure_ascii=False) + "\n").encode())
    data = {ref["path"]: (json.dumps(record, ensure_ascii=False) + "\n").encode(), record["original_capture_ref"]["path"]: captured}
    m.read_ref = lambda item: data[item["path"]] if item["path"] in data else original_read(item)
    try:
        m.actual_audit(ref, old_actor, peer["binding_sha256"])
    finally:
        m.read_ref = original_read

reject("foreign-host-author-rejected", lambda: synthetic("foreign-author", mutate_capture=lambda parts: parts[2]["payload"].__setitem__("author", "/root/foreign_author")), "ACTUAL_PEER_DELIVERY")
reject("wrong-recipient-peer-rejected", lambda: synthetic("wrong-peer", mutate_capture=lambda parts: parts[2]["payload"].__setitem__("recipient", "/root/other")), "ACTUAL_PEER_DELIVERY")
reject("canonical-actor-replacement-rejected", lambda: synthetic("actor-substitution", mutate_record=lambda record: record.__setitem__("actor_id", "codex:/root/foreign_author")), "AUDIT_FIXED_ROOT_ACTOR_BINDING")
reject("metadata-adjacency-rejected", lambda: synthetic("wrong-adjacency", mutate_capture=lambda parts: parts[2].__setitem__("ordinal", parts[2]["ordinal"] + 2)), "ACTUAL_PEER_DELIVERY")
reject("metadata-time-rejected", lambda: synthetic("wrong-time", mutate_capture=lambda parts: parts[2].__setitem__("timestamp", "2000-01-01T00:00:00Z")), "ACTUAL_PEER_DELIVERY")
reject("client-authored-rejected", lambda: synthetic("client-authored", mutate_capture=lambda parts: parts[2]["metadata"].__setitem__("client_authored", True)), "ACTUAL_PEER_DELIVERY")
reject("shifted-source-offset-rejected", lambda: synthetic("shifted-offset", mutate_record=lambda record: record["source_line_offsets"].__setitem__(2, record["source_line_offsets"][2] + 1)), "ACTUAL_ROOT_AUDIT_BYTES")
reject("wrong-line-digest-rejected", lambda: synthetic("wrong-digest", mutate_record=lambda record: record["original_line_sha256"].__setitem__(2, "0" * 64)), "AUDIT_RANGE_DIGEST")

def fake_matching_sha(record):
    parts = [json.loads(line) for line in original_lines]
    parts[2]["payload"]["content"][0]["text"] += "X"
    captured = b"".join((json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode() for row in parts)
    record["original_capture_ref"] = fake_ref("matching-digest-capture", captured)
    record["original_line_sha256"] = [hashlib.sha256(line).hexdigest() for line in captured.splitlines(keepends=True)]
    return captured

def reject_forged_three_lines():
    record = copy.deepcopy(peer)
    captured = fake_matching_sha(record)
    ref_raw = (json.dumps(record, ensure_ascii=False) + "\n").encode()
    ref = fake_ref("matching-digest-binding", ref_raw)
    data = {ref["path"]: ref_raw, record["original_capture_ref"]["path"]: captured}
    m.read_ref = lambda item: data[item["path"]] if item["path"] in data else original_read(item)
    try: m.actual_audit(ref, old_actor, peer["binding_sha256"])
    finally: m.read_ref = original_read

reject("fake-three-lines-even-matching-sha-rejected", reject_forged_three_lines, "ACTUAL_ROOT_AUDIT_BYTES")

new_choice = json.loads((N / "source.choice.json").read_bytes())
old_choice = json.loads((OLD / "source.choice.json").read_bytes())
check("three-fresh-run-ids", set(new_choice["selectors"]) == set(old_choice["selectors"]) and all(new_choice["selectors"][key]["run_id"] != old_choice["selectors"][key]["run_id"] for key in new_choice["selectors"]))
check("future-output-roots-absent", all(not Path(row[name]).exists() for row in new_choice["selectors"].values() for name in ("receipt_root", "scratch_root", "output_root")))
contract = json.loads((N / "root-calling-contract.json").read_bytes())
check("contract-binds-new-author", contract["author"] == contract["source_actor"] == new_actor)
check("contract-binds-all-new-source-files", all(contract["bound_source_refs"][key] == pin(N / name) for key, name in contract["source_file_bindings"].items()))
check("review-gate-unmodified", contract["execution_grant"] is False and contract["formal_case_accepted_delta"] == 0 and m.ROOT_THREAD_ID == peer["Root_thread_id"])

result = {"schema": "researchos.fullw09-v2-peer-audit-source-controls.v1", "scope": "SOURCE_ONLY_NO_PREPARE_NO_RUN_NO_NATIVE",
          "new_source_author": new_actor, "prior_source_author": old_actor, "prior_real_peer_binding_ref": peer_ref,
          "prior_real_peer_capture_ref": peer["original_capture_ref"], "count": len(rows),
          "pass": sum(row["passed"] for row in rows), "fail": sum(not row["passed"] for row in rows), "controls": rows,
          "prior_author_controls_69_preserved_not_recounted": True,
          "prior_independent_controls_112_preserved_not_recounted": True,
          "actual_prepare_run": False, "native_calls": 0, "Canon_modified": False,
          "new_author_actual_peer_delivery": "PENDING_REAL_ROOT_DELIVERY", "execution_grant": False}
path = N / "peer-audit-controls.json"
with path.open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print(json.dumps({"count": result["count"], "pass": result["pass"], "fail": result["fail"], "ref": pin(path)}, ensure_ascii=False))
