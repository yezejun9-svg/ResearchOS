import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent / "attempt2"
OUT.mkdir()
BASE = "execution/v2.4/receipts/W05/W05-99/"
CP, OW, ST, CM = [ROOT / ("execution/v2.4/" + name) for name in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write(enc(value))


def ref(relative, expected=None):
    digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if expected:
        assert digest == expected, relative
    return {"path": relative, "sha256": digest}


before = {path: path.read_bytes() for path in [CP, OW, ST, CM]}
cp, ow = json.loads(before[CP]), json.loads(before[OW])
assert cp["revision"] == 271 and ow["revision"] == 99 and len(cp["failure_counters"]) == 206
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "396287cc5427eb125aaedb8a2b7fadf63e6b9322"
for path, raw in before.items():
    with (OUT / (path.stem + ".original.json")).open("xb") as stream:
        stream.write(raw)
prefix = BASE + "cli_read_interrupt_source_review_codex/c5dc6318-b068-4630-81ee-21ae287b842d/"
review_ref = ref(prefix + "source_review.json", "ecfb699818af3fae4aaf404263b0752382984f2f3dbbc3f21e3b3f2d91eaf0f9")
review = json.loads((ROOT / review_ref["path"]).read_bytes())
assert review["decision"] == "SOURCE_READY_L02_EXACT4_CURRENT_STREAM_COMPOSITION"
assert review["candidate_commit"] == "f565599af3679fef6d5233fe27d16b8c92a61db2"
validation = review["actual_validation"]
assert validation["full_exit"] == validation["original_probe_exit"] == 0 and validation["input_count"] == 39065 and not validation["drift"]
assert validation["counts"]["full-cli"] == {"pass":234,"fail":0,"skip":0,"top_pass":67}
failure_ref = ref(prefix + "failure_origins.json", "5befb7800725425768702d3833311ca4de71e1d566698be33637708791f9d9c9")
failures = json.loads((ROOT / failure_ref["path"]).read_bytes())
assert len(failures["new_independent_origins"]) == 3
provider_wt = ROOT / ".local/worktrees/codex-w0599-provider-binding"
provider_prefix = BASE + "provider_binding_executor_codex/provider-39d6478d4a884156b0881788325e4c63/"
provider_path = provider_prefix + "failure_origins.json"
provider_raw = (provider_wt / provider_path).read_bytes()
assert hashlib.sha256(provider_raw).hexdigest() == "4ba98ed94fe1438f952a0bc792808f989a45a01a90203405578dbbb46dfdcd23"
provider_failures = json.loads(provider_raw)
assert len(provider_failures["entries"]) == 9 and provider_failures["history_chain"]["same_cause_failures"] == 5
assert provider_failures["history_chain"]["parent_stop_applied"]
public = {provider_path: provider_raw}
for item in provider_failures["entries"]:
    assert item["exit"] == 1
    for key in ["origin", "invocation", "stdout", "stderr"]:
        file = item[key]
        assert file["path"].startswith(provider_prefix)
        raw = (provider_wt / file["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == file["sha256"]
        public[file["path"]] = raw
for relative, raw in public.items():
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.is_file() and target.read_bytes() == raw
    else:
        with target.open("xb") as stream:
            stream.write(raw)
save("provider_failure_import_manifest.json", {"schema": "researchos.root.sealed-failure-origin-import.v1", "files": [{"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)} for name,raw in sorted(public.items())], "source_edits": 0, "paid_calls": 0, "private_db_reads": 0, "formal_increment": 0})
provider_failure_ref = ref(provider_path, "4ba98ed94fe1438f952a0bc792808f989a45a01a90203405578dbbb46dfdcd23")
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
old = copy.deepcopy(cp["failure_counters"])
new_entries = []
for item in failures["new_independent_origins"]:
    original = item["unique_original_invocation"]
    for key in ["unique_original_invocation", "stdout", "stderr"]:
        ref(item[key]["path"], item[key]["sha256"])
    invocation = json.loads((ROOT / original["path"]).read_bytes())
    assert invocation["exit"] == item["actual_exit"]
    new_entries.append({"origin_key": "W05-99/w05-review/l02/" + original["sha256"], "attempts": 1, "retries_used": 0, "status": item["classification"], "evidence_ref": failure_ref, "detail": item, "counter_reset": False, "formal_increment": 0})
history_count = 0
for item in provider_failures["entries"]:
    original = item["invocation"]
    if item["group"] == "PROVIDER_HISTORY_REFUSAL":
        history_count += 1
    new_entries.append({"origin_key": "W05-99/provider9/" + original["sha256"], "attempts": 1, "retries_used": 0, "status": "EXECUTOR_REPORTED_ACTUAL_FAILURE_NOT_ACCEPTED", "failure_group": item["group"], "same_history_attempt": history_count if item["group"] == "PROVIDER_HISTORY_REFUSAL" else None, "evidence_ref": provider_failure_ref, "detail": item, "counter_reset": False, "formal_increment": 0})
assert history_count == 5 and len(new_entries) == 12
root_failed_ref = ref(BASE + "integration_codex/cli-source-adoption-r272/register.invocation.json")
root_failed = json.loads((ROOT / root_failed_ref["path"]).read_bytes())
assert root_failed["actual_exit"] == 1
new_entries.append({"origin_key": "W05-99/root/r272-adoption-invocation-field-mismatch", "attempts": 1, "retries_used": 0, "status": "ACTUAL_PRE_CAS_METADATA_KEYERROR_PRESERVED", "evidence_ref": root_failed_ref, "detail": "Original independent invocation field is exit, not actual_exit. First Root script stopped before canonical CAS; original stdout/stderr/invocation retained. Corrected exact field in separately saved v2 script; no original overwritten.", "counter_reset": False, "formal_increment": 0})
for item in new_entries:
    assert item["origin_key"] not in {entry.get("origin_key") for entry in cp["failure_counters"]}
    cp["failure_counters"].append(item)
assert len(cp["failure_counters"]) == 219 and cp["failure_counters"][:206] == old
subs = ow["card_path_bindings"]["W05-99"]["subtasks"]
subs["cli_read_interruption"].update(state="SOURCE_READY_EXACT4_CURRENT_COMPOSITION_INDEPENDENTLY_VERIFIED_MAIN_INTEGRATION_PENDING", independent_source_review_ref=review_ref, independent_failure_origins_ref=failure_ref, independent_closed_inputs=39065)
subs["provider_transport_reasoning_binding"].update(iteration_chain_state="CUMULATIVE_HISTORY_FAILURES5_LIMIT_EXCEEDED_ORIGINAL_AUTHOR_RETRIES_STOPPED_NOT_ACCEPTED", failure_origins_ref=provider_failure_ref, cumulative_history_failure_attempts=5, first_history_failure_limit_stage="candidate-3", author_held_tests=provider_failures["history_chain"]["held_tests"])
cp.setdefault("preserved_unindexed_tool_diagnostics", []).append({"at": now, "source_ref": failure_ref, "observations": failures["conversation_only_tool_diagnostics"], "reason": "No original invocation raw captured; preserve conversation observations without fabricating raw/exit or recounting ambiguous origins."})
cp["preserved_unindexed_tool_diagnostics"].append({"at": now, "source_ref": provider_failure_ref, "observations": provider_failures["other_tooling_errors"], "reason": "Original nine captured failure invocations imported separately; tooling-only conversation diagnostics retained, not fabricated as original raw."})
cp.setdefault("failure_chains", {})["W05-99/provider9-original-history-refusal"] = {"evidence_ref": provider_failure_ref, "actual_failed_invocations": 5, "first_reaches_two": provider_failures["history_chain"]["first_reaches_two"], "status": "LIMIT_EXCEEDED_PRESERVED_AUTHOR_RETRIES_STOPPED_NOT_ACCEPTED", "history": provider_failures["history_chain"], "counter_reset": False}
cp.update(revision=272, expected_previous_revision=271, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=100, amended_at=now, amended_by="codex:/root")
cp["next_command"] = "Archive current public evidence/canonical272, exact cherry-pick reviewedL02f5655994src174receipt on Main then current complete CLI closure with lock/git actual inputs. Provider9 author history chain5failures stopped; distinct negative controls/regressions and nonself assessment only. Schema23 exact10+immutable5 all12gates isolated, MAIN23hold. Root alone CAS; revalidateW04/W07 final source;22/42CURRENT required."
cp["note"] = "L02 independent exact4source READY234/67top fullPASS0fail0skip plus originaloversize1PASS; current39065inputs allstable incl formerly omitted lock/git inputs; Root can archive then integrate exactsource. Initial independent2Go-listfail+232PASS2skip refusal preserved; author old3origins not recounted. Provider9 actual9capturedfailedinvocations imported, samehistory5 cumulatives and candidate3first2/4..6boundaryexceeded retained, further original-author retries stopped, laterPASS candidate unaccepted/earlyDBsnapshots absent.206prefix+12neworiginals+1RootpreCASerror=219. Other11old deletions retained; schema23/publichandler/F08/LIVE/formal gates not accepted."
cp["work_in_progress"].update(status="L02_CURRENT_SOURCE_INDEPENDENT_READY_INTEGRATION_PENDING_PROVIDER9_LIMIT219_PRESERVED_SCHEMA23_EXACT10_ISOLATED", next_action=cp["next_command"], cli_read_independent_source_review_ref=review_ref, cli_read_independent_failure_origins_ref=failure_ref, provider_binding_failure_origins_ref=provider_failure_ref)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "L02_INDEPENDENT_CURRENT_SOURCE_ACCEPTED_AND_PROVIDER_CUMULATIVE_FAILURE_BOUNDARY_PRESERVED", "review_ref": review_ref, "provider_failure_ref": provider_failure_ref, "failure_origins": [206,219], "formal_increment": 0})
for item in [review_ref, failure_ref, provider_failure_ref, ref((OUT / "provider_failure_import_manifest.json").relative_to(ROOT).as_posix())]:
    if item["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(item["path"])
save("record.json", {"schema": "researchos.root.resume-checkpoint.v1", "actor": "codex:/root", "at": now, "checkpoint": [271,272], "ownership": [99,100], "failure_origins": [206,219], "review_ref": review_ref, "provider_failure_ref": provider_failure_ref, "state_registry_unchanged": True, "formal_cases_current": 0, "formal_increment": 0})
assert all(path.read_bytes() == raw for path,raw in before.items())
for path, value in [(CP,cp),(OW,ow)]:
    temporary = path.with_name(path.name + ".root272.tmp")
    with temporary.open("xb") as stream:
        stream.write(enc(value))
    assert path.read_bytes() == before[path]
    os.replace(temporary,path)
assert ST.read_bytes() == before[ST] and CM.read_bytes() == before[CM]
print(json.dumps({"checkpoint":272,"ownership":100,"failure_origins":219,"review_ref":review_ref,"record_ref":ref((OUT/"record.json").relative_to(ROOT).as_posix()),"formal_increment":0}))
