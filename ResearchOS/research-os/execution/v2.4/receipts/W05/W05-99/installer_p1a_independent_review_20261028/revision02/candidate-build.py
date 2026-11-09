#!/usr/bin/env python3
"""Freeze the reviewed product candidate into a relocatable static payload.

This command only reads the candidate and writes a new output/receipt directory.
It neither installs nor launches the product.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FINALIZER = Path(__file__).resolve().parent / "finalize" / "main.go"
MARKER_SHA256 = "c785a1bb1b328cac9c37794e8fbd7cf607c4e4322f80963ea203436ba4e2f8e3"
SOURCE_COMMIT = "5c4c94022bd92da68ef544f2779527bfe065c428"
VERIFIER_PATH = "apps/desktop/resources/control/runtime-verifier-installation.json"
HASH = re.compile(r"[0-9a-f]{64}\Z")
ROLES = ("cli", "control", "electron", "verifier", "validator")
SCOPE_SCHEMAS = {
    "researchos.installer-p1a-exact4-revision-scope.v1",
    "researchos.installer-p1a-exact2-scope-admission-revision.v1",
}
SCOPE_OWNER = "codex:/root/installer_p1a_builder"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def regular(path):
    stat = path.lstat()
    if path.is_symlink() or not path.is_file() or stat.st_nlink != 1:
        raise ValueError(f"nonregular or aliased file: {path}")
    if getattr(stat, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"reparse file: {path}")
    return stat


def exact_tree(root):
    """Return physical files, rejecting links/reparse nodes and spelling aliases."""
    result = {}
    root = Path(root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError("root must be an existing absolute directory")
    for directory, dirs, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in dirs:
            path = parent / name
            if path.is_symlink() or not path.is_dir() or getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
                raise ValueError(f"redirected directory: {path}")
        for name in files:
            path = parent / name
            regular(path)
            relative = path.relative_to(root).as_posix()
            folded = relative.casefold()
            if folded in result:
                raise ValueError(f"case alias: {relative}")
            result[folded] = relative
    return result


def validate_row(row):
    if not isinstance(row, dict) or set(row) != {"path", "sha256", "bytes"}:
        raise ValueError("invalid inventory row")
    name = row["path"]
    if (not isinstance(name, str) or not name or "\\" in name or name.startswith("/")
            or any(part in ("", ".", "..") or part.endswith((".", " "))
                   or ":" in part for part in name.split("/"))):
        raise ValueError(f"unsafe inventory path: {name!r}")
    if not isinstance(row["bytes"], int) or isinstance(row["bytes"], bool) or row["bytes"] < 0:
        raise ValueError(f"invalid size: {name}")
    if not isinstance(row["sha256"], str) or not HASH.fullmatch(row["sha256"]):
        raise ValueError(f"invalid digest: {name}")


def verify_files(root, rows, extra=(), strict_physical=True):
    names = set()
    previous = ""
    for row in rows:
        validate_row(row)
        name = row["path"]
        if name <= previous or name.casefold() in names:
            raise ValueError(f"unsorted or alias inventory: {name}")
        names.add(name.casefold())
        previous = name
        path = root.joinpath(*name.split("/"))
        stat = regular(path)
        if stat.st_size != row["bytes"] or digest(path.read_bytes()) != row["sha256"]:
            raise ValueError(f"file changed: {name}")
    physical = exact_tree(root)
    expected = {row["path"].casefold(): row["path"] for row in rows}
    expected.update({name.casefold(): name for name in extra})
    if any(physical.get(key) != name for key, name in expected.items()) or (strict_physical and physical != expected):
        raise ValueError(f"physical inventory mismatch: missing={sorted(set(expected)-set(physical))}, extra={sorted(set(physical)-set(expected))}")
    return [physical[key] for key in sorted(set(physical) - set(expected))]


def source_extras(root, rows):
    expected = {row["path"].casefold() for row in rows} | {"installed-product.json"}
    return [{"path": name, "sha256": digest((root / name).read_bytes()),
             "bytes": regular(root / name).st_size}
            for key, name in sorted(exact_tree(root).items()) if key not in expected]


def canonical_path(value, require_existing=False):
    """Reject lexical aliases and existing Windows reparse/case aliases."""
    if not isinstance(value, str) or not Path(value).is_absolute() or os.path.normpath(value) != value:
        raise ValueError(f"noncanonical absolute path: {value!r}")
    path = Path(value)
    if not re.fullmatch(r"[A-Z]:\\", path.anchor):
        raise ValueError(f"canonical drive path required: {value!r}")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        if part.endswith((".", " ")) or part in (".", ".."):
            raise ValueError(f"noncanonical path component: {part!r}")
        if not current.is_dir():
            break
        names = os.listdir(current)
        if part not in names:
            if any(name.casefold() == part.casefold() for name in names):
                raise ValueError(f"case alias path component: {part!r}")
            break
        current /= part
        stat = current.lstat()
        if current.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"reparse ancestor: {current}")
    if require_existing and not path.is_dir():
        raise ValueError(f"required directory absent: {value}")
    if path.resolve(strict=False) != path:
        raise ValueError(f"redirected path: {value}")
    return path


def related(left, right):
    l, r = str(left).casefold(), str(right).casefold()
    return l == r or l.startswith(r + os.sep.casefold()) or r.startswith(l + os.sep.casefold())


def validate_destinations(candidate_raw, output_raw, receipts_raw, artifact_raw, receipt_root_raw):
    candidate = canonical_path(candidate_raw, require_existing=True)
    artifact = canonical_path(artifact_raw, require_existing=True)
    receipt_root = canonical_path(receipt_root_raw, require_existing=True)
    output = canonical_path(output_raw)
    receipts = canonical_path(receipts_raw)
    if output.parent != artifact or receipts.parent != receipt_root:
        raise ValueError("output and receipts must be direct children of authorized roots")
    if any(related(a, b) for a, b in ((candidate, output), (candidate, receipts),
                                       (candidate, artifact), (candidate, receipt_root),
                                       (output, receipts), (artifact, receipt_root))):
        raise ValueError("source, output and receipt roots overlap")
    if output.exists() or receipts.exists():
        raise ValueError("output and receipts must be create-new")
    return candidate, output, receipts


def bound_roots(scope_raw, expected_sha256):
    if not isinstance(expected_sha256, str) or not HASH.fullmatch(expected_sha256):
        raise ValueError("an external scope SHA-256 pin is required")
    scope = canonical_path(scope_raw)
    raw = scope.read_bytes()
    if digest(raw) != expected_sha256:
        raise ValueError("scope bytes differ from external SHA-256 pin")
    document = json.loads(raw)
    if not isinstance(document, dict) or document.get("schema") not in SCOPE_SCHEMAS or \
            document.get("owner") != SCOPE_OWNER or document.get("worktree") != str(ROOT):
        raise ValueError("unrecognized scope contract, owner or worktree")
    artifact, receipt = document.get("artifact_root"), document.get("receipt_root")
    if not isinstance(artifact, str) or not isinstance(receipt, str):
        raise ValueError("scope roots required")
    canonical_path(artifact, require_existing=True)
    canonical_path(receipt, require_existing=True)
    if related(Path(artifact), Path(receipt)):
        raise ValueError("scope roots overlap")
    return artifact, receipt


def freeze(candidate):
    marker_path = candidate / "installed-product.json"
    if regular(marker_path).st_size != 20401 or digest(marker_path.read_bytes()) != MARKER_SHA256:
        raise ValueError("candidate marker differs from independent review")
    marker = json.loads(marker_path.read_bytes())
    if marker.get("source_commit") != SOURCE_COMMIT or marker.get("schema") != "researchos.product-layout/1":
        raise ValueError("candidate source/schema mismatch")
    rows = marker["files"]
    verify_files(candidate, rows, extra=("installed-product.json",), strict_physical=False)
    binaries = marker["binaries"]
    for role in ROLES:
        item = binaries.get(role)
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise ValueError(f"binary role malformed: {role}")
        match = next((row for row in rows if row["path"] == item["path"]), None)
        if match is None or match["sha256"] != item["sha256"]:
            raise ValueError(f"binary role changed: {role}")
    verifier = json.loads((candidate / VERIFIER_PATH).read_bytes())
    if (verifier.get("source_commit") != SOURCE_COMMIT or
            verifier.get("executable_hash") != "sha256:" + binaries["verifier"]["sha256"] or
            verifier.get("arguments") != []):
        raise ValueError("candidate verifier manifest mismatch")
    metadata = {key: value for key, value in marker.items() if key not in
                ("files", "binaries", "install_root", "installation_id", "inventory_digest")}
    payload_rows = [row for row in rows if row["path"] != VERIFIER_PATH]
    if len(rows) != len(payload_rows) + 1:
        raise ValueError("verifier manifest absent from candidate inventory")
    return {"schema": "researchos.static-payload/1", "candidate_marker_sha256": MARKER_SHA256,
            "metadata": metadata, "binaries": binaries, "files": payload_rows,
            "verifier_template": {key: value for key, value in verifier.items()
                                  if key not in ("executable", "executable_hash")}}


def build(args, authorized_roots=None):
    args._owned_receipts = None
    artifact_root, receipt_root = authorized_roots or bound_roots(args.scope, args.scope_sha256)
    candidate, output, receipts = validate_destinations(
        args.candidate, args.output, args.receipts, artifact_root, receipt_root)
    locked = json.loads((ROOT / "execution/toolchains/locked.json").read_bytes())["tools"]
    go = Path(args.go).absolute()
    if digest(go.read_bytes()) != locked["go"]["sha256"]:
        raise ValueError("Go compiler is not pinned")
    manifest = freeze(candidate)
    source_extra_before = source_extras(candidate, json.loads((candidate / "installed-product.json").read_bytes())["files"])
    raw = encode(manifest)
    receipts.mkdir(exist_ok=False)
    owned = receipts.lstat()
    args._owned_receipts = (receipts, owned.st_dev, owned.st_ino)
    output.mkdir(exist_ok=False)
    (receipts / "candidate-before.json").write_bytes(encode({"marker_sha256": MARKER_SHA256,
        "source_commit": SOURCE_COMMIT, "files": len(manifest["files"]),
        "unreviewed_source_extras_excluded": source_extra_before}))
    payload = output / "payload"
    payload.mkdir()
    for row in manifest["files"]:
        src = candidate.joinpath(*row["path"].split("/"))
        dst = payload.joinpath(*row["path"].split("/"))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    verify_files(payload, manifest["files"])
    if freeze(candidate) != manifest:
        raise ValueError("source changed during payload copy")
    source_extra_after = source_extras(candidate, json.loads((candidate / "installed-product.json").read_bytes())["files"])
    if source_extra_after != source_extra_before:
        raise ValueError("unreviewed source extras changed during payload copy")
    (receipts / "candidate-after.json").write_bytes(encode({"marker_sha256": MARKER_SHA256,
        "source_commit": SOURCE_COMMIT, "files": len(manifest["files"]),
        "unreviewed_source_extras_excluded": source_extra_after}))
    (output / "payload-manifest.json").write_bytes(raw)
    scratch = output / "build-scratch"
    for name in ("gocache", "gotmp", "gomodcache", "temp"):
        (scratch / name).mkdir(parents=True)
    env = os.environ.copy()
    env.update({"GOENV": "off", "GOTOOLCHAIN": "local", "GOROOT": str(go.parent.parent),
                "GOPATH": str(scratch), "GOMODCACHE": str(scratch / "gomodcache"),
                "GOCACHE": str(scratch / "gocache"), "GOTMPDIR": str(scratch / "gotmp"),
                "GOPROXY": "off", "GOSUMDB": "off", "TEMP": str(scratch / "temp"),
                "TMP": str(scratch / "temp")})
    command = [str(go), "build", "-mod=readonly", "-trimpath", "-buildvcs=false",
               "-ldflags=-X main.trustedManifestSHA256=" + digest(raw),
               "-o", str(output / "finalizer.exe"), str(FINALIZER)]
    (receipts / "go-build-command.json").write_bytes(encode({"argv": command,
        "tool_sha256": locked["go"]["sha256"], "manifest_sha256": digest(raw)}))
    run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
    (receipts / "go-build.stdout.raw").write_bytes(run.stdout)
    (receipts / "go-build.stderr.raw").write_bytes(run.stderr)
    (receipts / "go-build-exit.json").write_bytes(encode({"exit_code": run.returncode}))
    if run.returncode:
        raise RuntimeError("pinned Go finalizer build failed")
    shutil.rmtree(scratch)
    (receipts / "result.json").write_bytes(encode({"status": "STATIC_PAYLOAD_BUILT_NOT_INSTALLED",
        "candidate_marker_sha256": MARKER_SHA256, "payload_manifest_sha256": digest(raw),
        "finalizer_sha256": digest((output / "finalizer.exe").read_bytes()),
        "payload_file_count": len(manifest["files"]), "formal_increment": 0}))
    print((receipts / "result.json").read_text(encoding="utf-8"), end="")


def write_owned_failure(args, exc):
    owned = getattr(args, "_owned_receipts", None)
    if owned is None:
        return False
    target, device, inode = owned
    try:
        stat = target.lstat()
        if stat.st_dev != device or stat.st_ino != inode or target.is_symlink() or \
                getattr(stat, "st_file_attributes", 0) & 0x400:
            return False
        with (target / "failed.json").open("xb") as file:
            file.write(encode({"status": "FIRST_FAILURE_RETAINED",
                "error_type": type(exc).__name__, "error": str(exc)}))
        return True
    except (OSError, ValueError):
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for flag in ("candidate", "output", "receipts", "go", "scope", "scope-sha256"):
        parser.add_argument("--" + flag, required=True)
    arguments = parser.parse_args()
    try:
        build(arguments)
    except Exception as exc:
        write_owned_failure(arguments, exc)
        print(f"static payload build refused: {exc}", file=sys.stderr)
        raise SystemExit(1)
