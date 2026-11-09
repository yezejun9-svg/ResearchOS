"""Proposed W09 read-only evidence consumer. No formal authority is granted here."""
import hashlib
import json
import os
import platform
import re
import tempfile
from pathlib import Path


def require(ok, code):
    if not ok:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": digest(raw), "bytes": len(raw)}


def verify_native(root, source, report, expected, selected):
    """Rebuild the assertion list and test roster from the pinned Go JSONL bytes."""
    run_id = report.get("run_id")
    require(isinstance(run_id, str) and re.fullmatch(r"[0-9a-f]{32}", run_id), "RUN_ID_MISSING")
    require(source.get("run_id") == run_id and Path(source["report_reference"]).parent.name == "run-" + run_id,
            "CURRENT_RUN_NOT_BOUND")
    refs = source["raw_evidence_references"]
    require(len(refs) == 2 and refs == report.get("raw_evidence_references"), "RAW_REFS_DISAGREE")
    stdout = (root / refs[0]).resolve(strict=True)
    stderr = (root / refs[1]).resolve(strict=True)
    require(stdout.parent == stderr.parent == (root / source["report_reference"]).resolve(strict=True).parent
            and stdout.name == "go-test.stdout.jsonl" and stderr.name == "go-test.stderr.txt", "RAW_RUN_DIR_MISMATCH")
    events = [json.loads(line) for line in stdout.read_bytes().decode("utf-8").splitlines()]
    require(events and all(isinstance(e, dict) and e.get("Action") in
                           {"start", "run", "pause", "cont", "pass", "fail", "skip", "output", "bench"}
                           for e in events), "GO_JSONL_INVALID")
    actions = [(e.get("Action"), e.get("Test")) for e in events if e.get("Test") in selected]
    require(sorted(t for a, t in actions if a == "pass") == sorted(selected)
            and not any(a in {"fail", "skip"} for a, _ in actions), "GO_TEST_ROSTER_NOT_PASS")
    require(not any(e.get("Test") and e["Test"] not in selected and e.get("Action") in {"pass", "fail", "skip"}
                    for e in events), "FOREIGN_GO_TEST")
    assertions = []
    for event in events:
        output = event.get("Output", "")
        require(isinstance(output, str), "GO_OUTPUT_NOT_TEXT")
        for line in output.splitlines():
            if line.startswith("W09_ASSERTION "):
                item = json.loads(line[len("W09_ASSERTION "):])
                require(isinstance(item, dict) and event.get("Test") == item.get("test_name")
                        and item.get("test_name") in selected, "ASSERTION_STDOUT_OWNER_MISMATCH")
                item["raw_evidence_reference"] = refs[0]
                assertions.append(item)
    require(assertions == report.get("assertion_results") and len(assertions) == len(expected)
            and sorted(x.get("assertion_id") for x in assertions) == sorted(expected)
            and all(x.get("run_id") == run_id and x.get("status") == "PASS" for x in assertions),
            "STDOUT_ASSERTION_REPLAY_MISMATCH")
    locked_path = root / "execution/toolchains/locked.json"
    locked_raw = locked_path.read_bytes()
    locked = json.loads(locked_raw)
    vm = report.get("version_manifest", {})
    require(vm.get("go_lock_sha256") == "sha256:" + digest(locked_raw), "GO_LOCK_PIN_MISMATCH")
    go = report.get("go_executable")
    require(isinstance(go, dict) and isinstance(go.get("path"), str), "ACTUAL_GO_MISSING")
    go_path = Path(go["path"]).resolve(strict=True)
    require(go == file_pin(go_path) and go_path == Path(locked["tools"]["go"]["path"]).resolve(strict=True)
            and go["sha256"] == locked["tools"]["go"]["sha256"], "ACTUAL_GO_NOT_LOCKED")
    packages = sorted({"./internal/domain" if t.startswith("TestW09") and t not in
                       {"TestW09RootReadRejectsEscape", "TestW09RootIdentityRejectsReplacement"}
                       else "./adapters/retrieval" for t in selected})
    argv = [report["actual_invocation"][0], "test", "-count=1", "-json", "-run",
            "^(?:" + "|".join(selected) + ")$", *packages]
    require(report.get("actual_invocation") == source.get("actual_invocation") == argv
            and Path(argv[0]).resolve(strict=True) == go_path, "ACTUAL_INVOCATION_MISMATCH")
    source_hashes = vm.get("source_sha256")
    require(isinstance(source_hashes, dict) and all(isinstance(k, str) and v ==
            "sha256:" + digest((root / k).read_bytes()) for k, v in source_hashes.items())
            and {"internal/domain/retrieval_test.go", "internal/domain/domain_test.go",
                 "internal/domain/w09_evidence_export_test.go", "ops/ci/retrieval.py",
                 "ops/ci/w09_formal_router.py", "ops/ci/w09_evidence_closure.py"} <= set(source_hashes),
            "CURRENT_SOURCE_CLOSURE_MISMATCH")
    return {"run_id": run_id, "stdout": file_pin(stdout), "stderr": file_pin(stderr),
            "go": go, "source_hashes": source_hashes, "records": assertions}


