"""Integrate only independently reviewed frozen source commits and rebuild Mu."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import traceback

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
COMMITS = ["6eb611b11364ba25a9560ba54c1b54f3a549eb32", "0bbcef5347ed9bd3a1174c7d3df9dfd8a270e837", "890d4c164bffad73e562ceacfdc216820d0313fd", "c571781e9703bc7a96fa63629e0cc3bee7f3deec"]
NODE = Path("C:/nvm4w/nodejs/node.exe")
BUNDLE = ROOT / ".local/w0599-main-stream-integration-r268/mu-worker.mjs"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    with (OUT / name).open("xb") as stream:
        stream.write(raw)
    return {"path": (OUT / name).relative_to(ROOT).as_posix(), "sha256": sha(raw)}


def run(name, argv):
    started = stamp()
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True)
    for suffix, raw in (("stdout.raw", proc.stdout), ("stderr.raw", proc.stderr)):
        with (OUT / (name + "." + suffix)).open("xb") as stream:
            stream.write(raw)
    save(name + ".invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": started, "ended_at": stamp(),
         "actual_exit": proc.returncode, "stdout_sha256": sha(proc.stdout), "stderr_sha256": sha(proc.stderr)})
    assert proc.returncode == 0, (name, proc.returncode, proc.stderr.decode("utf8", errors="replace"))
    return proc.stdout


def blobs(commit, index):
    raw = run(f"candidate-{index}-raw-diff", ["git", "diff-tree", "--no-commit-id", "--raw", "--no-abbrev", "-r", "-z", commit])
    fields = raw.split(b"\0")
    output = []
    position = 0
    while position < len(fields) and fields[position]:
        metadata = fields[position].decode().split()
        path = fields[position + 1].decode()
        position += 2
        assert metadata[4] in ["A", "M"], metadata
        output.append({"path": path, "blob_oid": metadata[3]})
    return output


def source_snapshot(names):
    return {name: {"sha256": sha((ROOT / name).read_bytes()), "bytes": (ROOT / name).stat().st_size} if (ROOT / name).is_file() else "MISSING" for name in names}


def build_snapshot():
    paths = {ROOT / name for name in ["adapters/runtime/mu/build.mjs", "adapters/runtime/mu/worker.mjs", "third_party/mu.MANIFEST.json", "third_party/VENDORED_FROM.md", "third_party/mu/package.json", "third_party/mu/package-lock.json", "execution/v2.4/component_lock.json"]}
    manifest = json.loads((ROOT / "third_party/mu.MANIFEST.json").read_bytes())
    assert manifest["files"] == 5083 and len(manifest["entries"]) == 5083
    for name, expected in manifest["entries"].items():
        path = ROOT / name
        raw = path.read_bytes()
        assert sha(raw) == expected["sha256"] and len(raw) == expected["size"], name
        paths.add(path)
    paths.update(p for p in (ROOT / "third_party/mu/node_modules").rglob("*") if p.is_file() and ".git" not in p.parts)
    paths.update(p for p in (ROOT / "third_party/mu/packages").rglob("*") if p.is_file() and ".git" not in p.parts)
    paths.add(NODE)
    result = {}
    for path in sorted(paths):
        name = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else "absolute:" + path.as_posix()
        result[name] = {"sha256": sha(path.read_bytes()), "bytes": path.stat().st_size}
    return result


def main():
    archive = json.loads((ROOT / (BASE + "integration_codex/source-evidence-archive-r268/completed.json")).read_bytes())
    starting_head = run("head-before", ["git", "rev-parse", "HEAD"]).decode().strip()
    assert starting_head == archive["head"] == "4bed09af79996b07857610cefdfd65be6775aa70"
    assert not run("index-before", ["git", "diff", "--cached", "--name-only", "-z"])
    metadata_names = ["execution/v2.4/checkpoint.json", "execution/v2.4/path_ownership.json", "execution/v2.4/step_state.json", "execution/v2.4/commands.json"]
    canonical_before = {name: (ROOT / name).read_bytes() for name in metadata_names}
    own = json.loads(canonical_before[metadata_names[1]])
    subs = own["card_path_bindings"]["W05-99"]["subtasks"]
    allowed = set(subs["real_model_streaming"]["paths"] + subs["real_model_streaming_worker"]["paths"])
    assert own["revision"] == 96 and json.loads(canonical_before[metadata_names[0]])["revision"] == 268
    assert subs["real_model_streaming"]["source_composition_commits"] == COMMITS
    review_name = BASE + "streaming_signed_zero_source_review_codex/4bb6828c-89ea-4a19-b0ed-e3b07da94b8a/source_review.json"
    assert sha((ROOT / review_name).read_bytes()) == "9f0035ba65341adacc98d00e6da220c239769a83c26475e262b2816868ee0d26"
    resource_review = BASE + "vendor_resource_restore_independent_review_codex/cc65c5e5-9b17-4c0d-9add-e560b1850a09/review.json"
    assert sha((ROOT / resource_review).read_bytes()) == "5e83c9aa66baab0e5a91b4feb40429e5d46cc031c7fa61433478699d30682ef9"
    deleted_before = set(line for line in run("status-before", ["git", "status", "--short", "--untracked-files=no"]).decode().splitlines() if line.startswith(" D "))
    assert len(deleted_before) == 11
    all_source_names = [x for x in run("tracked-source-list", ["git", "ls-files", "-z", "--", "adapters", "apps", "internal", "migrations", "tools", "tests", "contracts", "bootstrap", "go.mod", "go.sum"]).decode().split("\0") if x]
    before_source = source_snapshot(all_source_names)
    save("main-source.before.json", before_source)
    expected = {}
    candidates = []
    for index, commit in enumerate(COMMITS):
        entries = blobs(commit, index)
        for entry in entries:
            name = entry["path"]
            assert name.startswith(BASE) or name in allowed, name
            expected[name] = entry["blob_oid"]
        candidates.append({"commit": commit, "entries": entries})
    save("frozen-candidate-blobs.json", candidates)
    actual_commits = []
    for index, commit in enumerate(COMMITS):
        run(f"cherry-{index}", ["git", "cherry-pick", commit])
        head = run(f"head-{index}", ["git", "rev-parse", "HEAD"]).decode().strip()
        actual_commits.append({"original_commit": commit, "main_commit": head})
        assert all((ROOT / name).read_bytes() == raw for name, raw in canonical_before.items())
    mismatches = []
    for name, oid in sorted(expected.items()):
        raw = (ROOT / name).read_bytes()
        actual_oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual_oid != oid:
            mismatches.append({"path": name, "expected_oid": oid, "actual_oid": actual_oid})
    save("integrated-blob-audit.json", {"entries": len(expected), "mismatches": mismatches})
    assert not mismatches, mismatches
    after_source = source_snapshot(sorted(set(all_source_names) | allowed))
    save("main-source.after.json", after_source)
    changed_sources = sorted(name for name in after_source if before_source.get(name, "MISSING") != after_source[name])
    assert set(changed_sources) <= allowed and len(changed_sources) == 20, changed_sources
    expected_leaves = {
      "adapters/runtime/mu/worker.mjs": "0d50cea351f325f28ca5ee377eac36833768a28be42cf48ec0e50834c0ff6517",
      "adapters/runtime/mu/worker-stream.test.mjs": "9a503dee2fa61e182d93bec5498aae02f1f51560263a0fa671bcf0b94cdc6b70",
      "internal/domain/runtime_model_stream.go": "9454e41c1cf43b471cf4048e6350df1c1a36c7b8a7cc17403951116b08b1c1c8",
      "internal/domain/runtime_model_stream_test.go": "85d54d0067d1d67853ac5ac9d8be6f6982d74e34bb623ead454e8dd816911b3e",
      "apps/cli/cli_model_stream_integration_windows_test.go": "5b555b26c3c79d0cdf6c47af7a37a3d5e562166eb3c76e1e07ba5d8018e2f585"}
    assert all(after_source[name]["sha256"] == expected_sha for name, expected_sha in expected_leaves.items())
    assert not BUNDLE.exists() and not BUNDLE.with_name(BUNDLE.name + ".build.json").exists()
    assert sha(NODE.read_bytes()) == "5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6"
    build_before = build_snapshot()
    build_before_ref = save("build-inputs.before.json", build_before)
    build_raw = run("build", [str(NODE), str(ROOT / "adapters/runtime/mu/build.mjs"), str(BUNDLE)])
    metadata = json.loads(build_raw)
    build_after = build_snapshot()
    build_after_ref = save("build-inputs.after.json", build_after)
    assert build_before == build_after
    assert metadata["vendored_files_verified"] == 5083 and metadata["source_sha256"] == expected_leaves["adapters/runtime/mu/worker.mjs"]
    assert metadata["bundle_sha256"] == sha(BUNDLE.read_bytes())
    with (OUT / "build.metadata.original.json").open("xb") as stream:
        stream.write(BUNDLE.with_name(BUNDLE.name + ".build.json").read_bytes())
    assert all((ROOT / name).read_bytes() == raw for name, raw in canonical_before.items())
    deleted_after = set(line for line in run("status-after", ["git", "status", "--short", "--untracked-files=no"]).decode().splitlines() if line.startswith(" D "))
    assert deleted_before == deleted_after
    result = {"schema": "researchos.root.reviewed-main-stream-source-integration.v1", "actor": "codex:/root", "actual_at": stamp(), "actual_exit": 0,
              "status": "REVIEWED_EXACT20_SOURCE_INTEGRATED_ACTUAL_VENDOR_VERIFIED_BUILD_TEST_COMPOSITION_PENDING",
              "starting_head": starting_head, "head": actual_commits[-1]["main_commit"], "commits": actual_commits,
              "frozen_blob_entries_verified": len(expected), "changed_source_paths": changed_sources, "builder": metadata,
              "build_input_count": len(build_before), "build_source_drift": False, "build_before_ref": build_before_ref, "build_after_ref": build_after_ref,
              "prior_stream_bundle_sha256": "1d32a76d55bfa47083736ef63bfef67642fa6ae8d3255deb535fc8e77d8c6445",
              "current_bundle_equals_prior_stream_bundle": metadata["bundle_sha256"] == "1d32a76d55bfa47083736ef63bfef67642fa6ae8d3255deb535fc8e77d8c6445",
              "old_deletions_preserved": True, "canonical_state_registry_unchanged": True, "runtime_qualification": False, "formal_increment": 0}
    result_ref = save("result.json", result)
    print(json.dumps({"result_ref": result_ref, "head": result["head"], "changed_source_paths": len(changed_sources), "build": metadata, "status": result["status"]}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        save("failure.json", {"actual_at": stamp(), "traceback": traceback.format_exc(), "automatic_retry": False, "formal_increment": 0})
        raise
