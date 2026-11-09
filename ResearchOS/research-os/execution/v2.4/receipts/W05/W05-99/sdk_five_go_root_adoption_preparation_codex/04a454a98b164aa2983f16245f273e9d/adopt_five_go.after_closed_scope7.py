"""Integrate the five independently reviewed Go proposals after Scope7 failed lease closes."""
import sys
sys.dont_write_bytecode = True
import argparse, hashlib, json, os
from pathlib import Path

ROOT = Path("D:/作品集/ResearchOS/research-os")
OUT = Path(__file__).resolve().parent
PREPARATION_SHA = "e064e1cdac43f479d224b3d65fa8422707a5f93ce45b5296feb73a53606ec318"
TARGETS = ("internal/host/vault.go", "internal/host/host.go", "apps/control/main.go",
           "internal/domain/runtime_qualification.go", "apps/cli/cli_stream.go")
STATE = "FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD"

def need(value, message):
    if not value:
        raise RuntimeError(message)

def path_for(value):
    p = Path(value)
    p = p if p.is_absolute() else ROOT / p
    p = p.resolve(strict=True)
    need(ROOT in p.parents and p.is_file() and not p.is_symlink(), "repository file boundary")
    return p

def verify(ref):
    p = path_for(ref["path"])
    b = p.read_bytes()
    need(len(b) == ref["bytes"] and hashlib.sha256(b).hexdigest() == ref["sha256"],
         "pinned bytes changed: " + ref["path"])
    return b

def ref_for(path):
    b = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

def save(name, value):
    p = OUT / name
    b = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with p.open("xb") as f:
        f.write(b)
        f.flush()
        os.fsync(f.fileno())
    return ref_for(p)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--closure-ref", required=True)
    a = ap.parse_args()
    raw = (OUT / "preparation.json").read_bytes()
    need(hashlib.sha256(raw).hexdigest() == PREPARATION_SHA, "preparation bytes")
    prep = json.loads(raw)
    need(tuple(x["target"] for x in prep["mapping"]) == TARGETS, "exact five targets")
    closure_ref = json.loads(a.closure_ref)
    closure = json.loads(verify(closure_ref))
    need(closure["schema"] == "researchos.scope7-failed-lease-close-cas-verified.v1"
         and closure["actor"] == "codex:/root" and closure["after"] == [340, 168, 672]
         and closure["old_lease_closed_failed"] is True and closure["execution_grant"] is False
         and closure["formal_increment"] == 0 and closure["counter_reset"] is False,
         "actual failed Scope7 lease closure")
    refs = closure["canonical_refs"]
    need([Path(x["path"]).name for x in refs] ==
         ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"],
         "canonical reference order")
    originals = [verify(x) for x in refs]
    cp, ow = map(json.loads, originals[:2])
    need(cp["revision"] == 340 and ow["revision"] == 168
         and len(cp["failure_counters"]) == 672 and cp["head"] == prep["old_head"],
         "canonical tuple and source head")
    need(cp["work_in_progress"]["desktop58_finite_validation_state"] == STATE
         and ow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]["state"] == STATE,
         "old Scope7 lease remains closed failed")
    for x in [prep["source_review_ref"], prep["adoption_input_review_ref"]]:
        verify(x)
    writes = []
    for row in prep["mapping"]:
        target = path_for(row["target"])
        need(verify(row["before_ref"]) == verify(row["backup_ref"]) == target.read_bytes(),
             "Main before differs from independent baseline")
        after = verify(row["proposal_ref"])
        need(after == verify(row["prepared_ref"]), "prepared Go differs from reviewed proposal")
        writes.append((row, target, after))
    intent = save("main-adoption.started.json", {"schema": "researchos.sdk-five-go-main-adoption-intent.v1",
        "actor": "codex:/root", "closure_ref": closure_ref, "canonical_refs": refs,
        "preparation_ref": ref_for(OUT / "preparation.json"), "targets": list(TARGETS),
        "formal_acceptance_delta": 0, "provider_requests": 0, "automatic_retry": False})
    for i, (row, target, after) in enumerate(writes):
        need(target.read_bytes() == verify(row["before_ref"]), "target changed before write")
        need([verify(x) for x in refs] == originals, "canonical changed during integration")
        tmp = OUT / (str(i + 1) + ".integration.tmp")
        with tmp.open("xb") as f:
            f.write(after)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)
        need(target.read_bytes() == after, "target write verification")
        save(str(i + 1) + ".main-adoption.write.done.json",
             {"target_ref": ref_for(target), "backup_ref": row["backup_ref"], "intent_ref": intent})
    need(all(target.read_bytes() == after for _, target, after in writes), "five final Go bytes")
    need([verify(x) for x in refs] == originals, "canonical post-integration changed")
    result = save("main-adoption.closed.json", {"schema": "researchos.sdk-five-go-main-adoption-result.v1",
        "actor": "codex:/root", "status": "SOURCE_INTEGRATED_PENDING_BUILD_AND_RUNTIME",
        "targets": [ref_for(target) for _, target, _ in writes], "canonical_unchanged": True,
        "closure_ref": closure_ref, "intent_ref": intent, "main_head_before": prep["old_head"],
        "new_commit": None, "provider_requests": 0, "formal_acceptance_delta": 0,
        "no_automatic_rollback": True})
    print(json.dumps({"result_ref": result, "main_files_changed": 5}, ensure_ascii=False))

if __name__ == "__main__":
    main()
