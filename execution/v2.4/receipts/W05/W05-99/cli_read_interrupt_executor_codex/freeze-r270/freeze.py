import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
WT = ROOT / ".local/worktrees/codex-w0599-cli-read-interrupt"
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
SOURCE = ["apps/cli/cli_stream.go", "apps/cli/cli_continuation.go", "apps/cli/cli_read_interrupt_test.go", "apps/cli/cli_v2.go"]
HEAD = "d799ee058f59dc778d288566e25a72ae9f4f78a3"


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write(enc(value))


def ref(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def run(name, argv):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=WT, capture_output=True)
    for suffix, raw in [("stdout.raw", proc.stdout), ("stderr.raw", proc.stderr)]:
        with (OUT / (name + "." + suffix)).open("xb") as stream:
            stream.write(raw)
    save(name + ".invocation.json", {"argv": argv, "cwd": str(WT), "started_at": start, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": proc.returncode, "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest()})
    assert proc.returncode == 0, name
    return proc.stdout


assert run("head-before", ["git", "rev-parse", "HEAD"]).decode().strip() == HEAD
assert not run("index-before", ["git", "diff", "--cached", "--name-only", "-z"])
scope_path = ROOT / (BASE + "integration_codex/cli-read-causal-scope-r267/scope_registration.json")
assert ref(scope_path)["sha256"] == "b950974027f665aaf543029dd4dffbf5cbee23fb5b38a3e819a35dc508a333dc"
full_dir = ROOT / (BASE + "cli_read_interrupt_executor_codex/implementation-20261006-r266/closure-e2c362a78f104db8a09b5712cb314f3f")
full = json.loads((full_dir / "result.json").read_bytes())
assert full["actual_exit"] == 0 and not full["source_drift"] and full["input_count"] == 39061
assert full["assertion_counts"] == {"pass": 234, "fail": 0, "skip": 0}
before = json.loads((full_dir / "source_before.json").read_bytes())
assert before == json.loads((full_dir / "source_after.json").read_bytes())
for key, digest in before.items():
    if key.startswith("repo:"):
        path = WT / key.removeprefix("repo:")
    elif key.startswith("main:"):
        path = ROOT / key.removeprefix("main:")
    else:
        assert key.startswith("absolute:")
        path = Path(key.removeprefix("absolute:"))
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest, key
canonical = {name: hashlib.sha256((ROOT / ("execution/v2.4/" + name)).read_bytes()).hexdigest() for name in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]}
sources = []
for name in SOURCE:
    raw = (WT / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == before["repo:" + name]
    sources.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "git_blob_oid": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()})
files = []
for prefix in ["cli_read_interrupt_executor_codex/implementation-20261006-r266", "cli_read_interrupt_executor_codex/composition-rebase-r269"]:
    folder = ROOT / (BASE + prefix)
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(ROOT)
        raw = path.read_bytes()
        target = WT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.is_file() and target.read_bytes() == raw, str(relative)
        else:
            with target.open("xb") as stream:
                stream.write(raw)
        files.append(ref(path))
manifest = {"schema": "researchos.root.cli-read-exact4-frozen-source-manifest.v1", "actor": "codex:/root", "base_head": HEAD, "main_composition_head": "396287cc5427eb125aaedb8a2b7fadf63e6b9322", "scope_ref": ref(scope_path), "sources": sources, "public_receipts": files, "actual_current_full_result_ref": ref(full_dir / "result.json"), "actual_focused_result_ref": ref(ROOT / (BASE + "cli_read_interrupt_executor_codex/implementation-20261006-r266/closure-7b651b5cfbb34df2ad7145c4ee5ae273/result.json")), "source_inputs": 39061, "measurement_mode": "FIXTURE_NOT_LIVE_NOT_FORMAL", "source_acceptance": "PENDING_INDEPENDENT_REVIEW", "formal_increment": 0}
save("manifest.json", manifest)
for name in ["freeze.py", "driver.py", "manifest.json"]:
    original = OUT / name
    target = WT / original.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(original.read_bytes())
index = {}
for row in run("git-index", ["git", "ls-files", "--stage", "-z"]).split(b"\0"):
    if row:
        metadata, name = row.split(b"\t", 1)
        mode, oid, stage = metadata.split()
        assert stage == b"0"
        index[name.decode()] = oid.decode()
names = SOURCE + [item["path"] for item in files] + [(OUT / name).relative_to(ROOT).as_posix() for name in ["freeze.py", "driver.py", "manifest.json"]]
changed = []
for name in names:
    raw = (WT / name).read_bytes()
    oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if index.get(name) != oid:
        changed.append(name)
assert set(SOURCE).issubset(changed) and len(changed) == len(set(changed))
pathspec = OUT / "pathspec.nul"
with pathspec.open("xb") as stream:
    stream.write(b"\0".join(name.encode() for name in changed) + b"\0")
run("stage", ["git", "--literal-pathspecs", "add", "--pathspec-from-file=" + str(pathspec), "--pathspec-file-nul"])
pathspec.unlink()
staged = set(name for name in subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=WT).decode().split("\0") if name)
assert staged == set(changed)
staged_index = {}
for row in subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=WT).split(b"\0"):
    if row:
        metadata, name = row.split(b"\t", 1)
        staged_index[name.decode()] = metadata.split()[1].decode()
for name in changed:
    raw = (WT / name).read_bytes()
    assert staged_index[name] == hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(), name
run("commit", ["git", "commit", "-m", "fix(cli): preserve transport failure causes during read-only interruption"])
head = run("head-after", ["git", "rev-parse", "HEAD"]).decode().strip()
actual = set(name for name in run("commit-paths", ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head]).decode().split("\0") if name)
assert actual == staged
assert {name for name in actual if not name.startswith(BASE)} == set(SOURCE)
assert canonical == {name: hashlib.sha256((ROOT / ("execution/v2.4/" + name)).read_bytes()).hexdigest() for name in canonical}
handoff = {"schema": "researchos.root.cli-read-exact4-frozen-source-handoff.v1", "actor": "codex:/root", "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "candidate_commit": head, "base_head": HEAD, "worktree": str(WT), "source_paths": SOURCE, "actual_changed_paths": len(actual), "manifest_ref": ref(OUT / "manifest.json"), "full_result_ref": manifest["actual_current_full_result_ref"], "focused_result_ref": manifest["actual_focused_result_ref"], "root_canonical_unchanged": True, "old_deletions_not_staged": True, "source_acceptance": "PENDING_INDEPENDENT_REVIEW", "verification_required": ["Independent original oversize late-signal probe replay", "Actual cancellation cause and noncancel transport/body errors retained", "Accepted protocol fault plus observed signal before finish", "Accepted success plus observed signal before finish", "Real Windows CTRL_BREAK on actual compiled CLI", "Full current-composition CLI closure", "No active mutation/control/authority drift"], "formal_increment": 0}
save("handoff.json", handoff)
print(json.dumps(handoff, ensure_ascii=False))
