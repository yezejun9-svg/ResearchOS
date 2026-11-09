"""Proposal generator only. Reads Main sources; writes candidate files within this NS."""
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
HERE = Path(__file__).resolve().parent


def replace_one(body, old, new):
    count = body.count(old)
    if count != 1:
        raise ValueError(f"anchor cardinality {count}: {old[:90]!r}")
    return body.replace(old, new, 1)


def save_candidate(relative, output, transform):
    source = ROOT / relative
    old = source.read_text(encoding="utf-8")
    new = transform(old)
    (HERE / output).write_text(new, encoding="utf-8", newline="\n")
    diff = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                        fromfile="a/" + relative, tofile="b/" + relative))
    (HERE / (output + ".diff")).write_text(diff, encoding="utf-8", newline="\n")
    return source, HERE / output


def domain_test(body):
    body = replace_one(body, "\tt                     *testing.T\n}",
                       "\tt                     *testing.T\n}")  # assert exact struct without mutation
    old = "\tw := httptest.NewRecorder()\n\tf.h.ServeHTTP(w, r)\n\tvar o Object"
    new = "\tw := httptest.NewRecorder()\n\tf.h.ServeHTTP(w, r)\n\tw09ExportHTTP(f.t, method, path, key, etag, raw, w.Code, w.Body.Bytes(), w.Header().Get(\"ETag\"), w.Header().Get(\"Content-Type\"))\n\tvar o Object"
    return replace_one(body, old, new)


