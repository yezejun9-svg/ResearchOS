"""Archive sealed public evidence only; leave source and old deletions untouched."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
COMMITS = ["fef0ee2d56351e74ceed11b0b37d3f87e9c83494", "125ea34ca0878f18c4dce47f9259ab5e9e77c2eb", "c82f73cc6699b564f1357472e2859b90cafe6b0a"]


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write(enc(value))


def run(name, argv):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True)
    for suffix, raw in (("stdout.raw", proc.stdout), ("stderr.raw", proc.stderr)):
        with (OUT / (name + "." + suffix)).open("xb") as stream:
            stream.write(raw)
    save(name + ".invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": started,
         "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": proc.returncode,
         "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest()})
    assert proc.returncode == 0, (name, proc.returncode)
    return proc.stdout


def main():
    assert run("head-before", ["git", "rev-parse", "HEAD"]).decode().strip() == "26e1043751c989d4e6016a76f113e343c9e38382"
    assert not run("index-before", ["git", "diff", "--cached", "--name-only", "-z"])
    cp = json.loads((ROOT / "execution/v2.4/checkpoint.json").read_bytes())
    own = json.loads((ROOT / "execution/v2.4/path_ownership.json").read_bytes())
    assert cp["revision"] == 281 and own["revision"] == 109 and len(cp["failure_counters"]) == 237
    selected = {ROOT / "execution/v2.4/checkpoint.json", ROOT / "execution/v2.4/path_ownership.json", Path(__file__).resolve(), OUT / "driver.py"}
    prefixes = ['integration_codex/provider-zero-model-recovery-r275', 'integration_codex/configuration-test-and-p12-resource-r276', 'integration_codex/configuration-independent-review-r277', 'integration_codex/configuration-review-identity-r278', 'integration_codex/provider-inventory-causal-repair-r279', 'integration_codex/provider-inventory-scope-clarification-r280', 'integration_codex/configuration-development-recovery-r281', 'integration_codex/handoff-resume-r278', 'provider_inventory_repair_scope_readonly_codex/939895be3999443788f92f0012bfbd2b', 'provider_binding_zero_model_adjudication_codex/d7f95235-03e1-464f-b3b0-374ca7394fda', 'host_configuration_handler_scope_readonly_codex/7e34df584e1b45a1b68f06ce62fcdb95']
    for prefix in prefixes:
        parent = ROOT / (BASE + prefix)
        assert parent.is_dir(), str(parent)
        for path in parent.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                selected.add(path)
    previous = ROOT / (BASE + "integration_codex/source-evidence-archive-r274")
    for name in ["stage.invocation.json", "stage.stdout.raw", "stage.stderr.raw", "commit.invocation.json", "commit.stdout.raw", "commit.stderr.raw", "completed.json"]:
        selected.add(previous / name)
    # Any already-copied immutable candidate receipts must be archived before cherry-pick.
    for index, commit in enumerate(COMMITS):
        names = run(f"candidate-{index}-paths", ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit]).decode().split("\0")
        for name in names:
            if not name.startswith(BASE):
                continue
            path = ROOT / name
            if path.is_file():
                expected = run(f"candidate-{index}-existing-{hashlib.sha256(name.encode()).hexdigest()[:16]}", ["git", "show", commit + ":" + name])
                assert path.read_bytes() == expected, name
                selected.add(path)
    # Restrict staging to public files whose actual bytes differ from current index.
    index_raw = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT)
    index = {}
    for row in index_raw.split(b"\0"):
        if row:
            meta, name = row.split(b"\t", 1)
            mode, oid, stage = meta.split()
            assert stage == b"0"
            index[name.decode()] = oid.decode()
    files = []
    for path in sorted(selected):
        assert path.is_file()
        relative = path.relative_to(ROOT).as_posix()
        assert relative.startswith("execution/v2.4/") and path.suffix != ".zip"
        raw = path.read_bytes()
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if index.get(relative) == oid:
            continue
        files.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    save("manifest.json", {"schema": "researchos.root.public-source-evidence-archive.v1", "actor": "codex:/root",
         "checkpoint": 281, "ownership": 109, "failure_origins": 237, "files": files, "source_integration": False, "formal_increment": 0})
    names = [x["path"] for x in files] + [(OUT / "manifest.json").relative_to(ROOT).as_posix()]
    pathspec = OUT / "pathspec.nul"
    pathspec.write_bytes(b"\0".join(x.encode() for x in names) + b"\0")
    run("stage", ["git", "--literal-pathspecs", "add", "--pathspec-from-file=" + str(pathspec), "--pathspec-file-nul"])
    pathspec.unlink()
    staged = set(x for x in subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT).decode().split("\0") if x)
    assert staged == set(names), (len(staged), len(names))
    for file in files:
        raw = subprocess.check_output(["git", "show", ":" + file["path"]], cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest() == file["sha256"], file["path"]
    run("commit", ["git", "commit", "-m", "chore(execution): preserve configuration review and bounded model validator repair records"])
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    changed = set(x for x in subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head], cwd=ROOT).decode().split("\0") if x)
    assert changed == staged
    result = {"actual_exit": 0, "head": head, "actual_changed_paths": len(changed), "source_integration": False, "formal_increment": 0, "old_deletions_not_staged": True}
    save("completed.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
