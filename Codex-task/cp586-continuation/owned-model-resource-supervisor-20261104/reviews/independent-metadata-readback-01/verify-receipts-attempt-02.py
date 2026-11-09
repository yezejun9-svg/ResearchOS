"""Receipt-only verification. No process construction, network, profiles or weights."""
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import sys

BASE = Path(r"C:\Users\yqyyds\Documents\Codex\2026-11-04\task\cp586-continuation")
SUP = BASE / "owned-model-resource-supervisor-20261104"
V2 = SUP / "revision-02"
R4 = BASE / "owned-model-resource-stage-b" / "revision-04"
STAGEB = R4.parent
STAGEA = BASE / "owned-model-resource"
ATTEMPT = SUP / "attempt-01"
RUN = R4 / "run-01"
OUT = SUP / "reviews" / "independent-metadata-readback-01"
REPO = Path("D:/") / "\u4f5c\u54c1\u96c6" / "ResearchOS" / "research-os"
SCOPE = REPO / "execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/resource-metadata-supervised-once"
PROJECT = "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
AUTH_SHA = "49be9bed3cb9868b1e7347450f7bf085a3a5f8339aaa78ff7e73b803640d6334"
CP_SHA = "744f7be96d8c65bd20d5f7f86390d28d3557c82bf9935149d761aed60256cea0"
MAN_SHA = "8f7603011921d814e0cd3dd5c2c7d61c2ceea5a17b92b202901a461a130d96b4"
SCOPE_SHA = "061e15e40bdf24ddf88047756ca05fa933c8ee8199e9d8ed3247d025c35a7b01"
CONTROLLER_SHA = "332334cef1028a8c56f0127d4438e8cf1852ff08bc16544ea0d6e726994f3297"
R4_SCOPE_SHA = "49a78cf270e40f4e76131bd9a1cd98e929548f39d36e9e1d203507f6ab67bdab"
REVIEW_SHA = "a1e562a307fdf7a7b0532df9773adab8c3dc8be3736b233c55f202aac00dee78"
STAGEA_SHA = "1ee48d848976e0d1aff869c474516cc6ce90bdc7373fd2735b27b6dc6b61fd24"
MODEL_SHA = "0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0"
file_hashes = {}
checks = []
blocked_operations = []
def audit(event, args):
    if event.startswith(("subprocess.Popen", "_winapi.CreateProcess", "os.system", "os.spawn",
                         "os.exec", "socket.connect", "socket.bind", "socket.getaddrinfo")):
        blocked_operations.append(event)
        raise AssertionError("forbidden process/network event")
sys.addaudithook(audit)

def raw(path, limit=16 * 1024 * 1024):
    path = Path(path)
    if any(part.lower() in ("profile", "controller-profile", ".ssh", ".ollama") for part in path.parts):
        raise AssertionError("profile/private path forbidden")
    value = path.read_bytes()
    if len(value) > limit:
        raise AssertionError("receipt/source file exceeds declared bound")
    file_hashes[str(path)] = {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
    return value

def pairs(entries):
    value = {}
    for k, v in entries:
        if k in value: raise ValueError("duplicate JSON key")
        value[k] = v
    return value

def record(path, limit=256 * 1024):
    return json.loads(raw(path, limit), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))

def check(name, value):
    checks.append({"name": name, "ok": bool(value)})

def digest(path):
    return hashlib.sha256(raw(path)).hexdigest()

def same_path(left, right):
    return PureWindowsPath(str(left)) == PureWindowsPath(str(right))

def int_is(value, wanted):
    return type(value) is int and value == wanted

def pins(directory, manifest="MANIFEST.json", files_key="files", path_key="relative"):
    data = record(directory / manifest, 4 * 1024 * 1024)
    entries = data[files_key]
    checked = 0
    matched = 0
    for item in entries:
        path = (directory / item[path_key]).resolve()
        if not path.is_relative_to(directory.resolve()): raise AssertionError("pin path escape")
        content = raw(path)
        checked += 1
        matched += (len(content) == item["bytes"] and hashlib.sha256(content).hexdigest() == item["sha256"])
    check("all_pins_" + str(directory.name) + "_" + manifest, checked == matched)
    return {"checked": checked, "matched": matched}

