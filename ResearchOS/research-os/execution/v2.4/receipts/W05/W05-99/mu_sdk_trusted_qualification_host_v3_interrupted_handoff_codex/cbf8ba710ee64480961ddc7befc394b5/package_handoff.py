"""Freeze the interrupted Source draft and exact stored commandExecution items.

Read-only against the Source and Codex SQLite store. Writes only this handoff.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

here = Path(__file__).resolve().parent
source = here.parent.parent / "mu_sdk_trusted_qualification_host_source_v3_codex" / "c8b22080210c4a398acd8ad294ce31fc"
thread = "01a1100f-9a62-7282-be7c-d75c36fc4ccd"
db = Path(r"C:\Users\yqyyds\.codex\thread_history_1.sqlite")
items = {
    730: "exec-51cc7f09-100b-4808-a1c2-79fd459eb29b",
    732: "exec-298c277c-637b-40a7-83d7-3c168c94b974",
    733: "exec-c79f3e8c-37ec-45b9-a81d-431c01e6a644",
    734: "exec-1e8f5f95-427b-42c2-89be-b34ee20125e2",
    735: "exec-1292d5cb-f486-4723-9e99-eef4b4b176ec",
}
expected_source = [
    "execute.go", "go.authority.template.json", "hostapi.go", "main.go",
    "prepare.go", "prepare_runtime.go", "profile.template.json", "seed.template.json",
]

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

snapshot = here / "source_snapshot"
snapshot.mkdir(exist_ok=False)
members = []
for name in expected_source:
    origin = source / name
    data = origin.read_bytes()
    target = snapshot / name
    target.write_bytes(data)
    assert target.read_bytes() == data
    members.append({"name": name, "source_path": str(origin), "snapshot_path": str(target), "sha256": sha(data), "bytes": len(data)})
assert sorted(p.name for p in source.iterdir() if p.is_file()) == sorted(expected_source)

origin_dir = here / "original_io"
origin_dir.mkdir(exist_ok=False)
origins = []
con = sqlite3.connect("file:" + str(db) + "?mode=ro", uri=True)
for ordinal, item in items.items():
    row = con.execute("SELECT rollout_ordinal,item_type,item_json FROM thread_items WHERE thread_id=? AND item_id=?", (thread, item)).fetchone()
    assert row and row[1] == "commandExecution"
    raw = row[2].encode("utf-8")
    target = origin_dir / f"{ordinal}.commandExecution.item_json"
    target.write_bytes(raw)
    obj = json.loads(row[2])
    origins.append({"ordinal": ordinal, "thread_item_id": item, "rollout_ordinal": row[0], "path": str(target), "sha256": sha(raw), "bytes": len(raw), "outer_exit_code": obj.get("exitCode"), "status": obj.get("status")})
con.close()

# This failure happened in the functions.exec JavaScript isolate before any
# nested command or apply_patch call. No commandExecution row exists for it.
js_visible = (
    "Script failed\n"
    "Wall time 0.0 seconds\n"
    "Output:\n"
    "Script error:\n"
    "ReferenceError: p is not defined\n"
    "    at exec_main.mjs:2:30\n"
).encode("utf-8")
js_target = origin_dir / "731.visible_tool_response.txt"
js_target.write_bytes(js_visible)
origins.append({"ordinal": 731, "functions_exec_call_history_item": "01a11c36-5b7e-7370-9874-209022e63b2d/491225192", "path": str(js_target), "sha256": sha(js_visible), "bytes": len(js_visible), "shell_started": False, "capture_gap": "Visible response transcribed; no persisted commandExecution item or raw functions.exec transport payload."})
origins.sort(key=lambda x: x["ordinal"])

gaps = {
    "730": "Stored commandExecution item_json is complete as persisted, but contains decoded aggregatedOutput rather than original PTY bytes; downstream rg failed for a missing guessed path.",
    "731": "JavaScript ReferenceError before nested tool call. Visible tool response transcribed; original transport bytes unavailable. No shell/Python/native process started.",
    "732": "gofmt command not found in PowerShell; no Go formatter/native child started and no files formatted.",
    "733": "Stored commandExecution item_json decoded output; two guessed files absent; independent valid read in same batch did not cure failed rg.",
    "734": "Empty match during optional tool discovery. Diagnostic classification pending; exit code alone does not establish an implementation failure.",
    "735": "Outer PowerShell exit code 0 due pipeline tail, but stored aggregatedOutput includes an rg missing-path diagnostic for task.go.",
}
(here / "CAPTURE_GAPS.json").write_text(json.dumps(gaps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(here / "source_members.json").write_text(json.dumps(members, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(here / "origins.json").write_text(json.dumps(origins, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

manifest_entries = []
for path in sorted(here.rglob("*")):
    if not path.is_file() or path.name in {"manifest.json", "handoff.json"}:
        continue
    data = path.read_bytes()
    manifest_entries.append({"path": str(path.relative_to(here)).replace("\\", "/"), "sha256": sha(data), "bytes": len(data)})
manifest = {"schema": "researchos.interrupted-source-handoff.manifest.v1", "source_draft": str(source), "members": manifest_entries}
manifest_raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
(here / "manifest.json").write_bytes(manifest_raw)
handoff = {
    "schema": "researchos.interrupted-source-handoff.v1",
    "status": "SOURCE_DRAFT_FROZEN_UNVERIFIED",
    "source_namespace": str(source),
    "manifest_sha256": sha(manifest_raw),
    "manifest_bytes": len(manifest_raw),
    "source_member_count": len(members),
    "original_io_ordinals": [o["ordinal"] for o in origins],
    "implemented_in_draft": [
        "New prepare-runtime and finalize-prepare phase branches in main.go",
        "prepare-runtime reuses production prepareObjects and RegisterRuntimeQualificationPlan for a real independent qualification Goal/Task/Artifact/Runtime, leaving the qualification Task DRAFT",
        "prepare-runtime writes a private coordinator JSON with blank APIURL for the normal Host to fill",
        "finalize-prepare reads the CLI goal.start idempotency response, draft Goal, session, and formal binding before setting PREPARED",
        "seed.template.json leaves draft_goal_id empty until actual CLI draft exists",
    ],
    "not_verified_or_completed": [
        "No gofmt, Go parse, compile, test, or native setup was run; source syntax and runtime behavior remain unverified.",
        "No live CLI goal.start, Host startup, qualification admission, provider request, or database write from this Source occurred.",
        "No new source review or independent approval; no claim of trial readiness.",
        "The private coordinator credentials have a finite lifetime; startup timing and normal Host handoff remain to be checked.",
        "The exact stored CLI goal.start principal and response JSON assumptions in finalize-prepare remain to be verified against a real completed CLI command.",
        "The draft has not been reconciled with old Source static checker, diffs, or inverse; Root owns completion.",
        "Do not apply private runtime_bindings INSERT/DELETE. This draft uses only production Domain API plan creation.",
    ],
    "scope": "Receipt-only handoff. No Main, canonical, sealed old Source, native, SQL, provider, or setup execution.",
}
(here / "handoff.json").write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"handoff": str(here / "handoff.json"), "manifest_sha256": sha(manifest_raw), "source_members": len(members), "origins": [o["ordinal"] for o in origins]}, ensure_ascii=False))
