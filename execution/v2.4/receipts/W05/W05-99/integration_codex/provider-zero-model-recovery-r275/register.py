import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
PRE = BASE + "provider_binding_zero_model_adjudication_codex/d7f95235-03e1-464f-b3b0-374ca7394fda/"
paths = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def save(n, v):
    with (OUT / n).open("xb") as f:
        f.write((json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode())


def ref(p, expected=None):
    h = hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    if expected:
        assert h == expected, p
    return {"path": p, "sha256": h}


before = {p: p.read_bytes() for p in paths}
cp, ow = [json.loads(before[p]) for p in paths[:2]]
assert cp["revision"] == 274 and ow["revision"] == 102 and len(cp["failure_counters"]) == 223
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "26e1043751c989d4e6016a76f113e343c9e38382"
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
failure = ref(PRE + "failure_origins.precompile.json", "5e8abd4d170f15efef0875fcf07f52afa739a3f2c0f5b60e30a866f86a4795c2")
stop = ref(PRE + "stopped_before_compile.json", "4d7cb19ca8dd6aa1718ca227cb3e0a5a26722526e76cdac99e4101b3bdc76bbf")
origins = json.loads((ROOT / failure["path"]).read_bytes())
save("failure-import-observation.json", {"original": origins, "source_ref": failure, "note": "Preserve actual outer0/component rg IO error distinction and original raw limitations. No held history-chain retry or product test occurred."})
old = copy.deepcopy(cp["failure_counters"])
new = {"origin_key": "W05-99/root/archive-r272-guessed-runpy-read", "attempts": 1, "retries_used": 0, "status": "ORIGINAL_CONSOLE_READONLY_LOCATOR_ERROR_NO_RAW_CAPTURE", "detail": "Root Get-Content guessed source-evidence-archive-r272/run.py after listing entire directory; it did not exist. Original tool output stays in conversation. Subsequently rg --files --glob '*.py' located actual archive.py and driver.py. No raw reconstruction, source edit or product execution.", "counter_reset": False, "formal_increment": 0}
assert new["origin_key"] not in {v.get("origin_key") for v in old}
cp["failure_counters"].append(new)
origin_items = origins.get("new_tooling_origins", origins.get("origins", origins.get("entries")))
assert isinstance(origin_items, list) and len(origin_items) == 3
for i, item in enumerate(origin_items):
    for n in ["invocation", "stdout", "stderr"]:
        if n in item:
            target = Path(item[n]["path"])
            assert target.resolve().is_relative_to(ROOT.resolve())
            assert hashlib.sha256(target.read_bytes()).hexdigest() == item[n]["sha256"]
    key = "W05-99/p12-independent-precompile/" + str(item.get("id", i))
    assert key not in {v.get("origin_key") for v in cp["failure_counters"]}
    cp["failure_counters"].append({"origin_key": key, "attempts": 1, "retries_used": 0, "status": "PRECOMPILE_OR_READONLY_TOOLING_ORIGIN_ACTUAL_OUTER_COMPONENT_EXIT_DISTINCTION_PRESERVED", "evidence_ref": failure, "detail": item, "counter_reset": False, "formal_increment": 0})
assert len(cp["failure_counters"]) == 227 and cp["failure_counters"][:223] == old
candidate = "976c8c9a6bdf8703475e02b79b77f4c5fab2d650"
files = []
for name in ["generate_other.go", "generate_windows.go", "generator.go", "rubric.go", "truth.go"]:
    p = "evaluation/holdout/jev/" + name
    raw = subprocess.check_output(["git", "show", candidate + ":" + p], cwd=ROOT)
    files.append({"path": p, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "source": "immutable Git public non-test compilation dependency only"})
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {"schema": "researchos.root.compilation-resource-recovery.v1", "actor": "codex:/root", "executor": "codex:/root/w05_merge_review", "at": now, "parent": "W05", "card": "W05-99", "source_candidate": candidate, "original_scope_ref": ref(BASE + "integration_codex/provider-zero-model-scope-r274/scope_registration.json", "d6b2c180cc8132fe5098b6b5e7a61884e6df984486e5a913fe9e545723761b28"), "stop_ref": stop, "failure_ref": failure, "recovery_files": files, "allowed_write": "Only matching exact public candidate blobs into independent sparse checkout, new attempt2 receipt namespace/cache/driver/binary; source9 immutable", "actual_private_or_holdout_data_reads": 0, "generator_or_DPAPI_function_calls": 0, "generator_test_execution": 0, "model_calls": 0, "worker_starts": 0, "held_positive_execution": 0, "original_history_failures": 5, "counter_reset": False, "next": "One new Go-list precompile attempt; then full actual compilation vector and test binary freeze before registered six-DB P12 controls. Further missing package or prerequisite failure stops; no self-expanded recovery. Preserve originals/outer-component exit facts.", "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
sub = ow["card_path_bindings"]["W05-99"]["subtasks"]["provider_transport_reasoning_binding"]
sub.update(zero_model_precompile_stop_ref=stop, zero_model_public_compilation_recovery_ref=scope_ref, zero_model_scope_state="EXACT5_PUBLIC_GIT_DEPENDENCIES_CAUSAL_RECOVERY_AFTER_PRECOMPILE_STOP", author_retry_authorized=False)
cp.update(revision=275, expected_previous_revision=274, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=103, amended_at=now, amended_by="codex:/root")
cp["next_command"] = "P12 candidate-only zero-model precompile stopped original missing public Go package, exact5Git dependency recovery registered; complete one causal precompile/frozen driver then at most prior six-DB controls, stop unexpected accept. Original-history5 held. MainCLI234 noSourcechange receiptarchive26e; schema23isolated old17regressions, fixedhistorical14resource optionalenv, fullcurrent nonself beforeMain23. F08 future14/configure onlyreadonlyscope.22parents/42CURRENT required."
cp["note"] = "223failureprefix immutable +oneRootmissing-runpy readonly observation+threeP12 precompile/locator origins=227, outer0 versus componentIOerror/raw limitations preserved. No P12 test/model/worker or heldpositive executed beforestop. Root causal recovery limited to5 immutable public non-test Go package sources; no actual held/private dataset/generator/DPAPI access. Mainreceipt359archive26e sourceunchanged and old11deletionsprotected."
cp["work_in_progress"].update(status="P12_EXACT5_PUBLIC_COMPILATION_RECOVERY_SCHEMA23_OLD_REGRESSION_BOUNDARIES_PENDING", next_action=cp["next_command"], provider_zero_model_recovery_ref=scope_ref)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "P12_PRECOMPILE_MISSING_PUBLIC_PACKAGE_EXACT5_CAUSAL_RECOVERY_ORIGINAL_HISTORY5_HELD", "scope_ref": scope_ref, "failure_origins": [223, 227], "formal_increment": 0})
for v in [scope_ref, stop, failure]:
    if v["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(v["path"])
save("record.json", {"checkpoint": [274, 275], "ownership": [102, 103], "failure_origins": [223, 227], "scope_ref": scope_ref, "main_head": head, "formal_increment": 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, v in zip(paths[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root275.tmp")
    with tmp.open("xb") as f:
        f.write((json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode())
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in paths[2:])
print(json.dumps({"checkpoint": 275, "ownership": 103, "failure_origins": 227, "scope_ref": scope_ref, "formal_increment": 0}))
