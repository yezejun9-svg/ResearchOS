#!/usr/bin/env python3
"""Offline, pinned build of guarded Desktop/CLI NSIS carrier media."""
import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
NSI = Path(__file__).resolve().parent / "nsis" / "researchos.nsi"
ICON = NSI.with_name("ResearchOS.ico")
SCOPE_SCHEMA = "researchos.installer-p1b-source-build-scope.v1"
NSIS_SCHEMA = "researchos.scoped-nsis-tool-inputs.v1"
NSIS_EXE = Path(r"C:\Program Files (x86)\NSIS\Bin\makensis.exe")
HASH = set("0123456789abcdef")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def pinned_json(ref):
    path = Path(ref["path"])
    data = path.read_bytes()
    if len(data) != ref["bytes"] or sha(data) != ref["sha256"]:
        raise ValueError(f"fixed JSON changed: {path}")
    return json.loads(data)


def pinned_file(ref):
    path = Path(ref["path"])
    if path.stat().st_size != ref["bytes"] or file_sha(path) != ref["sha256"]:
        raise ValueError(f"fixed file changed: {path}")
    return path


def validate_payload(root, manifest):
    rows = manifest["files"]
    if manifest["schema"] != "researchos.static-payload/1" or len(rows) != 132:
        raise ValueError("unexpected P1a payload schema or inventory")
    names = set()
    for row in rows:
        name = row["path"]
        parts = name.split("/")
        if any(p in ("", ".", "..") or ":" in p or "\\" in p for p in parts):
            raise ValueError(f"unsafe payload path: {name}")
        path = root.joinpath(*parts)
        stat = path.lstat()
        if path.is_symlink() or not path.is_file() or getattr(stat, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"redirected payload file: {name}")
        if stat.st_size != row["bytes"] or file_sha(path) != row["sha256"]:
            raise ValueError(f"payload differs: {name}")
        folded = name.casefold()
        if folded in names:
            raise ValueError("case alias in manifest")
        names.add(folded)
    physical = set()
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            d = Path(parent) / name
            if d.is_symlink() or getattr(d.lstat(), "st_file_attributes", 0) & 0x400:
                raise ValueError(f"redirected payload directory: {d}")
        for name in files:
            physical.add((Path(parent) / name).relative_to(root).as_posix().casefold())
    if physical != names:
        raise ValueError("payload physical inventory differs")
    return rows


def validate_nsis(inputs):
    if inputs["schema"] != NSIS_SCHEMA or len(inputs["files"]) != 442:
        raise ValueError("NSIS input closure differs from Root pin")
    root = Path(inputs["root"])
    for row in inputs["files"]:
        path = root.joinpath(*row["path"].split("/"))
        if path.stat().st_size != row["bytes"] or file_sha(path) != row["sha256"]:
            raise ValueError(f"NSIS tool input differs: {row['path']}")
    if str(NSIS_EXE) != str(root / "Bin" / "makensis.exe"):
        raise ValueError("compiler path differs")


def create_archive(path, payload_root, manifest_path, finalizer, rows):
    # Fixed ordering and timestamps make the archived bytes reproducible.
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1,
                         allowZip64=True, strict_timestamps=True) as archive:
        for row in rows:
            name = "payload/" + row["path"]
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            with payload_root.joinpath(*row["path"].split("/")).open("rb") as src, archive.open(info, "w", force_zip64=True) as dst:
                for chunk in iter(lambda: src.read(4 * 1024 * 1024), b""):
                    dst.write(chunk)
        for name, source in (("payload-manifest.json", manifest_path), ("finalizer.exe", finalizer)):
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())


def inspect_archive(path, rows, manifest_sha, finalizer_sha):
    expected = {"payload/" + r["path"]: (r["bytes"], r["sha256"]) for r in rows}
    expected.update({"payload-manifest.json": (None, manifest_sha), "finalizer.exe": (None, finalizer_sha)})
    with zipfile.ZipFile(path) as z:
        if set(z.namelist()) != set(expected):
            raise ValueError("archive inventory differs")
        for name, (size, digest) in expected.items():
            h = hashlib.sha256()
            with z.open(name) as f:
                count = 0
                for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
                    count += len(chunk)
                    h.update(chunk)
            if (size is not None and count != size) or h.hexdigest() != digest:
                raise ValueError(f"archive byte mismatch: {name}")


def embedded_exactly_once(exe, needle):
    with exe.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        first = mm.find(needle)
        return first >= 0 and mm.find(needle, first + 1) == -1


