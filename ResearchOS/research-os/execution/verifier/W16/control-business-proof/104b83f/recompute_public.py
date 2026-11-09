"""Read public frozen evidence only; never launch a candidate or open authority DB."""
import base64
import hashlib
import json
import ntpath
import re
import sqlite3
from pathlib import Path

WT = Path(r"D:/作品集/ResearchOS/research-os/.local/worktrees/control-business-proof")
EVIDENCE = WT / "execution/receipts/W16/control-business-proof/104b83f"
OUT = Path(__file__).parent


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def encoded(value, sort=False):
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=sort)
    # Match Go encoding/json's escaping. Typed struct field order is retained.
    for a, b in [("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e"), ("\u2028", "\\u2028"), ("\u2029", "\\u2029")]:
        raw = raw.replace(a, b)
    return raw.encode()


def load(name):
    return json.loads((EVIDENCE / name).read_bytes())


def projection(bundle):
    raw = base64.b64decode(bundle["files"]["snapshot.sqlite"])
    assert digest(raw) == bundle["binding"]["snapshot_hash"]
    # The checked-in copy is checkpointed WAL-format SQLite. Python's in-memory
    # deserialize cannot open WAL files; modify only this memory buffer's two
    # journal format bytes. Hash original bytes separately; no evidence modified.
    memory = bytearray(raw)
    original_modes = list(memory[18:20])
    memory[18:20] = b"\x01\x01"
    db = sqlite3.connect(":memory:")
    db.deserialize(memory)
    schema = list(db.execute("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name"))
    data = {"schema": [list(row) for row in schema]}
    nonempty = {}
    for kind, table, _, _ in schema:
        if kind != "table":
            continue
        q = db.execute('SELECT * FROM "' + table.replace('"', '""') + '"')
        columns = [v[0] for v in q.description]
        rows = list(q)
        if rows:
            nonempty[table] = len(rows)
        entries = []
        for row in rows:
            # modernc's zero-length BLOB is a nil []byte and marshals to null.
            values = [None if v == b"" else base64.b64encode(v).decode() if isinstance(v, bytes) else v for v in row]
            entries.append(encoded(values).decode())
        data[table] = {"columns": columns, "rows": sorted(entries)}
    actual = digest(encoded(data, sort=True))
    assert actual == bundle["binding"]["projection_hash"], (actual, bundle["binding"]["projection_hash"])
    kinds = dict(db.execute("SELECT kind,count(*) FROM domain_objects GROUP BY kind"))
    assert set(kinds) <= {"ProjectProfile", "ProjectState", "BudgetPolicy", "RunPolicy", "AcceptancePolicy", "ResearchCycle", "SourceCursor"}
    assert db.execute("SELECT count(*) FROM uploaded_content").fetchone()[0] == 0
    assert db.execute("SELECT count(*) FROM evolution_hosts").fetchone()[0] == 0
    assert db.execute("SELECT count(*) FROM evolution_release_operations").fetchone()[0] == 0
    assert db.execute("SELECT id FROM auth_principals").fetchall() == [("fixture-control-replay-owner",)]
    assert db.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 20
    db.close()
    release = {}
    for name, value in bundle["files"].items():
        if name == "snapshot.sqlite":
            continue
        contents = base64.b64decode(value)
        assert contents == (WT / name).read_bytes(), name
        release[name] = digest(contents)
    assert len(release) == 22
    assert digest(encoded(release, sort=True)) == bundle["binding"]["release_hash"]
    return {"snapshot_hash": digest(raw), "projection_hash": actual, "release_files": len(release), "original_journal_modes": original_modes, "nonempty_tables": nonempty, "ordinary_object_kinds": kinds}


def semantic(result):
    body = result["body"].copy()
    if result["status"] >= 400:
        body.pop("correlation_id", None)
    assert set(result["headers"]) <= {"Content-Type", "Cache-Control", "ETag", "X-ResearchOS-Principal-ID"}
    return {"status": result["status"], "headers": result["headers"], "body": body}