def verify_owned(root, source, report, selected, owner):
    """Index each event by its real path and bind all assertion claims by ID."""
    owned = (root / source["report_reference"]).resolve(strict=True).parent / "owned"
    require(owned.is_dir() and not owned.is_symlink(), "OWNED_DIR_MISSING")
    claims = report.get("owned_export", {}).get("members")
    require(isinstance(claims, list) and claims, "OWNED_MANIFEST_MISSING")
    members, events = {}, {}
    opaque = ("http-request", "http-response", "file-body-", "simulated-opinion-", "g02-junction-stdout")
    for claim in claims:
        require(isinstance(claim, dict) and set(claim) == {"path", "sha256", "bytes"}, "OWNED_CLAIM_SHAPE")
        lexical = root / claim["path"]
        require(not lexical.is_symlink(), "OWNED_MEMBER_SYMLINK")
        path = lexical.resolve(strict=True)
        require(owned in path.parents and path not in members and not path.is_symlink()
                and re.fullmatch(r"[0-9]{8}-.+\.raw", path.name)
                and path.parent.name in selected, "OWNED_FOREIGN_OR_DUPLICATE")
        data = path.read_bytes()
        require(claim == {"path": str(path.relative_to(root)).replace("\\", "/"),
                          "sha256": digest(data), "bytes": len(data)}, "OWNED_PIN_DRIFT")
        members[path] = claim
        label = path.name.split("-", 1)[1][:-4]
        if label.startswith(opaque):
            continue
        item = json.loads(data)
        require(isinstance(item, dict) and item.get("_run_id") == report["run_id"]
                and item.get("_test_name") == path.parent.name, "EVENT_CURRENT_RUN_OR_OWNER_MISMATCH")
        events.setdefault(label, []).append({"value": item, "path": path, "pin": claim,
                                             "test": path.parent.name})
    require(set(members) == {p.resolve(strict=True) for p in owned.rglob("*.raw")}, "OWNED_SET_INCOMPLETE")
    require({p.parent.name for p in members} == {t for t in selected if t not in
            {"TestW09RootReadRejectsEscape", "TestW09RootIdentityRejectsReplacement"}}, "OWNED_TEST_SET_MISMATCH")
    for rec in report["assertion_results"]:
        aid = rec["assertion_id"]
        group = events.get("assertion-" + aid, [])
        require(len(group) == 1 and group[0]["test"] == owner[aid]
                and rec.get("owned_export_ref") == {"path": str(group[0]["path"]),
                                                   "sha256": group[0]["pin"]["sha256"],
                                                   "bytes": group[0]["pin"]["bytes"]},
                "ASSERTION_ID_PATH_PIN_MISMATCH")
        raw = group[0]["value"]
        require(raw.get("assertion_id") == aid and raw.get("actual") == rec.get("evidence")
                and raw.get("status") == "PASS" and isinstance(raw.get("expected"), dict)
                and all(raw["actual"].get(k) == v for k, v in raw["expected"].items()),
                "ASSERTION_ACTUAL_EXPECTED_MISMATCH")
    return {"members": members, "events": events, "owned": owned}