auth = record(SCOPE / "root-authorization.json", 64 * 1024)
command = record(SCOPE / "RUN_COMMAND.json", 64 * 1024)
journal = record(SCOPE / "preparation-journal.json", 64 * 1024)
resume = record(SCOPE / "RESUME.json", 64 * 1024)
checkpoint = record(OUT / "checkpoint.observed.json", 32 * 1024 * 1024)
consumed = record(ATTEMPT / "CONSUMED.json")
supervised = record(ATTEMPT / "SUPERVISOR-RESULT.json")
result = record(RUN / "RESULT.json")
version = record(RUN / "version.response.json", 65536)
tags = record(RUN / "tags.response.json", 65536)
startup = record(RUN / "SUSPENDED-OWNED-IDENTITY.json", 65536)
env_keys = record(RUN / "ENV-KEYS.json", 65536)

check("root_authorization_exact_hash", digest(SCOPE / "root-authorization.json") == AUTH_SHA)
check("checkpoint594_snapshot_exact_bytes", digest(OUT / "checkpoint.observed.json") == CP_SHA)
check("checkpoint594_revision_project", int_is(checkpoint["revision"], 594) and checkpoint["project_id"] == PROJECT)
check("authorization_actor_status_project", auth["actor"] == "codex:/root" and auth["status"] == "ROOT_AUTHORIZED_ONCE_AFTER_REVIEW" and auth["project_id"] == PROJECT)
binding = {"root_scope_sha256": AUTH_SHA, "checkpoint_revision": 594, "checkpoint_sha256": CP_SHA,
           "supervisor_manifest_sha256": MAN_SHA, "supervisor_scope_sha256": SCOPE_SHA,
           "controller_sha256": CONTROLLER_SHA, "controller_scope_sha256": R4_SCOPE_SHA}
for name, value in binding.items():
    check("consumed_binding_" + name, consumed.get(name) == value and (type(consumed.get(name)) is int if name == "checkpoint_revision" else True))
    check("supervisor_binding_" + name, supervised.get(name) == value and (type(supervised.get(name)) is int if name == "checkpoint_revision" else True))
for name, value in binding.items():
    if name != "root_scope_sha256":
        check("authorization_binding_" + name, auth.get(name) == value)
check("authorization_review_and_limits", auth["independent_supervisor_review_sha256"] == REVIEW_SHA
      and int_is(auth["max_controller_launches"], 1) and int_is(auth["inference_limit"], 0)
      and auth["endpoint"] == "http://127.0.0.1:43861" and same_path(auth["attempt_directory"], ATTEMPT))
check("preparation_journal_binding", journal["checkpoint_revision"] == 594 and journal["checkpoint_sha256"] == CP_SHA and journal["root_authorization_sha256"] == AUTH_SHA and int_is(journal["formal_increment"], 0))
check("resume_no_formal_or_resource_acceptance", int_is(resume["formal_accepted"], 0) and int_is(resume["formal_required"], 42) and int_is(resume["formal_increment"], 0) and resume["resource_ready"] is False and resume["counter_reset"] is False)
# RESUME is an evolving settlement summary, never the authorization snapshot.
# The prelaunch value13401272320 was observed in b70d42 with original RESUME
# SHA875b927f... in b0086e; no current free-space claim is made after consumption.
expected_args = ["-I", "-S", str(V2 / "supervise.py"), "--execute", "--expected-manifest-sha256",
                 MAN_SHA, "--root-scope", str(SCOPE / "root-authorization.json"),
                 "--root-scope-sha256", AUTH_SHA]
check("planned_command_exact_entry_args", same_path(command["exe"], r"C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe")
      and command["args"] == expected_args and same_path(command["cwd"], V2)
      and int_is(command["max_launches"], 1) and command["automatic_retry"] is False)
