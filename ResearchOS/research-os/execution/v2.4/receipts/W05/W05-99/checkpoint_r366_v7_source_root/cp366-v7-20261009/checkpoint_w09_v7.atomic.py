import sys
sys.dont_write_bytecode = True
import copy
import hashlib
import json
import types
from datetime import datetime, timezone
from pathlib import Path

R = Path("D:/作品集/ResearchOS/research-os")
B = R / "execution/v2.4/receipts/W05/W05-99"
O = Path(__file__).resolve().parent
CANON = [R / "execution/v2.4" / (n + ".json") for n in
         ("checkpoint", "path_ownership", "step_state", "commands")]
BEFORE = [
    ("2862e018e00c9a12a1e9ad88fb85d12c69cefd9098114fe9f29b05f863b5a725", 4279163),
    ("3ba05515053b60ba36ae3f09a2dc88d4af9861e86112b9ac7bcb33f3f8efbef5", 196536),
    ("fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149", 257446),
    ("b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129", 68156),
]
GP = B / "source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
TP = B / "mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
IDENTITY = R / "execution/project_identity.json"

def pin(p):
    p = Path(p).resolve(strict=True)
    with p.open("rb") as f:
        raw = f.read(256 * 1024 * 1024 + 1)
    assert len(raw) <= 256 * 1024 * 1024, "PIN_SIZE"
    return {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def verify(ref):
    assert isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"}, "REF_FIELDS"
    assert Path(ref["path"]).is_absolute() and type(ref["bytes"]) is int, "REF_TYPES"
    assert isinstance(ref["sha256"], str) and len(ref["sha256"]) == 64
    assert all(c in "0123456789abcdef" for c in ref["sha256"]), "REF_HASH"
    result = pin(ref["path"])
    assert result == ref, "REF_PIN"
    return result

def save(name, value):
    with (O / name).open("xb") as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return pin(O / name)

def module(p, raw):
    m = types.ModuleType("cp366_" + p.stem)
    m.__file__ = str(p)
    sys.modules[m.__name__] = m
    exec(compile(raw, str(p), "exec"), m.__dict__)
    return m

def transform(c, o, facts, fr, old_c, old_o):
    assert c == old_c and o == old_o and c["revision"] == 365 and o["revision"] == 169
    assert len(c["failure_counters"]) == 923
    assert c["work_in_progress"]["construction_active_parents"] == ["W05", "W09"]
    pending = facts["diagnostics"]
    assert [v["ordinal"] for v in pending] == list(range(926, facts["highest_observed_ordinal"] + 1))
    assert facts["next_failure_ordinal"] == facts["highest_observed_ordinal"] + 1
    assert facts["registered_after"] == 923 + len(pending)
    keys = {v.get("origin_key") for v in c["failure_counters"]}
    for v in pending:
        ref = verify(v["origin_ref"])
        n = v["ordinal"]
        key = hashlib.sha256((ref["sha256"] + "#" + str(n)).encode()).hexdigest()
        assert key not in keys
        keys.add(key)
        c["failure_counters"].append({
            "origin_key": key, "evidence_ref": ref,
            "original_payload": {
                "observed_ordinal": n, "immutable_origin_ref": ref,
                "actual_outer_exit": v["actual_outer_exit"],
                "actual_python_exit": v["actual_python_exit"],
                "actual_native_exit": v["actual_native_exit"],
                "diagnostic": v["description"], "origin_selector": v["origin_selector"],
                "exit_qualification": v["exit_qualification"]},
            "counted_once": True, "counter_reset": False, "automatic_retry": False})
    assert c["failure_counters"][:923] == old_c["failure_counters"]
    scope = facts["w09_scope_registration"]
    assert scope["owner_subtask"]["owner"] == "codex:/root"
    assert scope["owner_subtask"]["current_source_writer"] is None
    assert scope["worker"]["step_id"] == "W09-99"
    assert scope["worker"]["slice_id"] == "C19_FIXTURE_PRODUCER"
    assert scope["worker"]["owner"] == "codex:/root"
    assert scope["worker"]["state"] == "ROOT_REGISTERED_PENDING_ACTUAL"
    workers = [i for i, w in enumerate(c["workers"])
               if w.get("step_id") == "W09-99" and w.get("slice_id") == "C19_FIXTURE_PRODUCER"]
    assert len(workers) == 1
    i = workers[0]
    old_worker = copy.deepcopy(c["workers"][i])
    old_owner = copy.deepcopy(o["card_path_bindings"]["W09-99"]["subtasks"]["c19_fixture_producer"])
    assert scope["worker"]["scope_ref"] == scope["scope_ref"]
    assert scope["owner_subtask"]["scope_ref"] == scope["scope_ref"]
    assert scope["scope_ref"] != old_worker["scope_ref"]
    assert scope["owner_subtask"]["worktree_root"] != old_owner["worktree_root"]
    assert set(scope["owner_subtask"]["fixed_write_roots"]) == set(old_owner["fixed_write_roots"])
    assert all(scope["owner_subtask"]["fixed_write_roots"][k] != old_owner["fixed_write_roots"][k]
               for k in old_owner["fixed_write_roots"])
    c["workers"][i] = copy.deepcopy(scope["worker"])
    o["card_path_bindings"]["W09-99"]["subtasks"]["c19_fixture_producer"] = copy.deepcopy(scope["owner_subtask"])
    wip = c["work_in_progress"]
    assert "mu_sdk_r366" not in wip
    assert set(facts["work_in_progress"]) == {"mu_sdk_r366"}
    wip.update(copy.deepcopy(facts["work_in_progress"]))
    wip["mu_sdk_r366"]["previous_w09_worker"] = old_worker
    wip["mu_sdk_r366"]["previous_w09_owner"] = old_owner
    wip.update(r366_registered_failure_count=len(c["failure_counters"]),
               r366_highest_observed_diagnostic_ordinal_at_cutoff=facts["highest_observed_ordinal"],
               r366_next_failure_ordinal_at_cutoff=facts["next_failure_ordinal"],
               mu_sdk_r366_facts_ref=fr, later_diagnostics_observed_after_cutoff=[],
               root_next_failure_ordinal_live=facts["next_failure_ordinal"])
    stamp = datetime.now(timezone.utc).isoformat()
    c.update(expected_previous_revision=365, revision=366, updated_at=stamp, updated_by="codex:/root")
    c["note"] = facts["checkpoint_note"]
    o.update(revision=170, updated_at=stamp, updated_by="codex:/root")
    inverse_c = copy.deepcopy(c)
    inverse_c["failure_counters"] = copy.deepcopy(old_c["failure_counters"])
    inverse_c["workers"][i] = old_worker
    inverse_c["work_in_progress"] = copy.deepcopy(old_c["work_in_progress"])
    for k in ("expected_previous_revision", "revision", "updated_at", "updated_by", "note"):
        inverse_c[k] = old_c[k]
    inverse_o = copy.deepcopy(o)
    inverse_o["card_path_bindings"]["W09-99"]["subtasks"]["c19_fixture_producer"] = old_owner
    for k in ("revision", "updated_at", "updated_by"):
        inverse_o[k] = old_o[k]
    assert inverse_c == old_c and inverse_o == old_o, "FULL_CANONICAL_INVERSE"
    return c, o

def main():
    assert len(sys.argv) == 3, "FACTS_SHA256 FACTS_BYTES"
    fr = verify({"path": str(O / "checkpoint.execution.facts.json"),
                 "sha256": sys.argv[1], "bytes": int(sys.argv[2])})
    facts = json.loads(Path(fr["path"]).read_bytes())
    assert facts["schema"] == "researchos.root-cp366-w09-v7-facts.v1"
    assert facts["formal_acceptance"] is False
    refs_c = [pin(p) for p in CANON]
    assert [(v["sha256"], v["bytes"]) for v in refs_c] == BEFORE
    assert refs_c == facts["canonical_refs"]
    old = [p.read_bytes() for p in CANON]
    old_c, old_o = [json.loads(raw) for raw in old[:2]]
    assert old_c["project_id"] == "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
    assert old_c["head"] == "adc460c2138528f163f7fdab5e8d81dde157b7fb"
    assert (pin(IDENTITY)["sha256"], pin(IDENTITY)["bytes"]) == (
        "03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec", 420)
    assert pin(sys.executable)["sha256"] == "cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
    assert pin(GP)["sha256"] == "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
    assert pin(TP)["sha256"] == "094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
    gm = module(GP, GP.read_bytes())
    tm = module(TP, TP.read_bytes())
    refs = [fr, pin(__file__), pin(sys.executable), pin(IDENTITY), pin(GP), pin(TP), *refs_c[2:]]
    for item in facts["reviews"]:
        refs.extend([verify(item["handoff_ref"]), verify(item["manifest_ref"])])
        members = json.loads(Path(item["manifest_ref"]["path"]).read_bytes())["members"]
        for member in (members.values() if isinstance(members, dict) else members):
            normalized = {k: member[k] for k in ("path", "sha256", "bytes")}
            normalized["sha256"] = normalized["sha256"].removeprefix("sha256:")
            refs.append(verify(normalized))
    refs.extend(verify(v["origin_ref"]) for v in facts["diagnostics"])
    refs.extend(verify(v) for v in facts["actual_refs"])
    refs.append(verify(facts["w09_scope_registration"]["scope_ref"]))
    for mod in list(sys.modules.values()):
        for field in ("__file__", "__cached__"):
            p = getattr(mod, field, None)
            if p and Path(p).is_file():
                refs.append(pin(p))
    unique = {}
    for ref in refs:
        key = ref["path"].casefold()
        assert key not in unique or unique[key] == ref
        unique[key] = ref
    guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    guard.acquire(list(unique.values()))
    try:
        transaction = tm.update_pair(refs_c[:2], lambda c, o:
            transform(c, o, facts, fr, old_c, old_o), O, "activate")
        assert [p.read_bytes() for p in CANON[2:]] == old[2:]
        new_c = json.loads(CANON[0].read_bytes())
        assert new_c["revision"] == 366 and json.loads(CANON[1].read_bytes())["revision"] == 170
    finally:
        cleanup = guard.close()
        cleanup_ref = save("source_guard.cleanup.actual.json", cleanup)
        assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"] == 0
    def failure_array(raw):
        text = raw.decode("utf-8")
        start = text.index("[", text.index('"failure_counters":'))
        value, end = json.JSONDecoder().raw_decode(text[start:])
        return text[start:start + end]
    prefix = failure_array(old[0]).rstrip()[:-1].rstrip()
    assert failure_array(CANON[0].read_bytes()).startswith(prefix + ",")
    proof = save("canonical_pair.actual.json", {
        "transaction": transaction, "checkpoint_ref": pin(CANON[0]),
        "ownership_ref": pin(CANON[1]), "old923_semantic_equal": True,
        "old923_raw_array_prefix_preserved": True,
        "new_original_ordinals": [v["ordinal"] for v in facts["diagnostics"]],
        "registered_failures": len(new_c["failure_counters"]),
        "highest_registered_ordinal": facts["highest_observed_ordinal"],
        "next_failure_ordinal_at_cutoff": facts["next_failure_ordinal"],
        "formal_acceptance": False})
    resume = save("RESUME.r366.original.json", {
        "schema": "researchos.root-resume-w09-v7.v1",
        "checkpoint_ref": pin(CANON[0]), "ownership_ref": pin(CANON[1]),
        "historical_accepted_parents": 6, "current_formal_accepted": 0,
        "required_parents": 22, "required_formal": 42,
        "registered_failures": len(new_c["failure_counters"]),
        "next_failure_ordinal_at_cutoff": facts["next_failure_ordinal"],
        "current_scope": facts["w09_scope_registration"]["scope_ref"],
        "work_in_progress": facts["work_in_progress"],
        "counter_reset": False, "completion_asserted": False,
        "proof_ref": proof, "next_action": facts["next_action"]})
    save("handoff.actual.json", {"status": "ADMIN_CANONICAL_SAVED_NO_PRODUCT_ACCEPTANCE",
         "checkpoint_ref": pin(CANON[0]), "resume_ref": resume, "proof_ref": proof,
         "guard_cleanup_ref": cleanup_ref})
    print(json.dumps({"checkpoint_ref": pin(CANON[0]), "ownership_ref": pin(CANON[1]),
                      "resume_ref": resume, "formal_acceptance": False}), flush=True)

if __name__ == "__main__":
    main()