def retrieval_test(body):
    old = "\tline, _ := json.Marshal(Object{\"assertion_id\": id, \"status\": \"PASS\", \"evidence\": evidence})\n\tfmt.Println(\"W09_ASSERTION \" + string(line))"
    new = "\tvalue := Object{\"assertion_id\": id, \"status\": \"PASS\", \"evidence\": evidence}\n\tif pin := w09ExportEvent(t, \"assertion-\"+id, Object{\"assertion_id\": id, \"expected\": w09Expected(id), \"actual\": evidence, \"status\": \"PASS\"}); pin != nil { value[\"owned_export_ref\"] = pin }\n\tline, _ := json.Marshal(value)\n\tfmt.Println(\"W09_ASSERTION \" + string(line))"
    body = replace_one(body, old, new)
    old = "\t\ttext := []byte(fmt.Sprintf(\"simulated agent opinion %d\", i))\n\t\tu := f.expect"
    new = "\t\ttext := []byte(fmt.Sprintf(\"simulated agent opinion %d\", i))\n\t\tw09ExportRaw(t, fmt.Sprintf(\"simulated-opinion-%02d\", i), text)\n\t\tu := f.expect"
    body = replace_one(body, old, new)
    old = "\tif err = f.s.RecordEvidenceOrigin(context.Background(), f.token, f.project, Str(unknown, \"id\"), Str(original, \"id\"), Str(copyArtifact, \"id\"), rootID, \"unknown.txt\"); err == nil {"
    new = "\tw09ExportEvent(t, \"c19-complete-graph-before\", Object{\"records\": summary[\"records\"], \"counts\": summary, \"evidence_ids\": ids, \"root_id\": rootID})\n\tw09ExportOriginRows(t, f, \"c19-before\")\n\tfor _, name := range []string{\"original.txt\", \"experiment.txt\", \"repost-0.txt\", \"repost-1.txt\", \"repost-2.txt\", \"repost-3.txt\", \"unknown.txt\"} { w09ExportFile(t, \"c19-before-\"+name, filepath.Join(rootPath, name), rootID) }\n\tw09ExportState(t, f, \"c19-before\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tif err = f.s.RecordEvidenceOrigin(context.Background(), f.token, f.project, Str(unknown, \"id\"), Str(original, \"id\"), Str(copyArtifact, \"id\"), rootID, \"unknown.txt\"); err == nil {\n\t\tt.Fatal(\"same-content body without explicit source citation was falsely linked\")\n\t}"
    new = old + "\n\tw09ExportEvent(t, \"c19-unsupported-relation-rejection\", Object{\"unknown_id\": unknown[\"id\"], \"proposed_origin_id\": original[\"id\"], \"actual_error\": err.Error()})"
    body = replace_one(body, old, new)
    old = "\tw09Assertion(t, \"C19-04\", Object{\"primary_changed\": true, \"remaining_independent_roots\": 1, \"retained_records\": 27})"
    new = "\tw09ExportFile(t, \"c19-primary-changed\", filepath.Join(rootPath, \"original.txt\"), rootID)\n\tw09ExportEvent(t, \"c19-complete-graph-after\", Object{\"records\": summary[\"records\"], \"counts\": summary, \"evidence_ids\": ids, \"root_id\": rootID})\n\tw09ExportOriginRows(t, f, \"c19-after\")\n\tw09ExportState(t, f, \"c19-after\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tbefore, err := f.s.EvidenceSupportSummary(context.Background(), f.token, f.project, []string{Str(leaf, \"id\")})"
    new = "\tfor _, name := range []string{\"primary.txt\", \"middle.txt\", \"leaf.txt\"} { w09ExportFile(t, \"chain-before-\"+name, filepath.Join(rootPath, name), rootID) }\n\tw09ExportOriginRows(t, f, \"chain-before\")\n" + old
    body = replace_one(body, old, new)
    old = "\tw09Assertion(t, \"C19-05\", Object{\"before\": before, \"after\": after, \"new_relation_rejected\": true, \"intermediate_validity\": f.read(\"evidence\", Str(middle, \"id\"))[\"validity\"]})"
    new = "\tw09ExportFile(t, \"chain-middle-removed\", filepath.Join(rootPath, \"middle.txt\"), rootID)\n\tw09ExportEvent(t, \"chain-before-after\", Object{\"before\": before, \"after\": after, \"primary_id\": primary[\"id\"], \"middle_id\": middle[\"id\"], \"leaf_id\": leaf[\"id\"]})\n\tw09ExportOriginRows(t, f, \"chain-after\")\n\tw09ExportState(t, f, \"chain-after\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tartifact, evidence := w09LocalEvidence(t, f, rootID, \"same.txt\", \"alpha current v1\")"
    new = "\tw09ExportFile(t, \"a06-initial-authorized\", filepath.Join(aRoot, \"same.txt\"), rootID)\n\tw09ExportFile(t, \"a06-initial-denied\", filepath.Join(bRoot, \"same.txt\"), \"\")\n\tw09ExportState(t, f, \"a06-before-capture\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\t\tif _, err = f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, escape); err == nil {\n\t\t\tt.Fatal(\"escaped root\", escape)\n\t\t}"
    new = old + "\n\t\tw09ExportEvent(t, \"a06-escape-rejection\", Object{\"attempted_path\": escape, \"actual_error\": err.Error(), \"accepted\": false})"
    body = replace_one(body, old, new)
    old = "\t// Even before the maintenance projection, the old key must not replay v1."
    new = "\tw09ExportFile(t, \"a06-modified\", filepath.Join(aRoot, \"same.txt\"), rootID)\n\tw09ExportState(t, f, \"a06-modified-before-refresh\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tstate = f.state()\n\tmoveQuery := Object{\"query\": \"beta\""
    new = "\tw09ExportFile(t, \"a06-moved-source-absent\", filepath.Join(aRoot, \"same.txt\"), rootID)\n\tw09ExportFile(t, \"a06-moved-destination\", filepath.Join(bRoot, \"moved-out.txt\"), \"\")\n\tw09ExportState(t, f, \"a06-moved-before-refresh\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tstate = f.state()\n\tdeleteQuery := Object{\"query\": \"gamma\""
    new = "\tw09ExportFile(t, \"a06-deleted\", filepath.Join(aRoot, \"same.txt\"), rootID)\n\tw09ExportState(t, f, \"a06-deleted-before-refresh\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tw09Assertion(t, \"A06-01\", Object{\"modified_stale\": true"
    new = "\tw09ExportFile(t, \"a06-revoked-body\", filepath.Join(aRoot, \"same.txt\"), rootID)\n\tw09ExportState(t, f, \"a06-revoked\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tif first[\"id\"] == second[\"id\"] {"
    new = "\tw09ExportFile(t, \"a06-fts-file-1\", filepath.Join(root, \"same.txt\"), rootID)\n\tw09ExportFile(t, \"a06-fts-file-2\", filepath.Join(root, \"nested\", \"same.txt\"), rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tif _, err = f.db.Exec(\"DROP TABLE retrieval_fts\"); err != nil {"
    new = "\tw09ExportEvent(t, \"a06-indexed-result\", Object{\"result\": indexed, \"first_artifact\": first, \"second_artifact\": second})\n\tw09ExportState(t, f, \"a06-fts-indexed\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tw09Assertion(t, \"A06-03\", Object{\"indexed_hits\": 2"
    new = "\tw09ExportEvent(t, \"a06-fallback-result\", Object{\"result\": fallback, \"retrieval_fts_table_dropped\": true})\n\tw09ExportState(t, f, \"a06-fts-fallback\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tw09Assertion(t, \"W09-G02-ROOT-REPLACEMENT\", Object{"
    new = "\tw09ExportFile(t, \"g02-replacement-path\", aRoot, rootID)\n\tw09ExportFile(t, \"g02-denied-target\", filepath.Join(bRoot, \"same.txt\"), \"\")\n\tw09ExportState(t, f, \"g02-replacement-after-refresh\", rootID)\n\tw09ExportEvent(t, \"g02-os-branch\", Object{\"goos\": runtime.GOOS, \"goarch\": runtime.GOARCH, \"junction_branch\": runtime.GOOS == \"windows\"})\n" + old
    body = replace_one(body, old, new)
    old = "\tw09Assertion(t, \"W09-G02-UNICODE-LOCATOR\", Object{"
    new = "\tw09ExportFile(t, \"g02-unicode-input\", filepath.Join(root, \"unicode.txt\"), rootID)\n\tw09ExportState(t, f, \"g02-unicode\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tif err = os.Rename(aRoot, filepath.Join(base, \"A-original\")); err != nil {"
    new = "\tw09ExportFile(t, \"g02-authorized-before-replacement\", filepath.Join(aRoot, \"same.txt\"), rootID)\n\tw09ExportFile(t, \"g02-denied-before-replacement\", filepath.Join(bRoot, \"same.txt\"), \"\")\n\tw09ExportState(t, f, \"g02-before-replacement\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tif err = os.Remove(filepath.Join(source, \"input.txt\")); err != nil {"
    new = "\tw09ExportFile(t, \"g02-stale-input-before-delete\", filepath.Join(source, \"input.txt\"), rootID)\n\tw09ExportState(t, f, \"g02-before-delete\", rootID)\n" + old
    body = replace_one(body, old, new)
    old = "\tw09Assertion(t, \"W09-G02-STALE-INPUT-BODY\", Object{"
    new = "\tw09ExportFile(t, \"g02-stale-input-after-delete\", filepath.Join(source, \"input.txt\"), rootID)\n\tw09ExportState(t, f, \"g02-after-delete\", rootID)\n\tw09ExportEvent(t, \"g02-clean-context-manifest\", manifest)\n" + old
    body = replace_one(body, old, new)
    old = "\tw09Assertion(t, \"W09-G02-LEGACY-ROOT\", Object{"
    new = "\tw09ExportEvent(t, \"g02-legacy-sql-observation\", Object{\"root_identity\": identity, \"revoked\": revoked, \"revision\": revision, \"source\": \"SELECT root_identity,revoked,revision FROM retrieval_roots\"})\n" + old
    body = replace_one(body, old, new)
    return body