def only(events, label, test=None):
    group = events.get(label, [])
    require(len(group) == 1 and (test is None or group[0]["test"] == test), "EVENT_MISSING_" + label)
    return group[0]["value"]


def _raw_pin(claim, members, owner=None):
    require(isinstance(claim, dict) and set(claim) == {"path", "sha256", "bytes"}, "RAW_PIN_SHAPE")
    path = Path(claim["path"]).resolve(strict=True)
    require(path in members and (owner is None or path.parent.name == owner)
            and claim["sha256"] == members[path]["sha256"]
            and claim["bytes"] == members[path]["bytes"], "RAW_PIN_NOT_MEMBER")
    return path.read_bytes()


def verify_c19(ctx):
    events, members = ctx["events"], ctx["members"]
    test = "TestW09C19ExplicitOriginAndUnknown"
    before = only(events, "c19-complete-graph-before", test)
    after = only(events, "c19-complete-graph-after", test)
    rows = only(events, "origins-c19-before", test).get("rows")
    after_rows = only(events, "origins-c19-after", test).get("rows")
    require(isinstance(rows, list) and len(rows) == 6 and after_rows == rows,
            "C19_ORIGIN_ROWS_NOT_CLOSED")
    roots = [r for r in rows if r.get("relation") == "ROOT"]
    derived = [r for r in rows if r.get("relation") == "DERIVED"]
    require(len(roots) == 2 and len(derived) == 4 and
            len({r.get("evidence_id") for r in rows}) == 6, "C19_2ROOT_4DERIVED_MISMATCH")
    bindings = [x["value"] for x in events.get("local-evidence-binding", []) if x["test"] == test]
    names = {"original.txt", "experiment.txt", "unknown.txt", *(f"repost-{i}.txt" for i in range(4))}
    require(len(bindings) == 7 and {b.get("relative_path") for b in bindings} == names
            and len({b.get("evidence_id") for b in bindings}) == 7, "C19_SEVEN_INPUT_BINDINGS_MISSING")
    by_name = {b["relative_path"]: b for b in bindings}
    first = by_name["original.txt"]["evidence_id"]
    experiment = by_name["experiment.txt"]["evidence_id"]
    require({r["evidence_id"] for r in roots} == {first, experiment}
            and {r["evidence_id"] for r in derived} == {by_name[f"repost-{i}.txt"]["evidence_id"] for i in range(4)}
            and all(r.get("origin_id") == first for r in derived)
            and all(not r.get("origin_id") for r in roots), "C19_ORIGIN_EDGES_MISMATCH")
    bmap = {b["evidence_id"]: b for b in bindings}
    for r in rows:
        b = bmap[r["evidence_id"]]
        require(r.get("basis_root_id") == b.get("root_id") == before.get("root_id")
                and r.get("basis_relative_path") == b["relative_path"]
                and r.get("basis_artifact_id") == b.get("artifact_id"), "C19_ORIGIN_BASIS_MISMATCH")
    records = before.get("records")
    later = after.get("records")
    require(isinstance(records, list) and len(records) == 27 and isinstance(later, list)
            and len(later) == 27 and len({x.get("evidence_id") for x in records}) == 27
            and {x.get("evidence_id") for x in later} == {x.get("evidence_id") for x in records},
            "C19_GRAPH_27_INCOMPLETE")
    graph = {x["evidence_id"]: x for x in records}
    for name, b in by_name.items():
        row = graph.get(b["evidence_id"])
        require(row is not None and row.get("evidence_kind") == "OBSERVED"
                and row.get("source_kind") == b.get("source_kind"), "C19_OBSERVED_GRAPH_MISMATCH")
        file = only(events, "file-c19-before-" + name, test)
        body = _raw_pin(file.get("body"), members, test)
        require(file.get("exists") is True and file.get("root_id") == b.get("root_id")
                and Path(file["path"]).name == name and b.get("content_hash") == "sha256:" + digest(body),
                "C19_OBSERVED_BYTES_MISMATCH")
        if name.startswith("repost-"):
            require(row.get("root_evidence_id") == first and row.get("origin_relation") == "CONFIRMED"
                    and row.get("origin_evidence_id") == first, "C19_REPOST_GRAPH_MISMATCH")
        elif name == "unknown.txt":
            require(row.get("origin_relation") == "UNKNOWN" and not row.get("root_evidence_id")
                    and b["artifact_id"] == by_name["original.txt"]["artifact_id"]
                    and b["content_hash"] == by_name["original.txt"]["content_hash"],
                    "C19_UNKNOWN_COPY_FALSE_ORIGIN")
        else:
            require(row.get("root_evidence_id") == b["evidence_id"]
                    and row.get("origin_relation") == "CONFIRMED", "C19_ROOT_GRAPH_MISMATCH")
    simulations = [x["value"] for x in events.get("simulated-opinion-binding", []) if x["test"] == test]
    require(len(simulations) == 20 and {s.get("ordinal") for s in simulations} == set(range(20)),
            "C19_TWENTY_SIM_INPUTS_MISSING")
    for s in simulations:
        body = _raw_pin(s.get("body"), members, test)
        row = graph.get(s.get("evidence_id"))
        require(body == f"simulated agent opinion {s['ordinal']}".encode()
                and s.get("content_hash") == "sha256:" + digest(body)
                and s.get("evidence_kind") == "SIMULATED" and s.get("measurement_mode") == "FIXTURE"
                and s.get("source_kind") == "SIMULATION" and row is not None
                and row.get("evidence_kind") == "SIMULATED" and row.get("source_kind") == "SIMULATION",
                "C19_SIM_INPUT_GRAPH_MISMATCH")
    require({s["evidence_id"] for s in simulations} | set(bmap) == set(graph), "C19_INPUT_GRAPH_SET_MISMATCH")
    require(before.get("counts", {}).get("independent_observed_count") == 2
            and before["counts"].get("simulated_count") == 20 and before["counts"].get("unknown_count") == 1
            and after.get("counts", {}).get("independent_observed_count") == 1
            and after["counts"].get("unknown_count") == 6, "C19_COUNT_TRANSITION_MISMATCH")
    chain_test = "TestW09C19ChainInvalidation"
    chain = only(events, "chain-before-after", chain_test)
    chain_rows = only(events, "origins-chain-before", chain_test).get("rows")
    chain_after = only(events, "origins-chain-after", chain_test).get("rows")
    require(isinstance(chain_rows, list) and len(chain_rows) == 3 and chain_rows == chain_after
            and {r.get("relation") for r in chain_rows} == {"ROOT", "DERIVED"},
            "C19_CHAIN_ORIGINS_MISSING")
    edges = {r["evidence_id"]: r for r in chain_rows}
    require(edges[chain["primary_id"]].get("relation") == "ROOT"
            and edges[chain["middle_id"]].get("origin_id") == chain["primary_id"]
            and edges[chain["leaf_id"]].get("origin_id") == chain["middle_id"]
            and chain.get("before", {}).get("independent_observed_count") == 1
            and chain.get("after", {}).get("independent_observed_count") == 0
            and chain["after"].get("unknown_count") == 1
            and only(events, "file-chain-middle-removed", chain_test).get("exists") is False,
            "C19_CHAIN_INVALIDATION_NOT_CLOSED")
    changed = only(events, "file-c19-primary-changed", test)
    require("withdrawn" in _raw_pin(changed.get("body"), members, test).decode("utf-8")
            and only(events, "c19-unsupported-relation-rejection", test).get("actual_error"),
            "C19_INVALIDATION_OR_REJECTION_MISSING")


