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
RBASE = BASE + "host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec/"
ABASE = BASE + "host_configuration_upgrade_executor_codex/test-scope-r276-180e5f4f0b424c7a8c7b8dbe1e4c52c0/"
WT = ROOT / ".local/worktrees/codex-w0599-host-configuration-upgrade"
CHECKOUT = ROOT / ".local/independent-configuration-9673a59f"
CANON = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode()


def save(n, v):
    with (OUT / n).open("xb") as f:
        f.write(enc(v))


def ref(p, expected=None):
    p = Path(str(p).replace("\\", "/"))
    raw = (ROOT / p).read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    if expected:
        assert h == expected, str(p)
    return {"path": p.as_posix(), "sha256": h, "bytes": len(raw)}


def import_author(r):
    p = Path(r["path"])
    raw = (WT / p).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == r["sha256"]
    target = ROOT / p
    if target.exists():
        assert target.read_bytes() == raw
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as f:
            f.write(raw)
    return ref(p, r["sha256"])


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert cp["revision"] == 280 and ow["revision"] == 108 and len(cp["failure_counters"]) == 234
request_ref = ref(RBASE + "development_fixture_recovery_request.json", "3509a073a61c4d54c5926237e5a57be0ee673bb92dabe5492d757c7b2ab72525")
failure_ref = ref(RBASE + "failure_origins.prerequisite.json", "ce556078a0b7cae55d7d6bd171bce24adfc9a0d7ae87e16d6271deeeb5528120")
request = json.loads((ROOT / request_ref["path"]).read_bytes())
assert request["candidate"] == "c82f73cc6699b564f1357472e2859b90cafe6b0a"
resource = request["resource"]
assert resource["path"] == "evaluation/development/jev-v2/dataset.json"
assert resource["sha256"] == "c4408fcca39320561ed03de0b56c2a9b8400dadf4eccd1b99802599e685ee979"
oid = subprocess.check_output(["git", "rev-parse", request["candidate"] + ":" + resource["path"]], cwd=ROOT).decode().strip()
raw = subprocess.check_output(["git", "cat-file", "blob", oid], cwd=ROOT)
assert oid == resource["git_blob_oid"] == "6b84e9099aa7e4d467b741a36c199c71d489f12a"
assert hashlib.sha256(raw).hexdigest() == resource["sha256"] and len(raw) == resource["bytes"] == 122103
assert CHECKOUT.resolve().is_relative_to(ROOT.resolve()) and not (CHECKOUT / resource["path"]).exists()
for n in ["original_closure", "after_failed_test", "test_binary"]:
    ref(request[n]["path"], request[n]["sha256"])
assert request["original_closure"]["sha256"] == request["after_failed_test"]["sha256"]
origin = request["origin"]
assert origin["exit"] == 1 and origin["counts"] == {"pass": 185, "fail": 6, "skip": 0}
assert len(origin["failed_leaves"]) == 5
for n in ["invocation", "stdout", "stderr"]:
    ref(origin[n]["path"], origin[n]["sha256"])
assert json.loads((ROOT / Path(origin["invocation"]["path"].replace("\\", "/"))).read_bytes())["exit"] == 1
author_raw = (WT / (ABASE + "new_failure_origin.json")).read_bytes()
author = json.loads(author_raw)
author_ref = import_author({"path": ABASE + "new_failure_origin.json", "sha256": hashlib.sha256(author_raw).hexdigest()})
for n in ["invocation", "stdout", "stderr", "source_after"]:
    import_author(author[n])
