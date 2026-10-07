import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
CANDIDATE = "f565599af3679fef6d5233fe27d16b8c92a61db2"
SOURCES = {"apps/cli/cli_stream.go", "apps/cli/cli_continuation.go", "apps/cli/cli_read_interrupt_test.go", "apps/cli/cli_v2.go"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def run(name, argv):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True)
    for suffix, raw in [("stdout.raw", proc.stdout), ("stderr.raw", proc.stderr)]:
        with (OUT / (name + "." + suffix)).open("xb") as stream:
            stream.write(raw)
    save(name + ".invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": start, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": proc.returncode, "stdout_sha256": sha(proc.stdout), "stderr_sha256": sha(proc.stderr)})
    assert proc.returncode == 0, (name, proc.returncode)
    return proc.stdout


def snapshot(names):
    return {name: {"sha256": sha((ROOT / name).read_bytes()), "bytes": (ROOT / name).stat().st_size} if (ROOT / name).is_file() else "MISSING" for name in names}


archive = json.loads((ROOT / (BASE + "integration_codex/source-evidence-archive-r272/completed.json")).read_bytes())
head_before = run("head-before", ["git", "rev-parse", "HEAD"]).decode().strip()
assert head_before == archive["head"] == "154c7c2cee34b643b9ee4aa5a0beb4d99ee126b8"
assert not run("index-before", ["git", "diff", "--cached", "--name-only", "-z"])
review_path = BASE + "cli_read_interrupt_source_review_codex/c5dc6318-b068-4630-81ee-21ae287b842d/source_review.json"
assert sha((ROOT / review_path).read_bytes()) == "ecfb699818af3fae4aaf404263b0752382984f2f3dbbc3f21e3b3f2d91eaf0f9"
review = json.loads((ROOT / review_path).read_bytes())
assert review["candidate_commit"] == CANDIDATE and review["decision"] == "SOURCE_READY_L02_EXACT4_CURRENT_STREAM_COMPOSITION"
canonical = {name: (ROOT / ("execution/v2.4/" + name)).read_bytes() for name in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]}
assert json.loads(canonical["checkpoint.json"])["revision"] == 272 and json.loads(canonical["path_ownership.json"])["revision"] == 100
assert len(json.loads(canonical["checkpoint.json"])["failure_counters"]) == 219
sub = json.loads(canonical["path_ownership.json"])["card_path_bindings"]["W05-99"]["subtasks"]["cli_read_interruption"]
assert set(sub["paths"]) == SOURCES and sub["independent_source_review_ref"]["path"] == review_path
deleted = {line for line in run("status-before", ["git", "status", "--porcelain=v1", "--untracked-files=no"]).decode().splitlines() if line.startswith(" D ")}
assert len(deleted) == 11
tracked = {name for name in run("tracked-source", ["git", "ls-files", "-z", "--", "internal", "adapters", "apps", "tests", "migrations", "contracts", "bootstrap", "go.mod", "go.sum"]).decode().split("\0") if name}
source_before = snapshot(sorted(tracked | SOURCES))
save("source_before.json", source_before)
fields = run("candidate-raw-diff", ["git", "diff-tree", "--no-commit-id", "--raw", "--no-abbrev", "-r", "-z", CANDIDATE]).split(b"\0")
entries = []
position = 0
while position < len(fields) and fields[position]:
    metadata = fields[position].decode().split()
    name = fields[position + 1].decode()
    position += 2
    assert metadata[4] in ["A", "M"] and (name in SOURCES or name.startswith(BASE))
    entries.append({"path": name, "blob_oid": metadata[3]})
assert len(entries) == 178 and {item["path"] for item in entries if not item["path"].startswith(BASE)} == SOURCES
for item in entries:
    if item["path"] in SOURCES:
        continue
    raw = (ROOT / item["path"]).read_bytes()
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == item["blob_oid"]
save("candidate_blobs.json", entries)
run("cherry", ["git", "cherry-pick", CANDIDATE])
head = run("head-after", ["git", "rev-parse", "HEAD"]).decode().strip()
actual_paths = {name for name in run("commit-paths", ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head]).decode().split("\0") if name}
assert actual_paths == SOURCES
for item in entries:
    raw = (ROOT / item["path"]).read_bytes()
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == item["blob_oid"]
after = snapshot(sorted(tracked | SOURCES))
save("source_after.json", after)
changed = sorted(name for name in after if source_before[name] != after[name])
assert set(changed) == SOURCES
assert all((ROOT / ("execution/v2.4/" + name)).read_bytes() == raw for name,raw in canonical.items())
assert deleted == {line for line in run("status-after", ["git", "status", "--porcelain=v1", "--untracked-files=no"]).decode().splitlines() if line.startswith(" D ")}
bundle = ROOT / ".local/w0599-main-stream-integration-r268/mu-worker.mjs"
assert sha(bundle.read_bytes()) == "2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441"
result = {"schema": "researchos.root.reviewed-main-cli-exact4-integration.v1", "actor": "codex:/root", "actual_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": 0, "starting_head": head_before, "head": head, "original_candidate": CANDIDATE, "source_paths": changed, "source_inventory_count": len(after), "frozen_blob_entries_verified": 178, "archived_receipts_already_matching": 174, "main_commit_changed_paths": len(actual_paths), "canonical_unchanged": True, "old11_deletions_preserved": True, "bundle_sha256": sha(bundle.read_bytes()), "status": "INDEPENDENT_SOURCE_READY_EXACT4_INTEGRATED_MAIN_CURRENT_TEST_PENDING", "formal_increment": 0}
save("result.json", result)
print(json.dumps(result, ensure_ascii=False))
