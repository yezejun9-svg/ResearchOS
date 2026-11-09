from __future__ import annotations

import hashlib
import json
from pathlib import Path
from shutil import copy2


C = Path(r"C:/Users/yqyyds/Documents/Codex/2026-11-04/task")
OUT = Path(__file__).parent
REV4 = C / "product-v1-native-qualification-producer-author-20261105-rev4"
RUNS = C / "product-v1-owned-verification-20261104"
RUN = RUNS / "runs/product-v1-native-qualification-tests-01"
SCOPE = RUNS / "scopes/product-v1-native-qualification-tests-01.json"
OVERLAY = C / "product-v1-native-qualification-test01-rev4-overlay/overlay.json"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


rev4 = json.loads((REV4 / "MANIFEST.json").read_text(encoding="utf-8"))
scope = json.loads(SCOPE.read_text(encoding="utf-8"))
result = json.loads((RUN / "RESULT.json").read_text(encoding="utf-8"))
assert sha(SCOPE.read_bytes()) == "a9d093a2589f366cedff54c92a7060fc8a245153a59c791258ee32df44a72778"
assert sha(OVERLAY.read_bytes()) == "7077a172641cf0820b423265d09bd60ef180bb2cd9a7f3d31916e9d2a254f7c1"
assert result["status"] == "COMPLETED_OWNED_JOB_STOPPED" and result["root_exit_code"] == 0
assert result["stop_proved"] and result["job_active_zero"] and not result["input_drift"] and not result["errors"]
stdout = (RUN / "stdout.raw").read_bytes()
for package in ("internal/qualificationprobe", "cmd/researchos-qualification-helper", "adapters/runtime"):
    assert ("ok  \tresearchos.local/research-os/" + package).encode() in stdout or ("ok  \tresearchos.local/research-os/" + package).encode().replace(b"  ", b" ") in stdout
assert b"--- FAIL:" not in stdout and b"--- SKIP:" not in stdout

source_files = []
scope_inputs = {item["sha256"] for item in scope["inputs"]}
for item in rev4["files"]:
    rel = item["path"]
    original = REV4 / "source" / rel
    raw = original.read_bytes()
    assert sha(raw) == item["source_sha256"] and sha(raw) in scope_inputs
    dest = OUT / "source" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    copy2(original, dest)
    assert sha(dest.read_bytes()) == item["source_sha256"]
    source_files.append(item)

evidence = [
    (REV4 / "MANIFEST.json", OUT / "rev4/MANIFEST.json"),
    (REV4 / "changes.patch", OUT / "rev4/changes.patch"),
    (REV4 / "changes.inverse.patch", OUT / "rev4/changes.inverse.patch"),
    (REV4 / "FROZEN.txt", OUT / "rev4/FROZEN.txt"),
    (SCOPE, OUT / "test01/scope.json"),
    (OVERLAY, OUT / "test01/overlay.json"),
    (RUN / "RESULT.json", OUT / "test01/RESULT.json"),
    (RUN / "CONSUMED.json", OUT / "test01/CONSUMED.json"),
    (RUN / "stdout.raw", OUT / "test01/stdout.raw"),
    (RUN / "stderr.raw", OUT / "test01/stderr.raw"),
]
evidence_files = []
for src, dest in evidence:
    dest.parent.mkdir(parents=True, exist_ok=True)
    copy2(src, dest)
    assert dest.read_bytes() == src.read_bytes()
    evidence_files.append({"path": dest.relative_to(OUT).as_posix(), "sha256": sha(dest.read_bytes())})

manifest = {
    "schema": "researchos.native-qualification-source-test01-archive.v1",
    "status": "GO_ONLY_FAKE_TEST01_PASS_PENDING_INDEPENDENT_REVIEW_AND_INTEGRATION",
    "rev4_manifest_sha256": sha((REV4 / "MANIFEST.json").read_bytes()),
    "test_scope_sha256": sha(SCOPE.read_bytes()),
    "result_status": result["status"],
    "result_exit_code": result["root_exit_code"],
    "stop_proved": result["stop_proved"],
    "input_drift": result["input_drift"],
    "packages": ["internal/qualificationprobe", "cmd/researchos-qualification-helper", "adapters/runtime"],
    "source_files": source_files,
    "evidence_files": evidence_files,
    "native_cli_auth_probe_model": "NOT_RUN_BY_B3_AUTHOR_OR_TEST01",
    "formal_acceptance": False,
    "product_acceptance": False,
}
(OUT / "ARCHIVE-MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(OUT / "FROZEN.txt").write_text("Exact rev4 eight-file source and raw supervised Go-only fake test01 receipt copied and hash-verified. No Native/model acceptance.\n", encoding="utf-8")
print(sha((OUT / "ARCHIVE-MANIFEST.json").read_bytes()))