def build(args):
    raw = Path(args.scope).read_bytes()
    if sha(raw) != args.scope_sha256:
        raise ValueError("scope hash mismatch")
    scope = json.loads(raw)
    if scope.get("schema") != SCOPE_SCHEMA or scope.get("owner") != "codex:/root/installer_p1b_builder" or Path(scope["worktree"]) != ROOT:
        raise ValueError("scope owner/worktree mismatch")
    if len(scope["source_paths"]) != 11:
        raise ValueError("source scope changed")
    artifact_root, receipt_root = Path(scope["artifact_root"]), Path(scope["receipts_root"])
    if not artifact_root.is_dir() or not receipt_root.is_dir():
        raise ValueError("authorized artifact/receipt roots absent")
    output, receipts = artifact_root / args.candidate, receipt_root / args.candidate
    if output.exists() or receipts.exists():
        raise ValueError("candidate output or receipt already exists")
    manifest_path = pinned_file(scope["payload_manifest_ref"])
    manifest = json.loads(manifest_path.read_bytes())
    finalizer = pinned_file(scope["finalizer_ref"])
    inputs = pinned_json(scope["nsis_tool_inputs_ref"])
    pinned_json(scope["toolchain_lock_ref"])
    validate_nsis(inputs)
    payload_root = Path(scope["payload_artifact_root"]) / "payload"
    rows = validate_payload(payload_root, manifest)
    if not NSI.is_file() or not ICON.is_file():
        raise ValueError("NSIS source or ResearchOS icon missing")
    output.mkdir()
    receipts.mkdir()
    archive = output / "reviewed-p1a-payload.zip"
    create_archive(archive, payload_root, manifest_path, finalizer, rows)
    inspect_archive(archive, rows, scope["payload_manifest_ref"]["sha256"], scope["finalizer_ref"]["sha256"])
    archive_sha = file_sha(archive)
    commands = []
    for edition in ("Desktop", "CLI"):
        outfile = output / f"ResearchOS-{edition}-P1b-UNQUALIFIED.exe"
        argv = [str(NSIS_EXE), "/V4", f"/DEDITION={edition}", f"/DOUTFILE={outfile}",
                f"/DICON={ICON}", f"/DARCHIVE={archive}", f"/DMANIFEST={manifest_path}",
                f"/DFINALIZER={finalizer}", str(NSI)]
        command = {"argv": argv, "cwd": str(ROOT), "environment": {"NSISDIR": str(Path(inputs["root"]))},
                   "edition": edition, "tool_sha256": next(r["sha256"] for r in inputs["files"] if r["path"] == "Bin/makensis.exe")}
        (receipts / f"{edition.lower()}-command.json").write_bytes(encode(command))
        env = os.environ.copy()
        env["NSISDIR"] = str(Path(inputs["root"]))
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True)
        (receipts / f"{edition.lower()}-stdout.raw").write_bytes(result.stdout)
        (receipts / f"{edition.lower()}-stderr.raw").write_bytes(result.stderr)
        (receipts / f"{edition.lower()}-exit.json").write_bytes(encode({"exit_code": result.returncode}))
        if result.returncode != 0 or not outfile.is_file():
            raise RuntimeError(f"{edition} makensis failed with exit {result.returncode}")
        # SetCompress off preserves every File input as contiguous bytes. This
        # proves archive/helper/manifest are inside media without executing it.
        if not embedded_exactly_once(outfile, archive.read_bytes()) or not embedded_exactly_once(outfile, finalizer.read_bytes()) or not embedded_exactly_once(outfile, manifest_path.read_bytes()):
            raise ValueError(f"{edition} embedded bytes not found exactly once")
        commands.append({"edition": edition, "exe": str(outfile), "sha256": file_sha(outfile), "bytes": outfile.stat().st_size})
    validate_nsis(inputs)
    validate_payload(payload_root, manifest)
    result = {"status": "COMPILED_UNQUALIFIED_GUARDED_MEDIA", "formal_increment": 0,
              "payload_file_count": len(rows), "archive_sha256": archive_sha, "archive_bytes": archive.stat().st_size,
              "payload_manifest_sha256": scope["payload_manifest_ref"]["sha256"],
              "finalizer_sha256": scope["finalizer_ref"]["sha256"], "media": commands,
              "capability": "REJECTS_BEFORE_PROGRAM_DATA_REGISTRY_PATH_MUTATION",
              "limitations": ["NO_FRESH_INSTALL", "NO_UPGRADE", "NO_UNINSTALL", "NO_MAINTENANCE_GATE", "UNSIGNED"]}
    (receipts / "build-result.json").write_bytes(encode(result))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", required=True)
    parser.add_argument("--scope-sha256", required=True)
    parser.add_argument("--candidate", required=True)
    arguments = parser.parse_args()
    try:
        build(arguments)
    except Exception as exc:
        print(f"guarded media build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