def verify_a06(ctx):
    events, members = ctx["events"], ctx["members"]
    test = "TestW09A06HTTPInvalidationAndContext"
    stages = ("before-capture", "modified-before-refresh", "moved-before-refresh",
              "deleted-before-refresh", "revoked")
    states = [only(events, "state-a06-" + stage, test) for stage in stages]
    require(len({s.get("root_id") for s in states}) == 1
            and len({s.get("root_path") for s in states}) == 1
            and states[0].get("root_revoked") == 0 and states[-1].get("root_revoked") == 1
            and all(isinstance(s.get("project_state"), dict) and isinstance(s.get("actual_grants"), list)
                    and isinstance(s.get("actual_index"), list)
                    and isinstance(s.get("actual_snapshots"), list) and s.get("grant_count", 0) >= 1
                    for s in states), "A06_PERMISSION_ROOT_STATE_MISSING")
    labels = ("initial-authorized", "initial-denied", "modified", "moved-source-absent",
              "moved-destination", "deleted", "revoked-body")
    files = {label: only(events, "file-a06-" + label, test) for label in labels}
    require(files["initial-authorized"].get("exists") is True
            and files["modified"].get("exists") is True
            and files["moved-source-absent"].get("exists") is False
            and files["deleted"].get("exists") is False
            and files["revoked-body"].get("exists") is True
            and all(files[name].get("root_id") == states[0]["root_id"] for name in
                    ("initial-authorized", "modified", "moved-source-absent", "deleted", "revoked-body"))
            and files["initial-denied"].get("root_id") == files["moved-destination"].get("root_id") == "",
            "A06_FILE_PHASE_NOT_BOUND")
    for name in ("initial-authorized", "initial-denied", "modified", "moved-destination", "revoked-body"):
        require(files[name].get("type") == "regular" and
                len(_raw_pin(files[name].get("body"), members, test)) == files[name].get("size"),
                "A06_FILE_BODY_NOT_BOUND")
    require(_raw_pin(files["initial-authorized"]["body"], members, test) == b"alpha current v1"
            and _raw_pin(files["modified"]["body"], members, test) == b"beta changed v2"
            and _raw_pin(files["revoked-body"]["body"], members, test) == b"delta for revocation v4"
            and b"SECRET-B-UNAUTHORIZED" in _raw_pin(files["initial-denied"]["body"], members, test),
            "A06_PHASE_BYTES_MISMATCH")
    original_hash = "sha256:" + digest(_raw_pin(files["initial-authorized"]["body"], members, test))
    modified_hash = "sha256:" + digest(_raw_pin(files["modified"]["body"], members, test))
    revoked_hash = "sha256:" + digest(_raw_pin(files["revoked-body"]["body"], members, test))
    original_rows = [r for r in states[1]["actual_snapshots"] if r.get("relative_path") == "same.txt"
                     and r.get("root_id") == states[0]["root_id"] and r.get("content_hash") == original_hash]
    require(len(original_rows) == 1 and original_rows[0].get("status") == "CURRENT"
            and any(r.get("content_hash") == modified_hash for r in states[2]["actual_snapshots"])
            and any(r.get("content_hash") == revoked_hash and r.get("status") == "REVOKED"
                    for r in states[-1]["actual_snapshots"]), "A06_SNAPSHOT_ROWS_NOT_BOUND_TO_BYTES")
    exchanges = [x["value"] for x in events.get("http-exchange", []) if x["test"] == test]
    require(exchanges, "A06_HTTP_MISSING")
    search = {}
    for x in exchanges:
        request = _raw_pin(x.get("request"), members, test)
        response = _raw_pin(x.get("response"), members, test)
        require(x.get("delivery") == "IN_PROCESS_HTTptest_RECORDER"
                and x.get("authorization_header_exported") is False
                and b"SECRET-B-UNAUTHORIZED" not in response, "A06_HTTP_DELIVERY_OR_LEAK")
        if x.get("method") == "POST" and x.get("path", "").endswith("/search"):
            query = json.loads(request).get("query")
            search.setdefault((query, x.get("status")), []).append(json.loads(response))
    for key, minimum in {("alpha", 200): 2, ("alpha", 412): 1, ("different", 409): 1,
                         ("beta", 200): 1, ("gamma", 200): 1, ("delta", 200): 1}.items():
        require(len(search.get(key, [])) >= minimum, "A06_HTTP_PHASE_MISSING_" + str(key))
    for query in ("beta", "gamma", "delta"):
        require(any(not r.get("hits") for r in search[(query, 200)]), "A06_STALE_SEARCH_LEAK")
    alpha_initial = [r for r in search[("alpha", 200)] if len(r.get("hits", [])) == 1]
    require(alpha_initial and any(r.get("snapshot_hash") and
            r["hits"][0].get("validity") == "CURRENT"
            and r["hits"][0].get("artifact_ref", {}).get("id") == original_rows[0]["artifact_id"]
            for r in alpha_initial),
            "A06_INITIAL_SNAPSHOT_RESPONSE_MISSING")
    revisions = [s.get("project_state", {}).get("revision") for s in states]
    require(all(isinstance(v, int) for v in revisions)
            and revisions == sorted(revisions) and revisions[0] < revisions[-1]
            and states[-1].get("revoked_snapshots", 0) >= 1,
            "A06_REVISION_PERMISSION_TRANSITION_MISSING")
    escapes = [x["value"] for x in events.get("a06-escape-rejection", []) if x["test"] == test]
    require(len(escapes) == 2 and all(x.get("accepted") is False and x.get("actual_error") for x in escapes)
            and any(".." in x["attempted_path"] for x in escapes), "A06_ESCAPE_REJECTION_MISSING")
    fts_test = "TestW09A06FTSFallbackAndDuplicatePath"
    indexed = only(events, "a06-indexed-result", fts_test)
    fallback = only(events, "a06-fallback-result", fts_test)
    si = only(events, "state-a06-fts-indexed", fts_test)
    sf = only(events, "state-a06-fts-fallback", fts_test)
    require(indexed.get("first_artifact", {}).get("id") != indexed.get("second_artifact", {}).get("id")
            and indexed.get("result", {}).get("hits") and len(indexed["result"]["hits"]) == 2
            and fallback.get("retrieval_fts_table_dropped") is True
            and len(fallback.get("result", {}).get("hits", [])) == 2
            and {h.get("backend") for h in indexed["result"]["hits"]} == {"sqlite-fts5"}
            and {h.get("backend") for h in fallback["result"]["hits"]} == {"bounded-scan"}
            and si.get("root_id") == sf.get("root_id")
            and si.get("actual_index") == sf.get("actual_index"), "A06_FTS_SQL_TRANSITION_MISSING")
    needle = [x["value"] for x in events.get("http-exchange", []) if x["test"] == fts_test
              and x["value"].get("path", "").endswith("/search")]
    require(len(needle) == 2 and all(x.get("status") == 200 and
            json.loads(_raw_pin(x["request"], members, fts_test)).get("query") == "needle" for x in needle),
            "A06_FTS_HTTP_NOT_BOUND")
    require(json.loads(_raw_pin(needle[0]["response"], members, fts_test)) == indexed["result"]
            and json.loads(_raw_pin(needle[1]["response"], members, fts_test)) == fallback["result"],
            "A06_FTS_RESPONSE_NOT_SAME")