check("global_consumption_marker", consumed["status"] == "CONSUMED_LAUNCH_OUTCOME_NOT_YET_KNOWN"
      and int_is(consumed["outer_wait_seconds"], 180) and int_is(consumed["kill_confirmation_seconds"], 5)
      and consumed["automatic_retry"] is False)
check("supervisor_known_normal_exit_no_kill", supervised["status"] == "REPORTED_PROOF_COMPLETE_ROOT_REVIEW_REQUIRED"
      and int_is(supervised["controller_exit_code"], 0) and supervised["termination_confirmed"] is True
      and supervised["kill_attempted"] is False and supervised["automatic_retry"] is False)
check("supervisor_not_acceptance", supervised["resource_ready"] is False and supervised["independent_acceptance"] is False
      and supervised["reported_proof_complete"] is True and int_is(supervised["formal_increment"], 0)
      and supervised["counter_reset"] is False)
check("controller_metadata_status", result["status"] == "METADATA_VERIFIED_OWNED_JOB_CLOSED_ASSETS_UNCHANGED")
check("controller_cleanup_stream_asset_gates", all(result[k] is True for k in ("cleanup_proved", "streams_drained", "stage_a_assets_unchanged_after_stop")))
check("controller_zero_forbidden_counts", all(int_is(result[k], 0) for k in ("controller_inference_requests", "paid_provider_requests", "old_root_writes", "formal_increment")))
check("controller_not_ready_no_reset_no_error", result["resource_ready"] is False and result["counter_reset"] is False and not result.get("error"))
attempts = result["metadata_get_attempts"]
check("exact_once_version_tags", attempts == {"/api/version": 1, "/api/tags": 1} and all(type(v) is int for v in attempts.values()))
kernel = result["kernel"]; state = kernel["State"]; close = kernel["Close"]; primary = kernel["Primary"]
processes = state["Processes"]
check("kernel_final_accounting", int_is(state["Total"], 20) and int_is(state["Active"], 0)
      and state["Complete"] is True and state["PrimarySignaled"] is True and len(processes) == state["Total"])
check("kernel_close_and_errors", close["JobClosed"] is True and close["PrimarySignaled"] is True
      and close.get("Errors") in (None, []) and state.get("Errors") in (None, [])
      and kernel["CleanupProved"] is True and kernel["Error"] == "")
check("final_process_identities_unique", len({p["pid"] for p in processes}) == 20 and all(type(p["pid"]) is int and p["pid"] > 0 for p in processes))
check("all20_final_held_job_event_signaled", all(p[k] is True for p in processes for k in ("handle_held", "in_owned_job", "new_process_event", "signaled_after_cleanup")))
check("all20_exact_filetime_records", all(isinstance(p["creation_filetime_decimal"], str)
      and p["creation_filetime_decimal"].isascii() and p["creation_filetime_decimal"].isdecimal()
      and int(p["creation_filetime_decimal"]) > 0 for p in processes))
check("startup_primary_same_snapshot", startup == primary)
final_primary = [p for p in processes if p["pid"] == primary["pid"]]
check("startup_primary_matches_final_identity", len(final_primary) == 1
      and final_primary[0]["creation_filetime_decimal"] == primary["creation_filetime_decimal"]
      and same_path(final_primary[0]["image"], primary["image"])
      and same_path(primary["image"], STAGEA / "runtime/ollama.exe")
      and primary["handle_held"] is True and primary["in_owned_job"] is True)
check("startup_flags_are_snapshot_final_flags_true", primary["new_process_event"] is False
      and primary["signaled_after_cleanup"] is False and final_primary[0]["new_process_event"] is True
      and final_primary[0]["signaled_after_cleanup"] is True)
check("version_exact_metadata", version == {"version": "0.30.0-rc31"})
models = tags["models"]
check("tags_exact_model_metadata", len(models) == 1 and models[0]["name"] == "qwen3:4b-instruct"
      and models[0]["model"] == "qwen3:4b-instruct" and models[0]["digest"] == MODEL_SHA
      and int_is(models[0]["size"], 2497293803))
