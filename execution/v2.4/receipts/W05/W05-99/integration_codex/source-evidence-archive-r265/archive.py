"""Archive a fixed public evidence whitelist; do not integrate candidate source."""
import datetime
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(r"D:\作品集\ResearchOS\research-os")
OUT = pathlib.Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def run(name, argv):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True)
    (OUT / (name + ".stdout.raw")).write_bytes(result.stdout)
    (OUT / (name + ".stderr.raw")).write_bytes(result.stderr)
    record = {"argv": argv, "cwd": str(ROOT), "started_at": start, "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": result.returncode, "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()}
    (OUT / (name + ".invocation.json")).write_bytes(encode(record))
    assert result.returncode == 0, (name, result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def main():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip() == "6e9ac45bff1c76fac37f0462a051412f53ab11d8"
    assert not subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT)
    cp = json.loads((ROOT / "execution/v2.4/checkpoint.json").read_bytes())
    own = json.loads((ROOT / "execution/v2.4/path_ownership.json").read_bytes())
    assert cp["revision"] == 265 and own["revision"] == 93
    selected = {
        ROOT / "execution/v2.4/checkpoint.json",
        ROOT / "execution/v2.4/path_ownership.json",
        pathlib.Path(__file__).resolve(),
    }
    prefixes = [
        "integration_codex/resume-r264-resource",
        "integration_codex/model-stream-quarantine-repair-r265",
        "provider_resource_intake_review_codex/948c0201-2b62-42e7-a1b0-b12a6acfa473",
        "provider_binding_readonly_codex/cfcce581-d452-48c4-8a3e-274044516a28",
        "streaming_combined_source_review_codex/f67e12e4-175f-4fd9-9442-8bdf1c0ecf5e",
    ]
    for prefix in prefixes:
        parent = ROOT / (BASE + prefix)
        assert parent.is_dir(), str(parent)
        for path in parent.rglob("*"):
            if path.is_file() and not any(part in [".git", "__pycache__"] for part in path.relative_to(parent).parts) and path.suffix != ".pyc":
                selected.add(path)
    previous = ROOT / (BASE + "integration_codex/source-evidence-archive-r263")
    for name in ["stage.invocation.json", "stage.stdout.raw", "stage.stderr.raw", "commit.invocation.json", "commit.stdout.raw", "commit.stderr.raw", "completed.json"]:
        selected.add(previous / name)
    files = []
    for path in sorted(selected):
        assert path.is_file()
        rel = path.relative_to(ROOT).as_posix()
        assert rel.startswith("execution/v2.4/")
        assert not rel.endswith(".zip")
        raw = path.read_bytes()
        files.append({"path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    manifest = {"schema": "researchos.root.public-source-evidence-archive.v1", "actual_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actor": "codex:/root", "source_integration": False, "formal_increment": 0, "checkpoint": 265, "ownership": 93, "failure_origins": 170, "files": files}
    (OUT / "manifest.json").write_bytes(encode(manifest))
    names = [x["path"] for x in files] + [(OUT / "manifest.json").relative_to(ROOT).as_posix()]
    pathspec = OUT / "pathspec.nul"
    pathspec.write_bytes(b"\0".join(x.encode("utf-8") for x in names) + b"\0")
    run("stage", ["git", "--literal-pathspecs", "add", "--pathspec-from-file=" + str(pathspec), "--pathspec-file-nul"])
    pathspec.unlink()
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    staged = set(x for x in staged if x)
    assert staged == set(names), (len(staged), len(names))
    for file in files:
        raw = subprocess.check_output(["git", "show", ":" + file["path"]], cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest() == file["sha256"], file["path"]
    run("commit", ["git", "commit", "-m", "chore(execution): preserve T08 review failure and bounded repair scope"])
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    changed = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head], cwd=ROOT).decode("utf-8").split("\0")
    assert set(x for x in changed if x) == staged
    result = {"actual_exit": 0, "head": head, "actual_changed_paths": len(staged), "source_integration": False, "formal_increment": 0, "old_zip_deletions_not_staged": True}
    (OUT / "completed.json").write_bytes(encode(result))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