def replay(prefix, proof):
    suite = load(prefix + "-public-suite.json")
    bundle = load(prefix + "-public-bundle.json")
    binding = suite["inputs"]["binding"]
    assert binding == bundle["binding"] == proof["binding"]
    assert proof["profile"] == "control-business-fixture-v1"
    assert proof["revision"] == suite["inputs"]["revision"] == suite["labels"]["revision"] == "control-public-research-gates-v1"
    assert proof["inputs_hash"] == digest(encoded(suite["inputs"]))
    assert proof["labels_hash"] == digest(encoded(suite["labels"]))
    assert proof["public_suite_hash"] == digest(encoded(suite))
    policy = {"scope": "W16_G02_FIXTURE_ONLY", "profile": "control-business-fixture-v1", "protocol": "researchos-control-replay-v1", "projection": "control-manual-research-projection-v1", "binding": binding, "suite_hash": proof["public_suite_hash"], "min_additional_correct": 1, "mandatory_regressions_allowed": 0, "normalization": "root-error-correlation-id-only", "database_changes_allowed": 0, "timeout_ms": 10000, "promotion_live_qualified": False}
    assert digest(encoded(dict(sorted(policy.items())))) == proof["policy_hash"]
    assert proof["stable_hash"] == proof["candidate_hash"] == "sha256:4276dc5b6c8ac7d0f18026dc6d39140bf20a94fbf1d030f3872e5162a15ba24a"
    assert proof["stable_source_hash"] == proof["candidate_source_hash"] == digest((EVIDENCE / "control-source-files.json").read_bytes())
    scores = {"baseline": [], "candidate": []}
    seen = set()
    process_ids = []
    for case, label, pair in zip(suite["inputs"]["cases"], suite["labels"]["labels"], proof["pairs"], strict=True):
        assert case["id"] == label["id"] and label["required"] and label["database_unchanged"]
        for role in scores:
            invocation = pair[role]
            request = {"binding": binding, "case": case}
            assert invocation["request"] == request
            assert invocation["input_hash"] == digest(encoded(request))
            assert invocation["build_hash"] == proof["stable_hash"]
            assert invocation["source_hash"] == proof["stable_source_hash"]
            receipt, identity = invocation["receipt"], invocation["suspended_identity"]
            assert invocation["raw"].encode() == base64.b64decode(receipt["stdout"])
            assert digest(invocation["raw"].encode()) == invocation["raw_hash"]
            assert receipt["exit_code"] == 0 and not receipt["timed_out"] and receipt["capabilities"] == []
            assert all(receipt[k] for k in ["children_stopped", "streams_drained", "cleanup_complete", "output_copied"])
            for field in ["pid", "process_created_ns", "job", "appcontainer_sid", "profile"]:
                assert identity[field] == receipt[field]
            sid = receipt["appcontainer_sid"]
            assert sid not in seen
            seen.add(sid)
            stage = identity["staging_directory"]
            expected_image = ntpath.join(stage, "input", "control.exe")
            assert invocation["image_path"].casefold() == receipt["executable"].casefold() == expected_image.casefold()
            assert receipt["cwd"].casefold() == ntpath.join(stage, "output").casefold()
            assert receipt["argv"] == ["--fixture-control-replay", ntpath.join(stage, "input", "current-case.json")]
            result = json.loads(invocation["raw"])
            assert result["binding"] == binding and result["case_id"] == case["id"]
            correct = invocation["output_state_hash"] == binding["projection_hash"]
            assert re.fullmatch(r"sha256:[0-9a-f]{64}", invocation["output_database_hash"])
            correct &= all(semantic(a) == semantic(b) for a, b in zip(result["results"], label["results"], strict=True))
            scores[role].append(int(correct))
            process_ids.append({"case": case["id"], "role": role, "pid": receipt["pid"], "created": receipt["process_created_ns"]})
    gain = any(a == 0 and b == 1 for a, b in zip(scores["baseline"], scores["candidate"])) and not any(a == 1 and b == 0 for a, b in zip(scores["baseline"], scores["candidate"])) and all(scores["candidate"])
    return {"name": prefix, "projection": projection(bundle), "scores": scores, "gain": gain, "unique_container_sids": len(seen), "processes": process_ids, "limits": "Output DB bytes and old processes no longer available; stored output state hashes are host observations, not freshly remeasured here."}


def main():
    standalone = replay("TestW16ControlReplayNative", load("public-control-native-proof.json"))
    flow = load("control-business-no-gain.json")
    aggregate = replay("TestW16ControlBusinessNoGain", flow["execution"]["control_proof"])
    keys = ["scope", "candidate_artifact_ref", "stable_artifact_ref", "isolated_workspace_id", "baseline_suite_ref", "baseline_policy_hash", "changed_paths_manifest_ref", "experiment_id", "migration_plan_ref", "rollback_plan_ref", "independent_supervisor_id"]
    plan = {k: flow["candidate"][k] for k in keys}
    assert digest(encoded(plan, sort=True)) == flow["execution"]["plan_hash"]
    assert flow["candidate"]["status"] == "REJECTED" and flow["slot_state"] == "STABLE"
    assert flow["active_hash"] == flow["execution"]["baseline_hash"]
    assert flow["release_operation_count"] == flow["switch_effect_count"] == 0
    assert flow["acceptance"]["verdict"] == "PASS" and flow["execution"]["improved"] is False
    result = {"verdict": "PASS_PUBLIC_RECOMPUTATION", "sqlite_version": sqlite3.sqlite_version, "datasets": [standalone, aggregate], "no_gain_candidate_rejected": True, "native_replays_run": 0, "private_payloads_read": 0, "limits": ["Original authority snapshot/generation not retained for independent recomputation.", "Private score awaits separate controlled summary-only recomputation.", "No fresh authority or OS process qualification is implied."]}
    (OUT / "public-recomputation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "scores": [r["scores"] for r in result["datasets"]], "native_replays_run": 0, "private_payloads_read": 0}))


if __name__ == "__main__":
    main()