def verify_mode(root, source, report, route, ctx, native, decision_ref, decision_sha):
    """A later non-author decision must bind this run; absent facts fail closed."""
    require(isinstance(decision_ref, str) and decision_ref and isinstance(decision_sha, str)
            and re.fullmatch(r"[0-9a-f]{64}", decision_sha), "REVIEWED_MODE_DECISION_MISSING")
    decision_path = (root / decision_ref).resolve(strict=True)
    require(root in decision_path.parents and digest(decision_path.read_bytes()) == decision_sha,
            "MODE_DECISION_PIN_DRIFT")
    decision = json.loads(decision_path.read_bytes())
    mode = "LIVE_WINDOWS" if route[2] == "W09-G02" else "FIXTURE"
    require(decision.get("schema") == "researchos.w09-mode-decision.v2"
            and decision.get("route") == list(route) and decision.get("mode") == mode
            and decision.get("run_id") == native["run_id"]
            and decision.get("report_ref") == source["report_reference"]
            and decision.get("report_sha256") == digest((root / source["report_reference"]).read_bytes())
            and decision.get("stdout_sha256") == native["stdout"]["sha256"]
            and decision.get("source_sha256") == native["source_hashes"]
            and decision.get("go_executable") == native["go"]
            and decision.get("producer_id") and decision.get("reviewer_id")
            and decision["producer_id"] != decision["reviewer_id"]
            and decision.get("reviewer_role") == "INDEPENDENT_NON_AUTHOR"
            and decision.get("decision") == "QUALIFIED", "MODE_DECISION_CURRENT_RUN_NOT_CLOSED")
    reviewer_pin = decision.get("independent_review_ref")
    require(isinstance(reviewer_pin, dict) and set(reviewer_pin) == {"path", "sha256", "bytes"},
            "INDEPENDENT_REVIEW_RECEIPT_MISSING")
    reviewer_path = (root / reviewer_pin["path"]).resolve(strict=True)
    report_dir = (root / source["report_reference"]).resolve(strict=True).parent
    require(root in reviewer_path.parents and report_dir not in reviewer_path.parents,
            "REVIEWER_RECEIPT_OWNED_BY_PRODUCER")
    reviewer_raw = reviewer_path.read_bytes()
    require(digest(reviewer_raw) == reviewer_pin["sha256"] and len(reviewer_raw) == reviewer_pin["bytes"],
            "REVIEWER_RECEIPT_PIN_DRIFT")
    review = json.loads(reviewer_raw)
    require(review.get("schema") == "researchos.w09-independent-mode-review.v1"
            and review.get("actor_id") == decision["reviewer_id"]
            and review.get("actor_role") == "INDEPENDENT_NON_AUTHOR"
            and review.get("producer_id") == decision["producer_id"]
            and review.get("run_id") == native["run_id"]
            and review.get("report_sha256") == decision["report_sha256"]
            and review.get("source_sha256") == native["source_hashes"]
            and review.get("go_executable") == native["go"]
            and review.get("run_os") == report["version_manifest"]["os"]
            and review.get("run_os_release") == report["version_manifest"]["os_release"]
            and review.get("decision") == "QUALIFIED", "INDEPENDENT_REVIEW_NOT_CURRENT")
    if mode == "FIXTURE":
        require(decision.get("input_origin") == "OWNED_TEMP_DIR"
                and all(x["value"].get("delivery") == "IN_PROCESS_HTTptest_RECORDER"
                        for x in ctx["events"].get("http-exchange", []))
                and any(x["value"].get("root_path") and
                        Path(x["value"]["root_path"]).is_relative_to(Path(tempfile.gettempdir()))
                        for k, v in ctx["events"].items() if k.startswith("state-") for x in v),
                "FIXTURE_INPUT_NOT_ACTUAL")
    else:
        lock = json.loads((root / "execution/toolchains/locked.json").read_bytes())
        host = decision.get("host_witness")
        junction = decision.get("junction_witness")
        require(os.name == "nt" and platform.system() == "Windows"
                and platform.machine().lower() in {"amd64", "x86_64"}
                and int(platform.version().split(".")[-1]) >= 22000
                and decision.get("locked_go_sha256") == lock["tools"]["go"]["sha256"]
                and isinstance(host, dict) and isinstance(junction, dict), "LIVE_HOST_NOT_ACTUAL")
        for item, schema in ((host, "researchos.w09-host-witness.v1"),
                             (junction, "researchos.w09-junction-witness.v1")):
            raw = (root / item["path"]).read_bytes()
            require(item.get("sha256") == digest(raw) and item.get("bytes") == len(raw), "HOST_WITNESS_PIN")
            witness = json.loads(raw)
            require(witness.get("schema") == schema and witness.get("run_id") == native["run_id"]
                    and witness.get("report_sha256") == decision["report_sha256"]
                    and witness.get("go_executable") == native["go"]
                    and witness.get("source_sha256") == native["source_hashes"]
                    and witness.get("actual_platform") == "Windows 11 x64", "HOST_WITNESS_CURRENT_RUN")
        branch = only(ctx["events"], "g02-os-branch", "TestW09RootReplacementCannotFeedProduct")
        junction_event = only(ctx["events"], "g02-junction-command", "TestW09RootReplacementCannotFeedProduct")
        require(branch.get("goos") == "windows" and branch.get("goarch") == "amd64"
                and branch.get("junction_branch") is True
                and junction_event.get("exit_code") == 0
                and junction_event.get("command", [])[:3] == ["cmd.exe", "/c", "mklink"]
                and junction_event.get("output") == junction.get("output_pin")
                and _raw_pin(junction_event["output"], ctx["members"], "TestW09RootReplacementCannotFeedProduct") is not None,
                "JUNCTION_RAW_NOT_BOUND")
    return {"mode": mode, "decision_ref": decision_ref, "decision_sha256": decision_sha,
            "formal_authority": False}
