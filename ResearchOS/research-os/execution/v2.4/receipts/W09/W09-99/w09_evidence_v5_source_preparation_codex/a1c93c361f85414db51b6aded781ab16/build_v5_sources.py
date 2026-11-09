"""Static one-shot W09 source transform. Never imports candidate or runs Go."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True

here = Path(__file__).resolve().parent
old = here.parents[1] / "w09_evidence_revision_source_preparation_codex/fdbee1676fd64d8b9a93ce81076c6c4c"
pending = {}

def sub(text, old_text, new_text):
    if text.count(old_text) != 1:
        raise ValueError("non-unique source anchor: " + old_text[:70])
    return text.replace(old_text, new_text)

closure = (old / "w09_evidence_closure.py").read_text(encoding="utf-8")
closure = sub(closure, 'import re\nimport tempfile', 'import re\nimport stat\nfrom pathlib import PureWindowsPath\nimport tempfile')
closure = sub(closure, '''def file_pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": digest(raw), "bytes": len(raw)}
''', '''def file_pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": digest(raw), "bytes": len(raw)}


def safe_repo_rel(root, relative):
    """Validate canonical REL and every component before any byte read."""
    require(isinstance(relative, str) and relative and "\\\\" not in relative
            and not relative.startswith("/") and not PureWindowsPath(relative).drive
            and ":" not in relative and "//" not in relative
            and all(piece not in ("", ".", "..") for piece in relative.split("/")),
            "BAD_CANONICAL_REL")
    root = root.resolve(strict=True)
    path = root
    for piece in relative.split("/"):
        path = path / piece
        item = path.lstat()
        require(not path.is_symlink() and not getattr(path, "is_junction", lambda: False)()
                and not (getattr(item, "st_file_attributes", 0) &
                         getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)),
                "REF_ALIAS_OR_REPARSE")
    resolved = path.resolve(strict=True)
    require(root in resolved.parents and resolved.relative_to(root).as_posix() == relative,
            "FOREIGN_OR_ALIAS_REF")
    return resolved


def safe_repo_pin(root, claim):
    require(isinstance(claim, dict) and set(claim) == {"path", "sha256", "bytes"}
            and isinstance(claim.get("sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", claim["sha256"])
            and type(claim.get("bytes")) is int and claim["bytes"] >= 0,
            "TYPED_REF_REQUIRED")
    path = safe_repo_rel(root, claim["path"])
    require(path.is_file(), "REF_NOT_REGULAR_FILE")
    raw = path.read_bytes()
    require(digest(raw) == claim["sha256"] and len(raw) == claim["bytes"],
            "REF_BYTES_CHANGED")
    return path, raw
''')
closure = sub(closure, '''    opaque = ("http-request", "http-response", "file-body-", "simulated-opinion-", "g02-junction-stdout")
''', '''    opaque = ("http-request", "http-response", "file-body-", "g02-junction-stdout")
''')
closure = sub(closure, '''        if label.startswith(opaque):
            continue
''', '''        if label.startswith(opaque) or re.fullmatch(r"simulated-opinion-(?:0[0-9]|1[0-9])", label):
            continue
''')
closure = sub(closure, '''    simulations = [x["value"] for x in events.get("simulated-opinion-binding", []) if x["test"] == test]
    require(len(simulations) == 20 and {s.get("ordinal") for s in simulations} == set(range(20)),
            "C19_TWENTY_SIM_INPUTS_MISSING")
''', '''    raw_labels = [path.name.split("-", 1)[1][:-4] for path in members
                  if path.parent.name == test and
                  re.fullmatch(r"[0-9]{8}-simulated-opinion-(?:0[0-9]|1[0-9])\\.raw", path.name)]
    require(len(raw_labels) == 20 and set(raw_labels) ==
            {f"simulated-opinion-{i:02d}" for i in range(20)},
            "C19_RAW_OPINION_BODY_SET_MISMATCH")
    simulations = [x["value"] for x in events.get("simulated-opinion-binding", []) if x["test"] == test]
    require(len(simulations) == 20 and {s.get("ordinal") for s in simulations} == set(range(20)),
            "C19_TWENTY_SIM_INPUTS_MISSING")
''')
closure = sub(closure, '''        body = _raw_pin(s.get("body"), members, test)
        row = graph.get(s.get("evidence_id"))
''', '''        body = _raw_pin(s.get("body"), members, test)
        require(Path(s["body"]["path"]).name.endswith(
                f"-simulated-opinion-{s['ordinal']:02d}.raw"), "SIM_ORDINAL_BODY_SWAP")
        row = graph.get(s.get("evidence_id"))
''')
closure = sub(closure, '''    require({s["evidence_id"] for s in simulations} | set(bmap) == set(graph), "C19_INPUT_GRAPH_SET_MISMATCH")
''', '''    require({s["evidence_id"] for s in simulations} | set(bmap) == set(graph), "C19_INPUT_GRAPH_SET_MISMATCH")
    exchanges = [x["value"] for x in events.get("http-exchange", []) if x["test"] == test]
    def exact_exchange(method, suffix, request_pred, response_pred):
        matches = []
        for event in exchanges:
            if event.get("method") != method or not event.get("path", "").endswith(suffix)
                    or event.get("status") != 201:
                continue
            request = _raw_pin(event.get("request"), members, test)
            response = _raw_pin(event.get("response"), members, test)
            if request_pred(request) and response_pred(json.loads(response)):
                matches.append(event)
        require(len(matches) == 1, "C19_SIM_HTTP_CALL_NOT_UNIQUE_" + suffix)
        return matches[0]
    for s in simulations:
        body = _raw_pin(s["body"], members, test)
        content_call = exact_exchange("POST", "/content", lambda raw: raw == body,
            lambda reply: reply.get("content_hash") == s["content_hash"])
        upload = json.loads(_raw_pin(content_call["response"], members, test))
        artifact_call = exact_exchange("POST", "/artifacts",
            lambda raw: (lambda obj: obj.get("content_hash") == s["content_hash"]
                        and obj.get("storage_key") == upload.get("storage_key")
                        and obj.get("evidence_kind") == "SIMULATED"
                        and obj.get("measurement_mode") == "FIXTURE")(json.loads(raw)),
            lambda reply: reply.get("id") == s["artifact_id"]
                          and reply.get("content_hash") == s["content_hash"])
        evidence_call = exact_exchange("POST", "/evidence",
            lambda raw: (lambda obj: obj.get("snapshot_artifact_ref", {}).get("id") == s["artifact_id"]
                        and obj.get("evidence_kind") == "SIMULATED"
                        and obj.get("source_kind") == "SIMULATION")(json.loads(raw)),
            lambda reply: reply.get("id") == s["evidence_id"])
        require(len({content_call["request"]["path"], artifact_call["request"]["path"],
                     evidence_call["request"]["path"]}) == 3,
                "C19_SIM_HTTP_CALL_REUSE")
''')
closure = sub(closure, '''    original_hash = "sha256:" + digest(_raw_pin(files["initial-authorized"]["body"], members, test))
''', '''    initial_bundle = only(events, "a06-bundle-initial", test)
    stale_call = only(events, "a06-materialize-stale-rejected", test)
    new_bundle = only(events, "a06-bundle-after-delete", test)
    first_materialize = only(events, "a06-materialize-initial", test)
    after_materialize = only(events, "a06-materialize-after-delete", test)
    require(initial_bundle.get("root_id") == states[0]["root_id"]
            and initial_bundle.get("principal_id") == states[0]["principal"]
            and initial_bundle.get("task_id") == new_bundle.get("task_id")
            and initial_bundle.get("source_artifact_id") in initial_bundle.get("authorized_snapshot_ids", [])
            and initial_bundle.get("source_artifact_id") not in new_bundle.get("authorized_snapshot_ids", [])
            and new_bundle.get("deleted_artifact_id") not in new_bundle.get("authorized_snapshot_ids", [])
            and stale_call.get("task_id") == initial_bundle["task_id"]
            and stale_call.get("accepted") is False and stale_call.get("actual_error")
            and first_materialize.get("task_id") == after_materialize.get("task_id") == initial_bundle["task_id"]
            and first_materialize.get("accepted") is True
            and after_materialize.get("accepted") is True,
            "A06_CONTEXT_PERMISSION_CALL_GRAPH_MISSING")
    initial_manifest = _raw_pin(first_materialize.get("manifest"), members, test)
    later_manifest = _raw_pin(after_materialize.get("manifest"), members, test)
    require(initial_manifest and later_manifest and b"gamma deleted v3" not in later_manifest
            and first_materialize.get("target_path") != after_materialize.get("target_path")
            and stale_call.get("target_path") not in
                {first_materialize.get("target_path"), after_materialize.get("target_path")},
            "A06_MATERIALIZE_RAW_RESULT_MISSING")
    original_hash = "sha256:" + digest(_raw_pin(files["initial-authorized"]["body"], members, test))
''')
closure = sub(closure, '''    decision_path = (root / decision_ref).resolve(strict=True)
    require(root in decision_path.parents and digest(decision_path.read_bytes()) == decision_sha,
            "MODE_DECISION_PIN_DRIFT")
''', '''    decision_path = safe_repo_rel(root, decision_ref)
    require(digest(decision_path.read_bytes()) == decision_sha, "MODE_DECISION_PIN_DRIFT")
''')
closure = sub(closure, '''    reviewer_path = (root / reviewer_pin["path"]).resolve(strict=True)
    report_dir = (root / source["report_reference"]).resolve(strict=True).parent
    require(root in reviewer_path.parents and report_dir not in reviewer_path.parents,
            "REVIEWER_RECEIPT_OWNED_BY_PRODUCER")
    reviewer_raw = reviewer_path.read_bytes()
    require(digest(reviewer_raw) == reviewer_pin["sha256"] and len(reviewer_raw) == reviewer_pin["bytes"],
            "REVIEWER_RECEIPT_PIN_DRIFT")
''', '''    reviewer_path, reviewer_raw = safe_repo_pin(root, reviewer_pin)
    report_dir = safe_repo_rel(root, source["report_reference"]).parent
    require(report_dir not in reviewer_path.parents,
            "REVIEWER_RECEIPT_OWNED_BY_PRODUCER")
''')
closure = sub(closure, '''        for item, schema in ((host, "researchos.w09-host-witness.v1"),
                             (junction, "researchos.w09-junction-witness.v1")):
            raw = (root / item["path"]).read_bytes()
            require(item.get("sha256") == digest(raw) and item.get("bytes") == len(raw), "HOST_WITNESS_PIN")
            witness = json.loads(raw)
            require(witness.get("schema") == schema and witness.get("run_id") == native["run_id"]
                    and witness.get("report_sha256") == decision["report_sha256"]
                    and witness.get("go_executable") == native["go"]
                    and witness.get("source_sha256") == native["source_hashes"]
                    and witness.get("actual_platform") == "Windows 11 x64", "HOST_WITNESS_CURRENT_RUN")
''', '''        expected_witnesses = {json.dumps(host, sort_keys=True), json.dumps(junction, sort_keys=True)}
        require(len(expected_witnesses) == 2 and
                {json.dumps(item, sort_keys=True) for item in decision.get("witness_allowlist", [])}
                == expected_witnesses, "HOST_WITNESS_NOT_IN_FROZEN_RUN_ALLOWLIST")
        witness_values = {}
        for item, schema in ((host, "researchos.w09-host-witness.v1"),
                             (junction, "researchos.w09-junction-witness.v1")):
            _, raw = safe_repo_pin(root, item)
            witness = json.loads(raw)
            require(witness.get("schema") == schema and witness.get("run_id") == native["run_id"]
                    and witness.get("report_sha256") == decision["report_sha256"]
                    and witness.get("go_executable") == native["go"]
                    and witness.get("source_sha256") == native["source_hashes"]
                    and witness.get("actual_platform") == "Windows 11 x64", "HOST_WITNESS_CURRENT_RUN")
            witness_values[schema] = witness
''')
closure = sub(closure, '''                and junction_event.get("command", [])[:3] == ["cmd.exe", "/c", "mklink"]
                and junction_event.get("output") == junction.get("output_pin")
''', '''                and isinstance(junction_event.get("root_path"), str)
                and isinstance(junction_event.get("target_path"), str)
                and Path(junction_event["root_path"]).is_absolute()
                and Path(junction_event["target_path"]).is_absolute()
                and junction_event["root_path"] != junction_event["target_path"]
                and junction_event.get("command") == ["cmd.exe", "/c", "mklink", "/J",
                                                      junction_event["root_path"],
                                                      junction_event["target_path"]]
                and junction_event.get("command") ==
                    witness_values["researchos.w09-junction-witness.v1"].get("command")
                and junction_event.get("root_path") == decision.get("junction_root_path")
                and junction_event.get("target_path") == decision.get("junction_target_path")
                and junction_event.get("output") == junction.get("output_pin")
''')
pending["w09_evidence_closure.v5.proposed.py"] = closure

router = (old / "w09_formal_router.v4.proposed.py").read_text(encoding="utf-8")
router = sub(router, 'import platform\nfrom pathlib import Path',
             'import platform\nfrom pathlib import Path')
router = sub(router, 'from w09_evidence_closure import verify_native, verify_owned, verify_c19, verify_a06, verify_mode',
             'from w09_evidence_closure import verify_native, verify_owned, verify_c19, verify_a06, verify_mode, safe_repo_rel')
router = sub(router, '''    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("BAD_RELATIVE_REF")
    path = (ROOT / relative).resolve(strict=True)
    if path != ROOT and ROOT not in path.parents:
        raise ValueError("FOREIGN_REF")
    return path
''', '''    return safe_repo_rel(ROOT, relative)
''')
router = sub(router, '''        if label.startswith(("http-request", "http-response", "file-body-", "simulated-opinion-", "g02-junction-stdout")):
''', '''        if label.startswith(("http-request", "http-response", "file-body-", "g02-junction-stdout")) or __import__("re").fullmatch(r"simulated-opinion-(?:0[0-9]|1[0-9])", label):
''')
router = sub(router, '''        if len([label for label in member_map if "simulated-opinion-" in label.name]) != 20:
''', '''        if len([path for path in member_map if __import__("re").fullmatch(
                r"[0-9]{8}-simulated-opinion-(?:0[0-9]|1[0-9])\\.raw", path.name)]) != 20:
''')
main_at = router.index('\ndef main():')
router = router[:main_at] + '''
def _pinned_native_report():
    relative = os.getenv("RESEARCHOS_W09_NATIVE_REPORT_REF", "")
    expected = os.getenv("RESEARCHOS_W09_NATIVE_REPORT_SHA256", "")
    if not relative or len(expected) != 64:
        raise ValueError("SEALED_NATIVE_REPORT_NOT_GIVEN")
    path = _inside_repo(relative)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("SEALED_NATIVE_REPORT_DRIFT")
    report = json.loads(raw)
    if report.get("formal_construction_acceptance") != "NOT_RUN_POSTRUN_REVIEW_PENDING":
        raise ValueError("NATIVE_PRODUCER_PRETENDS_FORMAL")
    tool_ref = os.getenv("RESEARCHOS_W09_TOOL_RUN_REF", "")
    tool_sha = os.getenv("RESEARCHOS_W09_TOOL_RUN_SHA256", "")
    tool_path = _inside_repo(tool_ref)
    tool_raw = tool_path.read_bytes()
    if hashlib.sha256(tool_raw).hexdigest() != tool_sha:
        raise ValueError("NATIVE_TOOL_RUN_PIN_DRIFT")
    tool = json.loads(tool_raw)
    if (tool.get("schema") != "researchos.w09-native-producer-tool-run.v1"
            or tool.get("report_ref") != relative or tool.get("report_sha256") != expected
            or tool.get("run_id") != report.get("run_id")
            or tool.get("actual_invocation") != report.get("actual_invocation")
            or tool.get("native_exit_code") != report.get("exit_code")
            or tool.get("stdout_ref") != report.get("raw_evidence_references", [None])[0]
            or tool.get("stderr_ref") != report.get("raw_evidence_references", [None, None])[1]
            or tool.get("stdout_sha256") != _pin(tool["stdout_ref"])["sha256"]
            or tool.get("stderr_sha256") != _pin(tool["stderr_ref"])["sha256"]):
        raise ValueError("NATIVE_TOOL_RUN_NOT_SAME_RUN")
    source = dict(report)
    source["report_reference"] = relative
    return source, report, tool


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"test.retrieval", "test.research.fixture", "test.security"}:
        return _failure("INVALID_COMMAND_KEY")
    route = (sys.argv[1], os.getenv("RESEARCHOS_TASK_ID", ""),
             os.getenv("RESEARCHOS_CHECK_ID", ""), os.getenv("RESEARCHOS_CASE_ID", ""))
    if route not in NATIVE and route not in PRESERVED:
        return _failure("UNBOUND_SELECTOR_TUPLE")
    if not (ROOT / "execution/toolchains/locked.json").is_file():
        return _failure("WRONG_REPOSITORY_CWD")
    if route in PRESERVED:
        go = os.getenv("RESEARCHOS_GO", "")
        if route[1] == "W09":
            argv = [sys.executable, "-X", "utf8", str(ROOT / "tests/evidence/check/main.py")]
        elif route[1] == "W08":
            if not go: return _failure("MISSING_LOCKED_GO")
            argv = [go, "run", "./tests/research/check"]
        else:
            if not go: return _failure("MISSING_LOCKED_GO")
            argv = [go, "run", "./tests/security/check"]
        child = subprocess.run(argv, cwd=ROOT, env=os.environ.copy(),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               check=False, shell=False)
        sys.stderr.buffer.write(child.stderr)
        sys.stdout.buffer.write(child.stdout)
        return child.returncode
    try:
        source, report, tool = _pinned_native_report()
        pins, report, native = _native_exact(source, route)
        owned = _owned_exact(source, report, route)
        mode = _mode_review(source, report, route, owned, native)
        if mode.get("formal_authority") is not False:
            raise ValueError("MODE_REVIEW_MUST_NOT_SELF_ACCEPT")
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        return _failure("SEALED_NATIVE_OR_POSTRUN_MODE_OPEN", type(exc).__name__)
    print(json.dumps({"status": "PASS", "assertion_ids": list(FORMAL[route]),
                      "assertions": len(FORMAL[route]), "task_id": "W09",
                      "check_id": route[2] or None, "case_id": route[3] or None,
                      "native_assertion_ids": list(NATIVE[route]),
                      "source_pins": pins, "owned_export_member_count": len(owned["members"]),
                      "native_tool_run_ref": os.getenv("RESEARCHOS_W09_TOOL_RUN_REF"),
                      "mode_evidence": mode,
                      "formal_acceptance": "PENDING_INDEPENDENT_VERIFIER"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
pending["w09_formal_router.v5.proposed.py"] = router

producer = (old / "retrieval.proposed.py").read_text(encoding="utf-8")
producer = sub(producer, '''    stdout.write_bytes(out)
    stderr.write_bytes(err)
''', '''    with stdout.open("xb") as stream: stream.write(out)
    with stderr.open("xb") as stream: stream.write(err)
''')
producer = sub(producer, '''        "formal_construction_acceptance": "PENDING_INDEPENDENT_VERIFIER",
''', '''        "formal_construction_acceptance": "NOT_RUN_POSTRUN_REVIEW_PENDING",
        "formal_case_accepted_delta": 0,
''')
producer = sub(producer, '''    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    report["report_reference"] = str(path.relative_to(ROOT)).replace("\\\\", "/")
    print(json.dumps({key: value for key, value in report.items() if key not in {"assertion_results", "owned_export"}}, ensure_ascii=False))
''', '''    with path.open("xb") as stream:
        stream.write((json.dumps(report, ensure_ascii=False, indent=2) + "\\n").encode("utf-8"))
    report_ref = str(path.relative_to(ROOT)).replace("\\\\", "/")
    tool_run = {"schema": "researchos.w09-native-producer-tool-run.v1",
                "run_id": report["run_id"], "report_ref": report_ref,
                "report_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "native_exit_code": report.get("exit_code"),
                "actual_invocation": report.get("actual_invocation"),
                "stdout_ref": report.get("raw_evidence_references", [None])[0],
                "stderr_ref": report.get("raw_evidence_references", [None, None])[1],
                "stdout_sha256": hashlib.sha256((evidence / "go-test.stdout.jsonl").read_bytes()).hexdigest()
                                 if (evidence / "go-test.stdout.jsonl").is_file() else None,
                "stderr_sha256": hashlib.sha256((evidence / "go-test.stderr.txt").read_bytes()).hexdigest()
                                 if (evidence / "go-test.stderr.txt").is_file() else None,
                "formal_acceptance": "NOT_RUN"}
    tool_path = evidence / "native-tool-run.json"
    with tool_path.open("xb") as stream:
        stream.write((json.dumps(tool_run, ensure_ascii=False, indent=2) + "\\n").encode("utf-8"))
    report["report_reference"] = report_ref
    report["tool_run_reference"] = str(tool_path.relative_to(ROOT)).replace("\\\\", "/")
    report["tool_run_sha256"] = hashlib.sha256(tool_path.read_bytes()).hexdigest()
    print(json.dumps({key: value for key, value in report.items() if key not in {"assertion_results", "owned_export"}}, ensure_ascii=False))
''')
pending["retrieval.v5.proposed.py"] = producer

test = (old / "retrieval_test.proposed.go").read_text(encoding="utf-8")
test = sub(test, '''	if _, err = f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), filepath.Join(base, "materialized-v1")); err != nil {
		t.Fatal(err)
	}
'''.replace('+',''), '''	initialManifest, err := f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), filepath.Join(base, "materialized-v1"))
	if err != nil { t.Fatal(err) }
	w09ExportEvent(t, "a06-bundle-initial", Object{"task_id": task["id"], "principal_id": f.owner,
		"root_id": rootID, "source_artifact_id": artifact["id"],
		"authorized_snapshot_ids": bundle["authorized_snapshot_ids"]})
	w09ExportEvent(t, "a06-materialize-initial", Object{"task_id": task["id"],
		"target_path": filepath.Join(base, "materialized-v1"), "accepted": true,
		"manifest": w09ExportRaw(t, "a06-materialize-v1-manifest", Bytes(initialManifest))})
''')
test = sub(test, '''	if _, err = f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), filepath.Join(base, "stale-context")); err == nil {
		t.Fatal("old context materialized changed bytes")
	}
'''.replace('+',''), '''	if _, err = f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), filepath.Join(base, "stale-context")); err == nil {
		t.Fatal("old context materialized changed bytes")
	}
	w09ExportEvent(t, "a06-materialize-stale-rejected", Object{"task_id": task["id"],
		"target_path": filepath.Join(base, "stale-context"), "accepted": false,
		"actual_error": err.Error()})
''')
test = sub(test, '''	if containsSnapshot(Arr(newBundle, "authorized_snapshot_ids"), Str(artifact, "id")) || containsSnapshot(Arr(newBundle, "authorized_snapshot_ids"), Str(deletedArtifact, "id")) {
		t.Fatal("new context retained invalid snapshots", newBundle)
	}
'''.replace('+',''), '''	if containsSnapshot(Arr(newBundle, "authorized_snapshot_ids"), Str(artifact, "id")) || containsSnapshot(Arr(newBundle, "authorized_snapshot_ids"), Str(deletedArtifact, "id")) {
		t.Fatal("new context retained invalid snapshots", newBundle)
	}
	w09ExportEvent(t, "a06-bundle-after-delete", Object{"task_id": task["id"],
		"root_id": rootID, "principal_id": f.owner,
		"authorized_snapshot_ids": newBundle["authorized_snapshot_ids"],
		"deleted_artifact_id": deletedArtifact["id"]})
''')
test = sub(test, '''	if err != nil || strings.Contains(string(Bytes(manifest)), "gamma deleted v3") {
		t.Fatal("invalid body materialized", err, manifest)
	}
'''.replace('+',''), '''	if err != nil || strings.Contains(string(Bytes(manifest)), "gamma deleted v3") {
		t.Fatal("invalid body materialized", err, manifest)
	}
	w09ExportEvent(t, "a06-materialize-after-delete", Object{"task_id": task["id"],
		"target_path": filepath.Join(base, "materialized-after-delete"), "accepted": true,
		"manifest": w09ExportRaw(t, "a06-materialize-after-delete-manifest", Bytes(manifest))})
''')
pending["retrieval_test.v5.proposed.go"] = test

# All anchors and static Python syntax must validate before creating any output.
import ast
for name, body in pending.items():
    if name.endswith(".py"):
        ast.parse(body, filename=name)
for name, body in pending.items():
    with (here / name).open("xb") as stream:
        stream.write(body.encode("utf-8"))
print("V5_SOURCE_FILES", len(pending))
