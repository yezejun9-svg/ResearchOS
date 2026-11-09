import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
SCOPE_PATH = BASE + "integration_codex/configuration-main-scope-r282/scope_registration.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    with (OUT / name).open("xb") as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def run(name, argv):
    at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    p = subprocess.run(argv, cwd=ROOT, capture_output=True)
    for suffix, raw in [("stdout.raw", p.stdout), ("stderr.raw", p.stderr)]:
        with (OUT / (name + "." + suffix)).open("xb") as f:
            f.write(raw)
    save(name + ".invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": at, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": p.returncode, "stdout_sha256": sha(p.stdout), "stderr_sha256": sha(p.stderr)})
    assert p.returncode == 0, (name, p.returncode)
    return p.stdout


def snapshot(names):
    return {n: {"sha256": sha((ROOT / n).read_bytes()), "bytes": (ROOT / n).stat().st_size} if (ROOT / n).is_file() else "MISSING" for n in names}


scope_raw = (ROOT / SCOPE_PATH).read_bytes()
assert sha(scope_raw) == "2a0e849c2745a5515d1ac338c78a12435cb1473c0063536a22d371da70752a41"
scope = json.loads(scope_raw)
assert run("head-before", ["git", "rev-parse", "HEAD"]).decode().strip() == scope["main_base"] == "24072356acfd4c314c048b30a37334f9aef055d5"
assert not run("index-before", ["git", "diff", "--cached", "--name-only", "-z"])
canonical = {name: (ROOT / ("execution/v2.4/" + name)).read_bytes() for name in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]}
assert json.loads(canonical["checkpoint.json"])["revision"] == 282
assert json.loads(canonical["path_ownership.json"])["revision"] == 110
assert len(json.loads(canonical["checkpoint.json"])["failure_counters"]) == 238
source_rows = scope["exact_source16"]
sources = {r["path"] for r in source_rows}
assert len(sources) == 16
review_ref = scope["independent_source_review_ref"]
assert sha((ROOT / review_ref["path"]).read_bytes()) == review_ref["sha256"]
status_before = run("status-before", ["git", "status", "--porcelain=v1", "--untracked-files=no"]).decode().splitlines()
deleted = {line for line in status_before if line.startswith(" D ")}
assert len(deleted) == 11
tracked = {n for n in run("tracked-source", ["git", "ls-files", "-z", "--", "internal", "adapters", "apps", "tests", "migrations", "contracts", "bootstrap", "go.mod", "go.sum"]).decode().split("\0") if n}
before = snapshot(sorted(tracked | sources))
save("source_before.json", before)
entries = {}
commit_rows = []
for i, commit in enumerate(scope["candidate_commits_in_order"]):
    fields = run(f"candidate-{i}-diff", ["git", "diff-tree", "--no-commit-id", "--raw", "--no-abbrev", "-r", "-z", commit]).split(b"\0")
    rows = []
    pos = 0
    while pos < len(fields) and fields[pos]:
        meta, path = fields[pos].decode().split(), fields[pos + 1].decode()
        pos += 2
        assert meta[4] in ["A", "M"] and (path in sources or path.startswith(BASE)), path
        row = {"path": path, "blob_oid": meta[3], "commit": commit}
        rows.append(row)
        entries[path] = row
        if path not in sources and (ROOT / path).exists():
            raw = (ROOT / path).read_bytes()
            assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == meta[3], path
    commit_rows.append({"commit": commit, "entries": len(rows), "source_paths": [r["path"] for r in rows if r["path"] in sources]})
assert len(entries) == 1773 and {p for p in entries if not p.startswith(BASE)} == sources
save("candidate_blobs.json", {"commits": commit_rows, "unique_entries": list(entries.values())})
main_commits = []
for i, commit in enumerate(scope["candidate_commits_in_order"]):
    run(f"cherry-{i}", ["git", "cherry-pick", commit])
    main_commits.append(run(f"head-after-{i}", ["git", "rev-parse", "HEAD"]).decode().strip())
for path, entry in entries.items():
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == entry["blob_oid"], path
for row in source_rows:
    assert sha((ROOT / row["path"]).read_bytes()) == row["sha256"], row["path"]
after = snapshot(sorted(tracked | sources))
save("source_after.json", after)
changed = sorted(n for n in after if before[n] != after[n])
assert set(changed) == sources
assert all((ROOT / ("execution/v2.4/" + name)).read_bytes() == raw for name, raw in canonical.items())
assert deleted == {line for line in run("status-after", ["git", "status", "--porcelain=v1", "--untracked-files=no"]).decode().splitlines() if line.startswith(" D ")}
bundle = ROOT / ".local/w0599-main-stream-integration-r268/mu-worker.mjs"
assert sha(bundle.read_bytes()) == "2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441"
result = {"schema": "researchos.root.reviewed-configuration-main-source-integration.v1", "actor": "codex:/root", "actual_exit": 0, "starting_head": scope["main_base"], "head": main_commits[-1], "main_commits": main_commits, "original_candidate_commits": scope["candidate_commits_in_order"], "source_paths": changed, "source_inventory_count": len(after), "unique_candidate_blobs_verified": len(entries), "candidate_source_blobs": len(sources), "candidate_receipt_blobs": len(entries) - len(sources), "canonical_unchanged": True, "old11_deletions_preserved": True, "bundle_sha256": sha(bundle.read_bytes()), "status": "EXACT16_REVIEWED_SOURCE_INTEGRATED_MAIN_CURRENT_COMPOSITION_TEST_PENDING", "independent_source_review_ref": review_ref, "formal_increment": 0}
save("result.json", result)
print(json.dumps(result, ensure_ascii=False))
