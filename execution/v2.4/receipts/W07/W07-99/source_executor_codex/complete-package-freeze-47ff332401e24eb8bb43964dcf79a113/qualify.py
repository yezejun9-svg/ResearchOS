"""Actual readonly Go dependency qualification; no public-source capture."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[6]
MAIN = Path("D:/作品集/ResearchOS/research-os")
GO = MAIN / ".local/tools/go1.27.1/go/bin/go.exe"
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {"path": str(p), "sha256": digest(p)}
def save(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def run(argv, stem, env, cwd=ROOT):
    start = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=cwd, env=env, capture_output=True)
    stdout, stderr = OUT / (stem + ".stdout"), OUT / (stem + ".stderr")
    stdout.write_bytes(proc.stdout); stderr.write_bytes(proc.stderr)
    inv = {"actualargv": argv, "cwd": str(cwd), "exit_code": proc.returncode,
           "started_at": start, "ended_at": datetime.now(timezone.utc).isoformat(),
           "stdout_ref": ref(stdout), "stderr_ref": ref(stderr), "network_source_capture": False}
    save(OUT / (stem + ".invocation.json"), inv)
    if proc.returncode: raise RuntimeError(stem + " actual exit " + str(proc.returncode))
    return proc.stdout.decode("utf-8")
def packages(text):
    decoder = json.JSONDecoder(); offset = 0
    while offset < len(text):
        while offset < len(text) and text[offset].isspace(): offset += 1
        if offset == len(text): break
        obj, offset = decoder.raw_decode(text, offset)
        yield obj

if __name__ == "__main__":
    owned = [ROOT / "ops/ci/sources.py", ROOT / "tests/sources/check/parent_gate_test.py"]
    before = {str(p.relative_to(ROOT)): digest(p) for p in owned}
    save(OUT / "candidate-source-before.json", before)
    spec = importlib.util.spec_from_file_location("candidate", ROOT / "ops/ci/sources.py")
    gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
    env = dict(os.environ, GOTOOLCHAIN="local", GOENV="off", GOROOT=str(GO.parents[1]),
               GOPROXY="off", GOSUMDB="off", RESEARCHOS_GO=str(GO))
    # Verify native-filtered defaults against the actual MAIN project and its
    # existing cache; candidate code remains solely in this isolated worktree.
    effective = {}; inventories = {}
    for mode in ("fixture", "live"):
        filtered = {k: v for k, v in env.items() if k not in {"GOPATH", "GOCACHE", "GOMODCACHE"}}
        filtered["RESEARCHOS_SOURCE_MODE"] = mode
        with patch.object(gate, "ROOT", MAIN), patch.dict(os.environ, filtered, clear=True):
            gate.prepare_go_environment()
            prepared = dict(os.environ)
        effective[mode] = json.loads(run([str(GO), "env", "-json", "GOPATH", "GOCACHE", "GOMODCACHE", "GOROOT", "GOENV", "GOTOOLCHAIN"], mode + "-go-env", prepared, MAIN))
        output = run([str(GO), "list", "-deps", "-json", "./tests/sources/live"], mode + "-go-list", prepared, MAIN)
        inventories[mode] = sorted((p.get("ImportPath"), p.get("Dir"), p.get("GoFiles", []), p.get("EmbedFiles", [])) for p in packages(output))
    assert effective["fixture"] == effective["live"]
    assert inventories["fixture"] == inventories["live"]
    assert Path(effective["fixture"]["GOPATH"]) == MAIN / ".local/gopath"
    assert Path(effective["fixture"]["GOCACHE"]) == MAIN / ".local/gocache"
    assert Path(effective["fixture"]["GOMODCACHE"]) == MAIN / ".local/gopath/pkg/mod"
    env.update(GOPATH=str(MAIN / ".local/gopath"), GOCACHE=str(MAIN / ".local/gocache"))
    env.pop("GOMODCACHE", None); env.pop("RESEARCHOS_W07_PROOF_REF", None)
    run([sys.executable, "-B", "-X", "utf8", "tests/sources/check/parent_gate_test.py", "-v"], "parent-tests", env)
    env.update(RESEARCHOS_TASK_ID="W07", RESEARCHOS_CHECK_ID="W07-G01", RESEARCHOS_CASE_ID="", RESEARCHOS_SOURCE_MODE="fixture")
    result = json.loads(run([sys.executable, "-B", "-X", "utf8", "ops/ci/sources.py"], "final-fixture-collector", env))
    assert result["status"] == "PASS"
    proof_path = ROOT / result["product_proof_ref"]["path"]
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    capture = proof_path.parent
    snapshot = json.loads((capture / "source-before.json").read_text(encoding="utf-8"))
    assert snapshot == json.loads((capture / "source-after.json").read_text(encoding="utf-8"))
    assert all(snapshot[name] == "sha256:" + digest(ROOT / name) for name in snapshot)
    required = set(); selected = set()
    for p in packages((capture / "go-list.stdout").read_text(encoding="utf-8")):
        directory = Path(p.get("Dir", "")).resolve()
        if directory.is_relative_to(ROOT):
            selected.update((directory / n).relative_to(ROOT).as_posix() for field in ("GoFiles", "CgoFiles", "EmbedFiles") for n in p.get(field, []))
            if directory.relative_to(ROOT).parts[:1] != (".local",):
                required.update(f.relative_to(ROOT).as_posix() for f in directory.glob("*.go") if f.is_file())
    assert (required | selected).issubset(snapshot)
    gaps_path = MAIN / "execution/v2.4/receipts/W07/W07-99/source_executor_codex/current-context-2881cfa84dd64156b59d12795e6375a2/capture-coverage-gaps.json"
    gaps = json.loads(gaps_path.read_text(encoding="utf-8"))
    old_gaps = gaps["missing_from_capture_required_by_profile"]
    assert len(old_gaps) == 27 and set(old_gaps).issubset(snapshot)
    save(OUT / "historical-27-gaps.json", {"original_ref": ref(gaps_path), "paths": old_gaps, "candidate_all_captured": True})
    after = {str(p.relative_to(ROOT)): digest(p) for p in owned}
    save(OUT / "candidate-source-after.json", after)
    assert before == after
    result = {"status": "CANDIDATE_FIXTURE_QUALIFIED", "formal_acceptance": "NOT_ISSUED", "public_source_capture": "NOT_RUN",
              "effective_go_environment": effective, "actual_dependency_inventories_equal": True,
              "local_complete_go_inputs": len(required), "host_unselected_local_go_inputs": sorted(required-selected),
              "captured_source_count": len(snapshot), "historical_27_all_captured": True,
              "source_before_equals_after_and_current": True, "proof_ref": ref(proof_path),
              "candidate_sources": after, "go_ref": ref(GO)}
    save(OUT / "qualification.json", result)
    print(json.dumps(result, ensure_ascii=False))