check("controller_environment_key_whitelist", set(env_keys) == {"APPDATA","LOCALAPPDATA","OLLAMA_DEBUG","OLLAMA_HOST","OLLAMA_MODELS",
      "OLLAMA_NOHISTORY","OLLAMA_NOPRUNE","OLLAMA_NO_CLOUD","PATH","SystemRoot","TEMP","TMP","USERPROFILE","WINDIR"})
check("supervisor_environment_key_whitelist", set(consumed["environment_keys_only"]) == {"APPDATA","LOCALAPPDATA","PATH","SystemRoot","TEMP","TMP","USERPROFILE","WINDIR"})
stdout = raw(RUN / "stdout.raw", 2*1024*1024).decode("utf-8", errors="strict")
stderr = raw(RUN / "stderr.raw", 2*1024*1024).decode("utf-8", errors="strict")
requests = re.findall(r'\|\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+"([^"]+)"', stdout)
check("captured_http_logs_only_two_metadata_gets", sorted(requests) == [("GET", "/api/tags"), ("GET", "/api/version")])
check("required_startup_markers", "Ollama cloud disabled: true" in stderr
      and "vram-based default context" in stderr and "Listening on 127.0.0.1:43861" in stderr)
finished = dt.datetime.fromisoformat(result["finished_at"].replace("Z", "+00:00"))
deadline = dt.datetime.fromisoformat(kernel["CleanupDeadline"])
check("reported_finished_before_cleanup_deadline", finished <= deadline)

pin_sets = {"supervisor_v2": pins(V2), "supervisor_v1": pins(SUP),
            "r4_prepared": pins(R4, "PREPARED-MANIFEST.json"),
            "r4_source": pins(R4, "SOURCE-MANIFEST.json"),
            "old76": pins(STAGEB, "PREPARED-MANIFEST.json")}
check("supervisor_v2_exact_manifest", digest(V2 / "MANIFEST.json") == MAN_SHA)
check("supervisor_scope_and_review_exact", digest(V2 / "SCOPE.json") == SCOPE_SHA
      and digest(V2 / "reviews/independent-supervisor-review-02/source-review.json") == REVIEW_SHA)
check("controller_and_scope_exact_after_run", digest(R4 / "controller.exe") == CONTROLLER_SHA and digest(R4 / "SCOPE.json") == R4_SCOPE_SHA)
stagea = record(STAGEA / "MANIFEST.json", 4*1024*1024)
check("stageA_manifest_pin_and981_roster_only", digest(STAGEA / "MANIFEST.json") == STAGEA_SHA
      and int_is(stagea["verified_asset_file_count"], 981) and len(stagea["assets"]) == 981)
evidence = record(SCOPE / "evidence-manifest.json", 1024*1024)
matched = 0
for item in evidence:
    path = (SCOPE / "evidence" / item["path"]).resolve()
    if not path.is_relative_to((SCOPE / "evidence").resolve()): raise AssertionError("D evidence path escape")
    content = raw(path)
    matched += (len(content) == item["bytes"] and hashlib.sha256(content).hexdigest() == item["sha256"])
check("D_copied_evidence_manifest_all_pins", matched == len(evidence))

check("D_permanent_cp594_matches_C_snapshot", digest(SCOPE / "checkpoint.cp594.before-settlement.json") == CP_SHA)
actual_archive = record(SCOPE / "actual-evidence-manifest.json", 1024 * 1024)
actual_sources = {
 "actual-evidence/supervisor/CONSUMED.json": ATTEMPT / "CONSUMED.json",
 "actual-evidence/supervisor/SUPERVISOR-RESULT.json": ATTEMPT / "SUPERVISOR-RESULT.json",
 **{"actual-evidence/controller/" + name: RUN / name for name in
    ("RESULT.json", "ENV-KEYS.json", "SUSPENDED-OWNED-IDENTITY.json",
     "version.response.json", "tags.response.json", "stdout.raw", "stderr.raw")}
}
check("actual_archive_exact_public9_names", {item["path"].replace("\\", "/") for item in actual_archive} == set(actual_sources))
actual_matched = 0
for item in actual_archive:
    key = item["path"].replace("\\", "/")
    if key not in actual_sources: raise AssertionError("unapproved archive path")
    content = raw(SCOPE / item["path"])
    source_content = raw(actual_sources[key])
    actual_matched += (len(content) == item["bytes"] and hashlib.sha256(content).hexdigest() == item["sha256"] and content == source_content)
