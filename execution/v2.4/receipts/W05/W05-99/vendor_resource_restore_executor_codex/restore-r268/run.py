"""Execute the registered absent-only six-asset recovery; preserve all other state."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import traceback

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
SCOPE = "execution/v2.4/receipts/W05/W05-99/integration_codex/vendor-resource-scope-r268/scope_registration.json"
EXPECTED_SCOPE = "e204b141401508d858700ca6b32f34ffc54b145fc111085610957139936b118f"
EXPECTED_MANIFEST = "bd503c9b8078002a1471d01ef0f354dc82670a2a9726f2d1f9ea1497579e48de"
BASE = "4ba293847072069cd99154e5054f6ef4ae2b92e1"


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with (OUT / name).open("xb") as stream:
        stream.write(raw)
    return {"path": (OUT / name).relative_to(ROOT).as_posix(), "sha256": digest(raw)}


def run(name, argv):
    started = stamp()
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True)
    for suffix, raw in (("stdout.raw", proc.stdout), ("stderr.raw", proc.stderr)):
        with (OUT / (name + "." + suffix)).open("xb") as stream:
            stream.write(raw)
    save(name + ".invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": started,
         "ended_at": stamp(), "actual_exit": proc.returncode,
         "stdout_sha256": digest(proc.stdout), "stderr_sha256": digest(proc.stderr)})
    assert proc.returncode == 0, (name, proc.returncode)
    return proc.stdout


def safe_absent(relative):
    target = ROOT / relative
    vendor = (ROOT / "third_party/mu").resolve(strict=True)
    assert target.parent.resolve(strict=True).is_relative_to(vendor), relative
    for parent in [target.parent, *target.parent.parents]:
        if parent == ROOT.parent:
            break
        info = parent.lstat()
        assert stat.S_ISDIR(info.st_mode), str(parent)
        assert not (getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT), str(parent)
    assert not os.path.lexists(target), relative
    return target


def audit(entries):
    result = []
    for relative, expected in sorted(entries.items()):
        assert relative.startswith("third_party/mu/") and ".." not in Path(relative).parts
        path = ROOT / relative
        row = {"path": relative, "expected_sha256": expected["sha256"], "expected_size": expected["size"]}
        if not os.path.lexists(path):
            row["status"] = "MISSING"
        else:
            info = path.lstat()
            assert stat.S_ISREG(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT), relative
            raw = path.read_bytes()
            row.update(sha256=digest(raw), size=len(raw), status="MATCH" if digest(raw) == expected["sha256"] and len(raw) == expected["size"] else "DRIFT")
        result.append(row)
    return result


def public_inputs():
    names = [SCOPE, "third_party/mu.MANIFEST.json", "third_party/VENDORED_FROM.md",
             "execution/v2.4/component_lock.json", "third_party/mu/package-lock.json",
             "adapters/runtime/mu/build.mjs", "adapters/runtime/mu/worker.mjs"]
    return [{"path": name, "sha256": digest((ROOT / name).read_bytes()), "bytes": (ROOT / name).stat().st_size} for name in names]


def main():
    assert digest((ROOT / SCOPE).read_bytes()) == EXPECTED_SCOPE
    scope = json.loads((ROOT / SCOPE).read_bytes())
    assert scope["base_head"] == BASE and scope["owner"] == "codex:/root"
    assert run("head-before", ["git", "rev-parse", "HEAD"]).decode().strip() == BASE
    assert not run("index-before", ["git", "diff", "--cached", "--name-only", "-z"])
    status_before = run("status-before", ["git", "status", "--short", "--untracked-files=no"])
    manifest_raw = (ROOT / "third_party/mu.MANIFEST.json").read_bytes()
    assert digest(manifest_raw) == EXPECTED_MANIFEST
    manifest = json.loads(manifest_raw)
    assert manifest["files"] == len(manifest["entries"]) == 5083
    inputs_before = public_inputs()
    save("public-inputs.before.json", inputs_before)
    before = audit(manifest["entries"])
    before_ref = save("vendor.before.json", before)
    paths = scope["exact_resource_paths"]
    assert len(paths) == len(set(paths)) == 6
    assert {x["path"] for x in before if x["status"] == "MISSING"} == set(paths)
    assert not any(x["status"] == "DRIFT" for x in before)
    blobs = []
    # Validate every asset before any resource write, then revalidate per create.
    for index, asset in enumerate(scope["resources"]):
        relative = asset["path"]
        assert relative in paths and asset["expected_absence"]
        expected = manifest["entries"][relative]
        assert expected == {"sha256": asset["expected_sha256"], "size": asset["expected_size"]}
        safe_absent(relative)
        oid = run(f"asset-{index}-head-oid", ["git", "rev-parse", BASE + ":" + relative]).decode().strip()
        assert oid == asset["git"]["blob_oid"]
        raw = run(f"asset-{index}-original", ["git", "cat-file", "blob", oid])
        assert digest(raw) == expected["sha256"] and len(raw) == expected["size"]
        blobs.append((asset, raw))
    restored = []
    for asset, raw in blobs:
        assert public_inputs() == inputs_before
        target = safe_absent(asset["path"])
        with target.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        actual = target.read_bytes()
        assert actual == raw
        restored.append({"path": asset["path"], "sha256": digest(actual), "bytes": len(actual), "mode": "EXCLUSIVE_CREATE_FROM_IMMUTABLE_GIT_BLOB", "completed_at": stamp()})
        save(f"restored-{len(restored)}.json", restored[-1])
    after = audit(manifest["entries"])
    after_ref = save("vendor.after.json", after)
    assert all(x["status"] == "MATCH" for x in after)
    before_map = {x["path"]: x for x in before}
    assert all(x == before_map[x["path"]] for x in after if x["path"] not in paths)
    inputs_after = public_inputs()
    save("public-inputs.after.json", inputs_after)
    assert inputs_before == inputs_after
    status_after = run("status-after", ["git", "status", "--short", "--untracked-files=no"])
    removed = {line for line in status_before.decode().splitlines() if any(relative in line for relative in paths)}
    assert len(removed) == 6
    assert set(status_after.decode().splitlines()) == set(status_before.decode().splitlines()) - removed
    mirror = ROOT / "third_party/mu/node_modules/@earendil-works/pi-coding-agent/docs/images/exy.png"
    assert mirror.resolve(strict=True) == (ROOT / paths[-1]).resolve(strict=True)
    result = {"schema": "researchos.root.fixed-vendor-resource-recovery.v1", "actor": "codex:/root", "actual_at": stamp(),
              "status": "RESOURCE_BYTES_RESTORED_ALL_5083_MANIFEST_MATCH", "actual_exit": 0, "scope_ref": {"path": SCOPE, "sha256": EXPECTED_SCOPE},
              "vendor_before_ref": before_ref, "vendor_after_ref": after_ref, "before_matching": 5077, "before_missing": 6,
              "after_matching": 5083, "after_missing": 0, "existing_file_drift": 0, "restored": restored,
              "unchanged_public_inputs": True, "other_tracked_deletions_preserved": True, "mirror_is_same_original_path": True,
              "sdk_code_manifest_lock_changed": False, "actual_build_executed": False, "bundle_qualification": False, "formal_increment": 0}
    ref = save("result.json", result)
    print(json.dumps({"result_ref": ref, "status": result["status"], "restored": 6, "after_matching": 5083}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        save("failure.json", {"actual_at": stamp(), "actor": "codex:/root", "traceback": traceback.format_exc(), "formal_increment": 0, "automatic_retry": False})
        raise
