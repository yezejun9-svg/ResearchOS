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
OLD_SCOPE = R / "execution/v2.4/receipts/W09/W09-99/integration_codex/w09c19-root-scope-1791524400000/scope-registration.root.json"
OLD_SCOPE_REF = {"path": str(OLD_SCOPE.resolve()),
    "sha256": "17b5ebc80477f6ed9012eb751758a8ef9724956cd5f999ee3dd65f37cfa100f7", "bytes": 4891}

def pin(p):
    p = Path(p).resolve(strict=True)
    with p.open("rb") as f:
        raw = f.read(256 * 1024 * 1024 + 1)
    assert len(raw) <= 256 * 1024 * 1024, "PIN_SIZE"
    return {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def read_ref(ref):
    assert isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"}, "REF_FIELDS"
    assert Path(ref["path"]).is_absolute() and type(ref["bytes"]) is int, "REF_TYPES"
    assert 0 <= ref["bytes"] <= 256 * 1024 * 1024, "REF_SIZE"
    assert isinstance(ref["sha256"], str) and len(ref["sha256"]) == 64
    assert all(c in "0123456789abcdef" for c in ref["sha256"]), "REF_HASH"
    p = Path(ref["path"]).resolve(strict=True)
    assert str(p) == ref["path"], "REF_CANONICAL_PATH"
    with p.open("rb") as f:
        raw = f.read(ref["bytes"] + 1)
    assert len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"], "REF_PIN"
    return raw

def verify(ref):
    read_ref(ref)
    return ref

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

def transform(c, o, facts, fr, old_c, old_o, scope_object, old_scope_object):
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
    owner_mutable = {"scope_ref", "source_handoff_ref", "source_manifest_ref",
                     "independent_source_review_ref", "independent_source_manifest_ref",
                     "source_paths", "worktree_root", "fixed_write_roots"}
    worker_mutable = {"worktree", "scope_ref", "independent_source_review_ref"}
    new_owner, new_worker = scope["owner_subtask"], scope["worker"]
    assert set(new_owner) == set(old_owner) and set(new_worker) == set(old_worker), "OWNER_WORKER_FIELDS"
    assert all(new_owner[k] == old_owner[k] for k in old_owner if k not in owner_mutable), "OWNER_PROTECTED_FIELDS"
    assert all(new_worker[k] == old_worker[k] for k in old_worker if k not in worker_mutable), "WORKER_PROTECTED_FIELDS"
    assert new_worker["worktree"] == new_owner["worktree_root"], "WORKER_OWNER_ROOT"
    assert new_worker["independent_source_review_ref"] == new_owner["independent_source_review_ref"]
    candidate = Path(new_owner["worktree_root"]).resolve()
    expected_candidate = (R / ".local/worktrees/w09c19v7-1a11f30").resolve()
    assert candidate == expected_candidate, "FIXED_V7_CANDIDATE"
    fresh = {
        "candidate": str(R / ".local/worktrees/w09c19v7-1a11f30"),
        "isolation_receipt": str(R / "execution/v2.4/receipts/W09/W09-99/integration_codex/w09c19v7-isolation-1a11f30"),
        "producer_receipt": str(R / "execution/v2.4/receipts/W09/W09-99/integration_codex/w09c19v7-producer-1a11f30"),
        "prepare_environment": str(R / ".local/w09c19v7-isolation-env-1a11f30"),
        "producer_environment": str(R / ".local/w09c19v7-producer-env-1a11f30"),
    }
    assert all(Path(new_owner["fixed_write_roots"][k]).resolve() == Path(v).resolve()
               for k, v in fresh.items()), "FIXED_V7_WRITE_ROOTS"
    relative = ["internal/domain/domain_test.go", "internal/domain/retrieval_test.go",
                "ops/ci/retrieval.py", "internal/domain/w09_evidence_export_test.go",
                "ops/ci/w09_formal_router.py", "ops/ci/w09_evidence_closure.py"]
    assert len(new_owner["source_paths"]) == len(relative) and [
        Path(p).resolve() for p in new_owner["source_paths"]] == [
        candidate / p for p in relative], "SIX_FIXED_SOURCE_PATHS"
    for key in ("source_handoff_ref", "source_manifest_ref",
                "independent_source_review_ref", "independent_source_manifest_ref"):
        assert new_owner[key] == scope_object[key], "SCOPE_SOURCE_REVIEW_REF"
    assert scope_object["candidate_root"] == new_owner["worktree_root"], "SCOPE_CANDIDATE"
    assert scope_object["permitted_candidate_source_paths"] == new_owner["source_paths"], "SCOPE_SIX_SOURCE_PATHS"
    assert scope_object["fixed_write_roots"] == new_owner["fixed_write_roots"], "SCOPE_FIVE_WRITE_ROOTS"
    allowed_scope_changes = {"candidate_root", "source_handoff_ref", "source_manifest_ref",
        "independent_source_review_ref", "independent_source_manifest_ref",
        "permitted_candidate_source_paths", "fixed_write_roots"}
    assert set(scope_object) == set(old_scope_object), "SCOPE_FIELDS"
    assert all(scope_object[k] == old_scope_object[k] for k in old_scope_object
               if k not in allowed_scope_changes), "SCOPE_PROTECTED_FIELDS"
    assert scope_object["schema"] == "researchos.root-w09-c19-isolated-producer-scope.v1"
    assert scope_object["executor"] == scope_object["issued_by"] == "codex:/root"
    assert scope_object["main_adoption_authorized_by_this_scope"] is False
    assert scope_object["formal_consumer_execution_authorized_by_this_scope"] is False
    assert scope_object["formal_acceptance"] is False and scope_object["parent_acceptance"] is False
    assert scope_object["new_external_model_call"] is False and scope_object["original_trial_unchanged"] is True
    source_pairs = {(v["handoff_ref"]["path"], v["manifest_ref"]["path"]) for v in facts["reviews"]}
    assert (new_owner["source_handoff_ref"]["path"], new_owner["source_manifest_ref"]["path"]) in source_pairs
    assert (new_owner["independent_source_review_ref"]["path"],
            new_owner["independent_source_manifest_ref"]["path"]) in source_pairs
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
    facts_raw = read_ref(fr)
    facts = json.loads(facts_raw)
    assert facts["schema"] == "researchos.root-cp366-w09-v7-facts.v1"
    assert facts["formal_acceptance"] is False
    refs_c = [{"path": str(p.resolve()), "sha256": sha, "bytes": size}
              for p, (sha, size) in zip(CANON, BEFORE)]
    assert refs_c == facts["canonical_refs"]
    old = [read_ref(ref) for ref in refs_c]
    old_c, old_o = [json.loads(raw) for raw in old[:2]]
    assert old_c["project_id"] == "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
    assert old_c["head"] == "adc460c2138528f163f7fdab5e8d81dde157b7fb"
    assert (pin(IDENTITY)["sha256"], pin(IDENTITY)["bytes"]) == (
        "03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec", 420)
    assert pin(sys.executable)["sha256"] == "cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
    assert pin(GP)["sha256"] == "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
    assert pin(TP)["sha256"] == "094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
    gp_ref = {"path": str(GP.resolve()), "sha256": "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85", "bytes": 11404}
    tp_ref = {"path": str(TP.resolve()), "sha256": "094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9", "bytes": 6877}
    gm = module(GP, read_ref(gp_ref))
    tm = module(TP, read_ref(tp_ref))
    refs = [fr, pin(__file__), pin(sys.executable), pin(IDENTITY), pin(GP), pin(TP), *refs_c[2:]]
    for item in facts["reviews"]:
        refs.extend([verify(item["handoff_ref"]), verify(item["manifest_ref"])])
        members = json.loads(read_ref(item["manifest_ref"]))["members"]
        for member in (members.values() if isinstance(members, dict) else members):
            normalized = {k: member[k] for k in ("path", "sha256", "bytes")}
            normalized["sha256"] = normalized["sha256"].removeprefix("sha256:")
            refs.append(verify(normalized))
    refs.extend(verify(v["origin_ref"]) for v in facts["diagnostics"])
    refs.extend(verify(v) for v in facts["actual_refs"])
    scope_ref = verify(facts["w09_scope_registration"]["scope_ref"])
    refs.extend([scope_ref, verify(OLD_SCOPE_REF)])
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
        assert guard.get_buffer(fr["path"]) == facts_raw, "HELD_FACTS_BYTES"
        facts = json.loads(guard.get_buffer(fr["path"]))
        scope_object = json.loads(guard.get_buffer(scope_ref["path"]))
        old_scope_object = json.loads(guard.get_buffer(OLD_SCOPE_REF["path"]))
        transaction = tm.update_pair(refs_c[:2], lambda c, o:
            transform(c, o, facts, fr, old_c, old_o, scope_object, old_scope_object), O, "activate")
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
