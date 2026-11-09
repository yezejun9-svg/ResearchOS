"""Preserve command exits before parsing the two frozen offline builds."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
SOURCE = "a418d503f29646f62010905f9dc9338630aa0108"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


lock = json.loads((ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8"))
if sha(Path(sys.executable).read_bytes()) != lock["tools"]["python"]["sha256"]:
    raise RuntimeError("Python tool hash differs from frozen lock")
steps = []
for label in ("a", "b"):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != SOURCE:
        raise RuntimeError("frozen source HEAD changed")
    archive = ROOT / f".local/researchos-development-a418d50-{label}.zip"
    if archive.exists():
        raise RuntimeError("output already exists")
    argv = [sys.executable, "-B", "-X", "utf8", "ops/release/build.py", "--output", str(archive)]
    command = {"argv": argv, "cwd": str(ROOT), "source_commit": SOURCE,
               "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(f"build-{label}.command.json", command)
    with (OUT / f"build-{label}.stdout.raw.json").open("wb") as stdout, (OUT / f"build-{label}.stderr.raw.txt").open("wb") as stderr:
        result = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr)
    command.update(exit_code=result.returncode, finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save(f"build-{label}.command.json", command)
    if result.returncode:
        raise RuntimeError(f"build {label} failed; raw output and actual exit preserved")
    receipt = json.loads((OUT / f"build-{label}.stdout.raw.json").read_text(encoding="utf-8"))
    if receipt["source_commit"] != SOURCE or receipt["archive_sha256"] != sha(archive.read_bytes()):
        raise RuntimeError("build receipt differs from archive")
    steps.append({"label": label, "command": command, "receipt": receipt})
    save("steps.json", steps)
archives = [Path(s["receipt"]["archive"]) for s in steps]
if archives[0].read_bytes() != archives[1].read_bytes():
    raise RuntimeError("archives differ")
with zipfile.ZipFile(archives[0]) as first, zipfile.ZipFile(archives[1]) as second:
    if first.namelist() != second.namelist():
        raise RuntimeError("archive entries differ")
    manifest = json.loads(first.read("release-manifest.json"))
    for entry in manifest["files"]:
        raw = first.read(entry["path"])
        if raw != second.read(entry["path"]) or len(raw) != entry["size"] or sha(raw) != entry["sha256"]:
            raise RuntimeError(entry["path"])
report = {"source_commit": SOURCE, "scope": "BOUNDED_OFFLINE_FIXTURE_PACKAGE_ONLY", "steps": steps,
          "identical_archive": True, "all_manifest_files_verified": len(manifest["files"]),
          "clean_windows_A15": "NOT_RUN", "current_actual_release_qualification": "CLOSED",
          "independent_fixture_review": "PENDING"}
save("report.json", report)
print(json.dumps({"source_commit": SOURCE, "archive_sha256": steps[0]["receipt"]["archive_sha256"],
                  "file_count": steps[0]["receipt"]["file_count"], "identical_archive": True,
                  "license_gaps": manifest["sbom"]["license_gaps"]}, ensure_ascii=False))