check("actual_archive9_exact_bytes_match_C", actual_matched == len(actual_archive) == 9)

consistent = all(item["ok"] for item in checks)
summary = {
 "schema":"researchos.metadata-only-independent-receipt-checks.v1",
 "at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
 "metadata_only_readback_verified":consistent,
 "checks_count":len(checks),"checks":checks,
 "failing_checks":[item["name"] for item in checks if not item["ok"]],
 "authorization_cp":594,"authorization_cp_sha256":CP_SHA,
 "root_reported_tool_terminal":{"start_chunk":"d1e4ff","session":22187,"terminal_chunk":"5ab52c","actual_exit":0},
 "supervisor":{"status":supervised["status"],"controller_exit_code":supervised["controller_exit_code"],
               "termination_confirmed":supervised["termination_confirmed"],"kill_attempted":supervised["kill_attempted"]},
 "controller":{"status":result["status"],"finished_at":result["finished_at"],"cleanup_deadline":kernel["CleanupDeadline"],
               "metadata_get_attempts":attempts,"resource_ready":False,"formal_increment":0},
 "kernel":{"total":state["Total"],"active":state["Active"],"complete":state["Complete"],
           "held_job_event_signaled_records":len(processes),"exit_codes":dict(collections.Counter(str(p["exit_code"]) for p in processes)),
           "image_basenames":dict(collections.Counter(PureWindowsPath(p["image"]).name for p in processes)),
           "startup_primary":primary,"final_primary":final_primary[0],"job_closed":close["JobClosed"]},
 "model_metadata":{"version":version["version"],"name":models[0]["name"],"digest":models[0]["digest"],"bytes":models[0]["size"]},
 "captured_metadata_requests":requests,"pin_sets":pin_sets,"D_copied_evidence_pins":{"checked":len(evidence),"matched":matched},
 "D_actual_evidence_pins":{"checked":len(actual_archive),"matched":actual_matched},
 "mutable_resume_boundary":"Root RESUME now describes settlement CP595; original run authorization uses only frozen CP594 C/D snapshots, not current checkpoint or mutable RESUME.",
 "prelaunch_space_observation":{"bytes":13401272320,"observation_chunk":"b70d42","original_RESUME_hash_chunk":"b0086e","not_current_free_space_claim":True},
 "asset_check_boundary":"Pinned controller reports pre/post981 assets unchanged; independent reviewer hashes only StageA manifest, never weights or asset traversal.",
 "direct_tcp_tuple_boundary":"Actual tuple gate is inferred from the pinned reviewed controller successful path; no independent runtime socket-table query was made.",
 "profile_or_private_key_reads":0,"profile_traversals":0,"asset_weight_rehashes":0,
 "review_operations":{"real_Popen_calls":0,"controller_runs":0,"native_backend_runs":0,"HTTP":0,"D_writes":0,"Main_CP_writes":0,
                      "blocked_process_or_network_events":blocked_operations,"counter_reset":False},
 "resource_ready":False,"formal_pass_issued":False,"business_acceptance":False,"model_inference_qualification":False,
 "formal_progress":"0/42","automatic_retry_allowed":False,
 "file_hashes":file_hashes
}
with (OUT / "data-verification.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(summary, stream, ensure_ascii=True, indent=2)
    stream.write("\n")
print(json.dumps({k:summary[k] for k in ("metadata_only_readback_verified","checks_count","failing_checks","kernel","pin_sets",
        "D_copied_evidence_pins","review_operations","resource_ready","formal_pass_issued","formal_progress")}, ensure_ascii=True, indent=2))
raise SystemExit(0 if consistent and not blocked_operations else 1)