assert author["actual_exit"] == 1 and author["executed_test_count"] == 0
assert json.loads((ROOT / author["invocation"]["path"]).read_bytes())["exit"] == 1
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {"schema": "researchos.root.public-test-resource-recovery-scope.v1", "actor": "codex:/root", "reviewer": "codex:/root/w05_merge_review", "at": now, "card": "W05-99", "candidate": request["candidate"], "checkout": CHECKOUT.relative_to(ROOT).as_posix(), "request_ref": request_ref, "failure_ref": failure_ref, "exact_one_public_resource": resource, "source_writes": 0, "recovery": "Export only exact immutable candidate Git blob into own independent checkout. No holdout/private/native credential/model/provider access; no fixture synthesis or source/test edits.", "validation": "Freeze augmented actual complete current executable/source/compiler/tool/test-runtime input vectors, including restored resource. Execute only the five listed prerequisite-blocked leaves with same ed5e46 binary; unchanged source and executable. Preserve original 185PASS/6FAIL raw and report coverage by unique original test names; do not relabel old raw as successful or rerun 185 passed tests.", "only_failed_leaves": origin["failed_leaves"], "one_recovery_invocation": True, "stop": "First unexplained failure stops; no automatic second repair or resource extension. All12 source gates and current Main composition remain required.", "original_schema14_active_recovery": "INHERITED_OPEN_UNCHANGED", "model_calls": 0, "worker_starts": 0, "paid_calls": 0, "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
save("root_task_packet_locator_observation.json", {"schema": "researchos.transcript-observation.v1", "tool_chunk_id": "2b37cc", "actual_exit": 1, "failed_command": "rg -n add_parser|next|project_identity D:/作品集/ResearchOS/research-os/tools/task_packet.py", "cause": "Wrong repository path: task_packet.py is in original SPEC/tools. Other independent reads in the batch succeeded.", "raw_captured": False, "raw_limit": "Tool transcript retained, no fabricated original raw.", "product_tests_executed": 0, "mutations": 0})
root_failure_ref = ref((OUT / "root_task_packet_locator_observation.json").relative_to(ROOT).as_posix())
old = copy.deepcopy(cp["failure_counters"])
new = [("W05-99/configuration-test-args/" + author["invocation"]["sha256"], "ACTUAL_COMMAND_ARGUMENT_FAILURE_BEFORE_ZERO_TESTS", author_ref, author), ("W05-99/configuration-independent-prerequisite/" + origin["invocation"]["sha256"], "ACTUAL_ONE_TEST_INVOCATION_PUBLIC_DEVELOPMENT_FIXTURE_MISSING", failure_ref, origin), ("W05-99/Root/task-packet-locator/2b37cc", "ACTUAL_READONLY_LOCATOR_EXIT1_TRANSCRIPT_ONLY", root_failure_ref, None)]
keys = {v.get("origin_key") for v in old}
for key, status, ev, detail in new:
    assert key not in keys
    item = {"origin_key": key, "attempts": 1, "retries_used": 0, "status": status, "evidence_ref": ev, "counter_reset": False, "formal_increment": 0}
    if detail is not None:
        item["detail"] = detail
    cp["failure_counters"].append(item)
assert cp["failure_counters"][:234] == old and len(cp["failure_counters"]) == 237
assert cp["failure_chains"]["W05-99/provider9-original-history-refusal"]["actual_failed_invocations"] == 5
for p, b in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(b)
cp.update(revision=281, expected_previous_revision=280, updated_at=now, updated_by="codex:/root")
ow.update(revision=109, amended_at=now, amended_by="codex:/root")
cp["work_in_progress"].update(configuration_development_recovery_scope_ref=scope_ref, configuration_final11_candidate=request["candidate"])
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "CONFIGURATION_PUBLIC_DEVELOPMENT_EXACT_BLOB_RECOVERY_REGISTERED", "scope_ref": scope_ref, "failure_origins": [234, 237], "failure_counting": "Author argument failure one, independent prerequisite test invocation one despite six inclusive FAIL events, Root readonly missing script path one. Original prefixes and model history5 retained.", "formal_increment": 0})
for v in [scope_ref, failure_ref, request_ref, author_ref, root_failure_ref]:
    if v["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(v["path"])
save("record.json", {"checkpoint": [280, 281], "ownership": [108, 109], "failure_origins": [234, 237], "scope_ref": scope_ref, "public_resource_git_sha_verified": True, "formal_increment": 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root281.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 281, "ownership": 109, "failure_origins": 237, "scope_ref": scope_ref, "formal_increment": 0}))
