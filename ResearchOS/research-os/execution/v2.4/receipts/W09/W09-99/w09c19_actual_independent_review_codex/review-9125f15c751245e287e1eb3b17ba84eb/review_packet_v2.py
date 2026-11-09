"""Independent read-only C19 packet audit; never imports or calls a consumer."""
from pathlib import Path
import hashlib
import json
import re
import stat

O = Path(__file__).resolve().parent
checks = []
pins = {}


def check(name, ok, detail=None):
    row = {"check": name, "pass": bool(ok)}
    if detail is not None:
        row["detail"] = detail
    checks.append(row)
    if not ok:
        (O / "checks.failed.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
        raise AssertionError(name)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_ref(ref):
    p = Path(ref["path"])
    raw = p.read_bytes()
    check("PIN:" + str(p), sha(raw) == ref["sha256"].removeprefix("sha256:") and len(raw) == ref["bytes"])
    pins[str(p)] = {"path": str(p), "sha256": sha(raw), "bytes": len(raw)}
    return raw


def local(name):
    return json.loads((O / name).read_bytes())


report = local("native-report.input.json")
tool = local("native-tool-run.input.json")
packet = local("native-packet.public-index.json.input.json")
validation = local("validation.closed.json.input.json")
contract = local("consumer-contract.input.json")
inventory = local("compiler-inventory.input.json")
inputs = local("producer-inputs.read.json")
closings = local("closure-and-root-io.read.json")
T = Path(packet["consumer_source_root"])
run = report["run_id"]
selected = ["TestW09C19ChainInvalidation", "TestW09C19ExplicitOriginAndUnknown"]
ids = [f"C19-{i:02d}" for i in range(1, 6)]
producer = next(x["document"] for x in inputs if x["key"] == "invocation-1")
tmp = Path(producer["public_environment"]["TEMP"])

# Actual bytes, not report-level Boolean claims.
check("same_run", run == packet["run_id"] == tool["run_id"] == "9125f15c751245e287e1eb3b17ba84eb")
check("report_original", read_ref(packet["original_report_ref"]) == (O / "native-report.input.json").read_bytes())
check("tool_original", read_ref(packet["original_tool_run_ref"]) == (O / "native-tool-run.input.json").read_bytes())
check("component_scope", report["status"] == "PASS" and report["scope"] == "FIXTURE_IMPLEMENTED_SERVICE" and report["task_id"] == "W09" and report["check_id"] is None and report["case_id"] == "C19" and report["formal_case_accepted_delta"] == 0 and report["formal_construction_acceptance"] == "NOT_RUN_POSTRUN_REVIEW_PENDING")
check("actual_process_result", report["exit_code"] == tool["native_exit_code"] == 0 and report["timed_out"] is False)
check("selection_and_ids", report["selected_tests"] == selected and sorted(report["passed_tests"]) == selected and sorted(report["assertion_ids"]) == ids and report["assertions"] == 5 and report["missing_assertion_ids"] == [])
original_paths = set()
archive_paths = set()
for pair in packet["raw_copy_mapping"]:
    a, b = pair["original_ref"], pair["archive_ref"]
    check("unique_copy:" + a["path"], a["path"] not in original_paths and b["path"] not in archive_paths)
    original_paths.add(a["path"])
    archive_paths.add(b["path"])
    check("raw_copy:" + a["path"], read_ref(a) == read_ref(b))
run_dir = Path(packet["original_report_ref"]["path"]).parent
check("complete_original_packet", {str(p) for p in run_dir.rglob("*") if p.is_file()} == original_paths)
check("packet_count", len(original_paths) == 490)
stdout_path = T / tool["stdout_ref"]
stderr_path = T / tool["stderr_ref"]
stdout = stdout_path.read_bytes()
stderr = stderr_path.read_bytes()
check("tool_stdout_stderr", sha(stdout) == tool["stdout_sha256"] and sha(stderr) == tool["stderr_sha256"] and len(stderr) == 0)
check("tool_report_link", tool["report_ref"] == Path(packet["original_report_ref"]["path"]).relative_to(T).as_posix() and tool["report_sha256"] == packet["original_report_ref"]["sha256"] and tool["actual_invocation"] == report["actual_invocation"] and report["raw_evidence_references"] == [tool["stdout_ref"], tool["stderr_ref"]])
events = [json.loads(line) for line in stdout.decode("utf-8").splitlines()]
check("go_event_actions", bool(events) and all(x.get("Action") in {"start", "run", "pause", "cont", "pass", "fail", "skip", "output", "bench"} for x in events))
check("go_terminal_tests", sorted(x["Test"] for x in events if x.get("Action") == "pass" and x.get("Test")) == selected and not any(x.get("Action") in {"fail", "skip"} for x in events))
replayed = []
output_buffers = {}
for event in events:
    key = (event.get("Package"), event.get("Test"))
    output_buffers[key] = output_buffers.get(key, "") + event.get("Output", "")
    while "\n" in output_buffers[key]:
        line, output_buffers[key] = output_buffers[key].split("\n", 1)
        if line.startswith("W09_ASSERTION "):
            a = json.loads(line.removeprefix("W09_ASSERTION "))
            check("stdout_owner:" + a["assertion_id"], key[1] == a.get("test_name") and a["test_name"] in selected)
            a["raw_evidence_reference"] = tool["stdout_ref"]
            replayed.append(a)
check("stdout_streams_complete", all(not v for v in output_buffers.values()))
check("stdout_assertions_exact", replayed == report["assertion_results"] and sorted(a["assertion_id"] for a in replayed) == ids and all(a["run_id"] == run and a["status"] == "PASS" for a in replayed))

# Source/version and actual compiler listing closure.
vm = report["version_manifest"]
check("source_roster_21", set(vm["source_sha256"]) == set(contract["source_roster"]) and len(vm["source_sha256"]) == 21)
for name, digest in vm["source_sha256"].items():
    raw = (T / name).read_bytes()
    check("live_source:" + name, "sha256:" + sha(raw) == digest)
    pins[str(T / name)] = {"path": str(T / name), "sha256": sha(raw), "bytes": len(raw)}
go = report["go_executable"]
read_ref(go)
locked_raw = (T / "execution/toolchains/locked.json").read_bytes()
locked = json.loads(locked_raw)
check("GoRef_lock", go == inventory["GoRef"] and Path(go["path"]).resolve() == Path(locked["tools"]["go"]["path"]).resolve() and go["sha256"] == locked["tools"]["go"]["sha256"] and vm["go_lock_sha256"] == "sha256:" + sha(locked_raw))
check("spec_manifest", vm["spec_manifest_sha256"] == "sha256:" + sha((T / "spec/v2.0/PACKAGE_MANIFEST.json").read_bytes()))
check("native_argv", report["actual_invocation"] == [go["path"], "test", "-count=1", "-json", "-run", "^(?:" + "|".join(selected) + ")$", "./internal/domain"])
overlay = next(x["document"] for x in inputs if x["key"] == "source-overlay")
for name, ref in overlay["sources"].items():
    check("overlay_original:" + name, read_ref(ref) == (T / name).read_bytes())
listing = next(x["document"] for x in inputs if x["key"] == "invocation-0")
raw_listing = read_ref(listing["stdout_ref"]).decode("utf-8")
decoder, pos, packages, compiled, embeds = json.JSONDecoder(), 0, [], set(), []
fields = ("GoFiles", "CgoFiles", "CFiles", "CXXFiles", "MFiles", "HFiles", "FFiles", "SFiles", "SwigFiles", "SwigCXXFiles", "SysoFiles", "CompiledGoFiles", "TestGoFiles", "XTestGoFiles", "EmbedFiles", "TestEmbedFiles", "XTestEmbedFiles")
while pos < len(raw_listing):
    while pos < len(raw_listing) and raw_listing[pos].isspace():
        pos += 1
    if pos == len(raw_listing):
        break
    pkg, pos = decoder.raw_decode(raw_listing, pos)
    check("package_errors:" + pkg.get("ImportPath", ""), not pkg.get("Error") and not pkg.get("DepsErrors"))
    packages.append(pkg.get("ImportPath"))
    if not pkg.get("Dir"):
        continue
    for field in fields:
        for name in pkg.get(field, []):
            path = Path(name)
            path = path if path.is_absolute() else Path(pkg["Dir"]) / path
            compiled.add(str(path))
            if field.endswith("EmbedFiles"):
                embeds.append((pkg["ImportPath"], field, str(path)))
check("compiler_packages_exact", packages == inventory["packages"] and len(packages) == inventory["package_count"] == 351)
check("compiler_selected_paths_exact", compiled == {x["path"] for x in inventory["build_inputs"]} and len(compiled) == 3702)
check("compiler_embed_exact", embeds == [(x["package"], x["field"], x["ref"]["path"]) for x in inventory["actual_embed_files"]] and len(embeds) == 34)
for ref in inventory["build_inputs"] + inventory["product_inventory"] + inventory["compiler_tool_refs"]:
    read_ref(ref)
check("selected_tests_compiler_inputs", {str(T / n) for n in ("internal/domain/domain_test.go", "internal/domain/retrieval_test.go", "internal/domain/w09_evidence_export_test.go")} <= compiled)

# All owned exports are parsed by original bytes. Opaque bodies remain opaque.
owned = run_dir / "owned"
members, event_rows = {}, {}
for claim in report["owned_export"]["members"]:
    path = T / claim["path"]
    data = read_ref({**claim, "path": str(path)})
    check("owned_path:" + path.name, path.is_relative_to(owned) and path.parent.name in selected and re.fullmatch(r"[0-9]{8}-.+\.raw", path.name) is not None and not path.is_symlink() and path not in members)
    members[path] = (claim, data)
    label = path.name.split("-", 1)[1][:-4]
    if label.startswith(("http-request", "http-response", "file-body-")) or re.fullmatch(r"simulated-opinion-(?:0[0-9]|1[0-9])", label):
        continue
    value = json.loads(data)
    check("owned_event_lineage:" + path.name, value.get("_run_id") == run and value.get("_test_name") == path.parent.name)
    event_rows.setdefault((path.parent.name, label), []).append((path, value))
check("owned_manifest_complete", len(members) == 486 and set(members) == set(owned.rglob("*.raw")) and set(p.parent.name for p in members) == set(selected))


def one(test, label):
    rows = event_rows.get((test, label), [])
    check("unique_event:" + test + ":" + label, len(rows) == 1)
    return rows[0][1]


def body(ref, test):
    p = Path(ref["path"])
    check("owned_body_pin:" + p.name, p in members and p.parent.name == test and ref["sha256"] == members[p][0]["sha256"] and ref["bytes"] == members[p][0]["bytes"])
    return members[p][1]


for rec in replayed:
    aid, test = rec["assertion_id"], rec["test_name"]
    expected_owner = selected[0] if aid == "C19-05" else selected[1]
    raw = one(test, "assertion-" + aid)
    p, _ = event_rows[(test, "assertion-" + aid)][0]
    check("assertion_body:" + aid, test == expected_owner and raw["actual"] == rec["evidence"] and raw["assertion_id"] == aid and raw["status"] == "PASS" and all(raw["actual"].get(k) == v for k, v in raw["expected"].items()) and rec["owned_export_ref"] == {"path": str(p), "sha256": sha(members[p][1]), "bytes": len(members[p][1])})

test = selected[1]
before = one(test, "c19-complete-graph-before")
after = one(test, "c19-complete-graph-after")
origins = one(test, "origins-c19-before")["rows"]
check("c19_origins_immutable", origins == one(test, "origins-c19-after")["rows"] and len(origins) == 6 and len({x["evidence_id"] for x in origins}) == 6)
bindings = [v for _, v in event_rows[(test, "local-evidence-binding")]]
by_name = {v["relative_path"]: v for v in bindings}
check("c19_seven_bindings", len(bindings) == 7 and set(by_name) == {"original.txt", "experiment.txt", "unknown.txt", *(f"repost-{i}.txt" for i in range(4))})
first, experiment = by_name["original.txt"]["evidence_id"], by_name["experiment.txt"]["evidence_id"]
root_rows = [x for x in origins if x["relation"] == "ROOT"]
derived = [x for x in origins if x["relation"] == "DERIVED"]
check("c19_explicit_roots_derivations", {x["evidence_id"] for x in root_rows} == {first, experiment} and len(derived) == 4 and {x["evidence_id"] for x in derived} == {by_name[f"repost-{i}.txt"]["evidence_id"] for i in range(4)} and all(x["origin_id"] == first for x in derived) and all(not x.get("origin_id") for x in root_rows))
by_id = {v["evidence_id"]: v for v in bindings}
for origin in origins:
    b = by_id[origin["evidence_id"]]
    check("origin_basis:" + origin["evidence_id"], origin["basis_root_id"] == b["root_id"] == before["root_id"] and origin["basis_relative_path"] == b["relative_path"] and origin["basis_artifact_id"] == b["artifact_id"])
graph = {v["evidence_id"]: v for v in before["records"]}
later = {v["evidence_id"]: v for v in after["records"]}
check("c19_records_retained", len(before["records"]) == len(after["records"]) == len(graph) == 27 and set(graph) == set(later))
for name, b in by_name.items():
    row = graph[b["evidence_id"]]
    file = one(test, "file-c19-before-" + name)
    raw = body(file["body"], test)
    check("c19_observed_bytes:" + name, row["evidence_kind"] == "OBSERVED" and row["source_kind"] == b["source_kind"] and file["exists"] is True and file["root_id"] == b["root_id"] and Path(file["path"]).name == name and b["content_hash"] == "sha256:" + sha(raw))
    if name.startswith("repost-"):
        check("repost_explicit_origin:" + name, row["root_evidence_id"] == first and row["origin_evidence_id"] == first and row["origin_relation"] == "CONFIRMED")
    elif name == "unknown.txt":
        check("same_bytes_not_provenance", row["origin_relation"] == "UNKNOWN" and not row["root_evidence_id"] and b["artifact_id"] == by_name["original.txt"]["artifact_id"] and b["content_hash"] == by_name["original.txt"]["content_hash"])
    else:
        check("explicit_root:" + name, row["root_evidence_id"] == b["evidence_id"] and row["origin_relation"] == "CONFIRMED")
sims = [v for _, v in event_rows[(test, "simulated-opinion-binding")]]
check("20_simulations", len(sims) == 20 and {x["ordinal"] for x in sims} == set(range(20)))
http = [v for (owner, label), rows in event_rows.items() if label == "http-exchange" for _, v in rows]
check("fixture_http_only", bool(http) and all(x["delivery"] == "IN_PROCESS_HTTptest_RECORDER" and x["authorization_header_exported"] is False for x in http))
test_http = [v for _, v in event_rows[(test, "http-exchange")]]
for s in sims:
    raw = body(s["body"], test)
    row = graph[s["evidence_id"]]
    check("simulation_binding:" + str(s["ordinal"]), raw == f"simulated agent opinion {s['ordinal']}".encode() and s["content_hash"] == "sha256:" + sha(raw) and s["evidence_kind"] == row["evidence_kind"] == "SIMULATED" and s["source_kind"] == row["source_kind"] == "SIMULATION" and s["measurement_mode"] == "FIXTURE")
    content = [e for e in test_http if e["method"] == "POST" and e["path"].endswith("/content") and e["status"] == 201 and body(e["request"], test) == raw and json.loads(body(e["response"], test))["content_hash"] == s["content_hash"]]
    check("simulation_content:" + str(s["ordinal"]), len(content) == 1)
    uploaded = json.loads(body(content[0]["response"], test))
    artifacts, evidence = [], []
    for e in test_http:
        if e["method"] != "POST" or e["status"] != 201 or not e["path"].endswith(("/artifacts", "/evidence")):
            continue
        req, resp = json.loads(body(e["request"], test)), json.loads(body(e["response"], test))
        if e["path"].endswith("/artifacts") and req.get("content_hash") == s["content_hash"] and req.get("storage_key") == uploaded["storage_key"] and req.get("evidence_kind") == "SIMULATED" and req.get("measurement_mode") == "FIXTURE" and resp.get("id") == s["artifact_id"]:
            artifacts.append(e)
        if e["path"].endswith("/evidence") and req.get("snapshot_artifact_ref", {}).get("id") == s["artifact_id"] and req.get("evidence_kind") == "SIMULATED" and req.get("source_kind") == "SIMULATION" and resp.get("id") == s["evidence_id"]:
            evidence.append(e)
    check("simulation_business_calls:" + str(s["ordinal"]), len(artifacts) == len(evidence) == 1 and len({content[0]["request"]["path"], artifacts[0]["request"]["path"], evidence[0]["request"]["path"]}) == 3)
check("graph_input_set", {x["evidence_id"] for x in sims} | set(by_id) == set(graph))
check("c19_count_transition", before["counts"]["independent_observed_count"] == 2 and before["counts"]["simulated_count"] == 20 and before["counts"]["unknown_count"] == 1 and after["counts"]["independent_observed_count"] == 1 and after["counts"]["unknown_count"] == 6)
check("primary_change_and_rejection", b"withdrawn" in body(one(test, "file-c19-primary-changed")["body"], test) and bool(one(test, "c19-unsupported-relation-rejection")["actual_error"]))
chain_test = selected[0]
chain = one(chain_test, "chain-before-after")
chain_rows = one(chain_test, "origins-chain-before")["rows"]
edge = {v["evidence_id"]: v for v in chain_rows}
check("chain_immutable_lineage", chain_rows == one(chain_test, "origins-chain-after")["rows"] and len(chain_rows) == 3 and edge[chain["primary_id"]]["relation"] == "ROOT" and edge[chain["middle_id"]]["origin_id"] == chain["primary_id"] and edge[chain["leaf_id"]]["origin_id"] == chain["middle_id"])
check("chain_invalidation", chain["before"]["independent_observed_count"] == 1 and chain["after"]["independent_observed_count"] == 0 and chain["after"]["unknown_count"] == 1 and one(chain_test, "file-chain-middle-removed")["exists"] is False)
states = [v for (_, label), rows in event_rows.items() if label.startswith("state-") for _, v in rows]
check("actual_owned_temp_origin", bool(states) and all(Path(x["root_path"]).is_relative_to(tmp) for x in states if x.get("root_path")))

# Original process/guard evidence is audited, never recreated by this reviewer.
guards = [x for x in closings if "entries" in x["document"]]
check("six_guards", len(guards) == 6)
for x in guards:
    d = x["document"]
    read_ref(x["ref"])
    check("guard_closed:" + x["ref"]["path"], d["verification"] == "PASSED" and d["share_mode"] == "FILE_SHARE_READ_ONLY" and d["closed"] and d["retained_handles_count"] == 0 and not d["failure"] and not d["errors"] and all(e["verified"] and e["final_path_match"] and e["closed"] for e in d["entries"]))
compiler_guard = next(x["document"] for x in guards if Path(x["ref"]["path"]).name == "compiler-source-guard.cleanup.actual.json")
expected_compiler = {x["path"]: (x["sha256"], x["bytes"]) for x in inventory["build_inputs"] + inventory["product_inventory"] + inventory["compiler_tool_refs"] + [inventory["GoRef"], validation["compiler_inventory_ref"]]}
check("compiler_guard_exact", {x["path"]: (x["sha256"], x["bytes"]) for x in compiler_guard["entries"]} == expected_compiler)
isolation = next(x["document"] for x in closings if Path(x["ref"]["path"]).name == "isolation.ready.json")
jobs = [x["document"] for x in inputs if x["key"].startswith("invocation-")]
for r in isolation["invocation_refs"]:
    jobs.append(json.loads(read_ref(r)))
check("eight_owned_jobs", len(jobs) == 8)
for job in jobs:
    result = job["result"]
    cleanup = result["job_cleanup"]
    check("owned_job_closed:" + str(result["owned_child_pid"]), job["actual_native_exit"] == result["actual_exit"] == 0 and result["timed_out"] is False and result["error"] is None and job["exception"] is None and cleanup["active_processes_last_observed"] == 0 and not cleanup["errors"] and all(cleanup[k] for k in ("unnamed_exclusive_job", "kill_on_job_close_configured", "assigned_before_resume", "primary_exit_confirmed", "job_idle_confirmed", "handles_closed")))
    read_ref(job["stdout_ref"])
    read_ref(job["stderr_ref"])
root_io = next(x["document"] for x in closings if "postseal-root" in x["ref"]["path"])
check("root_wrapper_exit", root_io["producer"]["session_id"] == root_io["producer_poll1"]["session_id"] and root_io["producer_poll2"]["exit_code"] == 0 and root_io["explicit_final_python_exit"] == 0 and "ROOT_PYTHON_EXIT=0" in root_io["producer_poll2"]["output"] and root_io["prepare"]["exit_code"] == 0)
canonical = next(x["document"] for x in inputs if x["key"] == "canonical-pre")
for r in canonical["refs"]:
    read_ref(r)

summary = {"decision": "QUALIFIED", "scope": "COMPONENT_NATIVE_FIXTURE_ONLY", "run_id": run, "checks": len(checks), "failed_checks": 0, "source_roster": 21, "source_overlays": 6, "compiler_packages": 351, "compiler_inputs": 3702, "product_inventory": 572, "compiler_tools": 8, "embed_records": 34, "selected_tests": selected, "native_ids": ids, "owned_members": 486, "original_archive_pairs": 490, "jobs_closed": 8, "guard_groups_closed": 6, "guard_entries_closed": sum(len(x["document"]["entries"]) for x in guards), "fixture_temp_root": str(tmp), "http_exchanges": len(http), "external_model_provider_requests": 0, "reviewer_consumer_Git_Go_SQL_model_calls": 0, "formal_acceptance": False, "Main_adopted": False}
(O / "checks.json").write_text(json.dumps({"summary": summary, "checks": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
(O / "verified-input-pins.json").write_text(json.dumps(list(pins.values()), ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