def retrieval_runner(body):
    old = '"env": os.environ.copy()}\n    if os.name == "nt":'
    new = '"env": os.environ.copy()}\n    owned = evidence / "owned"\n    owned.mkdir(mode=0o700)\n    options["env"]["RESEARCHOS_W09_EVIDENCE_DIR"] = str(owned.resolve())\n    if os.name == "nt":'
    body = replace_one(body, old, new)
    old = '        report.update(status="PASS" if okay else "FAIL", assertions=len(found), assertion_ids=found,'
    new = '        owned = evidence / "owned"\n        export = collect_w09_owned(owned, selected, records)\n        okay = okay and export["complete"]\n        report["owned_export"] = export\n' + old
    body = replace_one(body, old, new)
    old = '    print(json.dumps({key: value for key, value in report.items() if key != "assertion_results"}, ensure_ascii=False))'
    new = '    print(json.dumps({key: value for key, value in report.items() if key not in {"assertion_results", "owned_export"}}, ensure_ascii=False))'
    body = replace_one(body, old, new)
    anchor = '\ndef main():\n'
    helper = '''
def collect_w09_owned(owned, selected, records):
    """Pin actual test exports. Missing/foreign/duplicate/changed files fail closed."""
    root = owned.resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("W09_OWNED_EXPORT_ROOT_MISSING")
    pins, paths = [], set()
    for file in sorted(root.rglob("*.raw")):
        resolved = file.resolve(strict=True)
        if root not in resolved.parents or file.is_symlink():
            raise ValueError("W09_FOREIGN_EXPORT")
        relative = str(resolved.relative_to(root)).replace("\\\\", "/")
        if relative in paths:
            raise ValueError("W09_DUPLICATE_EXPORT")
        paths.add(relative)
        data = resolved.read_bytes()
        pins.append({"path": str(resolved.relative_to(ROOT)).replace("\\\\", "/"),
                     "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    asserted = [r.get("owned_export_ref") for r in records]
    if not pins or len(asserted) != len(records) or any(not isinstance(p, dict) for p in asserted):
        return {"complete": False, "reason": "MISSING_ASSERTION_EXPORT", "members": pins}
    member_by_abs = {(ROOT / p["path"]).resolve(): p for p in pins}
    for claim in asserted:
        path = Path(claim["path"]).resolve(strict=True)
        actual = member_by_abs.get(path)
        if actual is None or actual["sha256"] != claim["sha256"] or actual["bytes"] != claim["bytes"]:
            return {"complete": False, "reason": "ASSERTION_EXPORT_DRIFT", "members": pins}
    tests = {p["path"].split("/owned/", 1)[1].split("/", 1)[0] for p in pins if "/owned/" in p["path"]}
    domain_selected = {name for name in selected if TESTS[name][0] == "./internal/domain"}
    return {"complete": tests == domain_selected, "selected_tests": selected,
            "exported_tests": sorted(tests), "assertion_export_refs": asserted, "members": pins}

'''
    body = replace_one(body, anchor, '\n' + helper + 'def main():\n')
    return body


if __name__ == "__main__":
    save_candidate("internal/domain/domain_test.go", "domain_test.proposed.go", domain_test)
    save_candidate("internal/domain/retrieval_test.go", "retrieval_test.proposed.go", retrieval_test)
    save_candidate("ops/ci/retrieval.py", "retrieval.proposed.py", retrieval_runner)
    print("generated 3 source candidates and exact unified diffs")
