"""Append only exact named renderer evidence, using one raw directory per Electron child."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import psutil

SOURCE = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012")
PACKAGE = Path(r"C:/Users/yqyyds/.codex/researchos-resource-cache/normal-readlane-combined-91218bdd-20261012")
OLD_RAW = SOURCE / ".local/receipts/approved-readlane-combined-20261012/cases/attempt01-http-qualification-renderer"
RAW = SOURCE / ".local/receipts/approved-readlane-renderer-supplement-20261012"
HERE = Path(__file__).resolve().parent
NODE = Path(r"C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe")
ELECTRON = Path(r"D:/作品集/ResearchOS/research-os/apps/desktop/node_modules/electron/dist/electron.exe")
UI = "070e6cda24ec2fadca104873534febcedfb7ddc0"
MAIN = "91218bdd3901bae94a2c1c90521a4d133c59026d"
UI_TREE = "eee694bdad48a45282cf9884f9b5ef21ee0a76e3"
CORE = "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8"
MU = "8dfebe36508ac0c2508735bb866756dab9283e74"
NODE_HASH = "5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6"
ELECTRON_HASH = "8d205e25b40da3ada4a08c92f32bfbd8e8d38edb4bfe443deea77fc9de685bac"
VALIDATOR_HASH = "e9a9ce0e267399f91ee2ea2b3e877049a79f26785c4498fc4f10a3584905ab52"
ORIGINAL_MANIFEST_SHA = "3c71b1c94b830166ddd57506d01da0b5453fe3df79acf7b25c2756110bce9574"
ORIGINAL_COMPOSITION_SHA = "2fb90c81c223f53cb7cb7f8a7d088dcceed18acc551575e38691feb9b5be889f"

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def need(value, why):
    if not value:
        raise RuntimeError(why)

def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd).decode().strip()

def preflight():
    need(not RAW.exists(), "supplement raw already exists")
    need(not (HERE / "renderer-supplement-report.json").exists(), "formal report already exists")
    need(sha(HERE / "manifest.json") == ORIGINAL_MANIFEST_SHA, "original manifest drift")
    need(sha(HERE / "composition.json") == ORIGINAL_COMPOSITION_SHA, "original composition drift")
    need(git(SOURCE, "rev-parse", "HEAD") == UI, "Source HEAD drift")
    need(git(SOURCE, "rev-parse", "HEAD^{tree}") == UI_TREE, "Source tree drift")
    need(subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=SOURCE) == b"", "Source dirty")
    need(sha(NODE) == NODE_HASH and sha(ELECTRON) == ELECTRON_HASH, "locked Node/Electron mismatch")
    descriptor = PACKAGE / "apps/desktop/resources/client-wire/descriptor.json"
    validator = PACKAGE / "apps/desktop/resources/client-wire/researchos-client-wire-validator.exe"
    need(sha(validator) == VALIDATOR_HASH, "package validator mismatch")
    composition = json.loads((HERE / "composition.json").read_bytes())
    rows = {row["path"]: row for row in composition["package_files"]}
    actual = {p.relative_to(PACKAGE).as_posix(): p for p in PACKAGE.rglob("*") if p.is_file()}
    need(len(actual) == len(rows) == 58 and set(actual) == set(rows), "package member census drift")
    for rel, path in actual.items():
        need(sha(path) == rows[rel]["sha256"] and path.stat().st_size == rows[rel]["bytes"], "package member drift: " + rel)
    need(composition["source_vector"] == {"desktop_ui_and_new_validator": UI,
          "core_control_and_verifier_reused": CORE, "mu_sdk": MU}, "vector drift")
    old_invocation = OLD_RAW / "electron.invocation.json"
    old = json.loads(old_invocation.read_bytes())
    need(old["actualargv"][-1] == "--renderer-case=legacy" and old["exit"] == 0, "old shared renderer evidence changed")
    RAW.mkdir(parents=True)
    save(RAW / "preflight.json", {
        "schema": "researchos.cp444-renderer-supplement-preflight.v1",
        "source_commit": UI, "source_tree": UI_TREE, "main_commit": MAIN,
        "package_root": str(PACKAGE), "package_composition": ref(HERE / "composition.json"),
        "original_manifest": ref(HERE / "manifest.json"),
        "source_vector": composition["source_vector"],
        "package_member_count": 58, "package_member_hash_mismatch": 0,
        "locked_node": ref(NODE), "locked_electron": ref(ELECTRON),
        "package_descriptor": ref(descriptor), "package_validator": ref(validator),
        "old_shared_renderer_invocation": ref(old_invocation),
        "old_shared_renderer_kind": "legacy", "old_shared_renderer_pid": old["pid"],
        "old_shared_renderer_raw_limitation_preserved": True,
        "actual_first_use": False, "formal_increment": 0})

def process_observation(node_pid, kind):
    try:
        descendants = psutil.Process(node_pid).children(recursive=True)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return []
    found = []
    for proc in descendants:
        try:
            cmdline = proc.cmdline()
            exe = proc.exe()
            if "--renderer-case=" + kind not in cmdline:
                continue
            if Path(exe).resolve() != ELECTRON.resolve():
                continue
            found.append({"pid": proc.pid, "parent_pid": proc.ppid(),
                          "creation_time_utc": datetime.datetime.fromtimestamp(proc.create_time(), datetime.timezone.utc).isoformat(),
                          "exe": exe, "argv": cmdline, "observed_at_utc": now()})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found

def exact_summary(text, case_name):
    counts = {}
    for key in ("tests", "pass", "fail", "skipped", "cancelled"):
        hits = re.findall(r"^[#ℹ]\s+" + key + r"\s+(\d+)\s*$", text, re.M)
        need(len(hits) == 1, "missing exact TAP summary " + key)
        counts[key] = int(hits[0])
    need(counts["pass"] == 1 and counts["fail"] == counts["cancelled"] == 0 and
         counts["tests"] == counts["skipped"] + 1, "named renderer TAP counts mismatch")
    need("✔ desktop-renderer/" + case_name + "-roundtrip" in text, "target renderer PASS absent")
    other = "legacy" if case_name == "react" else "react"
    need("✔ desktop-renderer/" + other + "-roundtrip" not in text, "other renderer also executed")
    return counts

def run_case(kind):
    case = RAW / kind
    case.mkdir()
    temp = case / "node-temp"
    temp.mkdir()
    env = os.environ.copy()
    env.update(RESEARCHOS_DESKTOP_WIRE_ROOT=str(PACKAGE / "apps/desktop"),
               RESEARCHOS_DESKTOP_CASE_RECEIPT=str(case),
               RESEARCHOS_DESKTOP_ELECTRON=str(ELECTRON), TEMP=str(temp), TMP=str(temp))
    exact = "^desktop-renderer/" + kind + "-roundtrip$"
    argv = [str(NODE), "--test", "--test-concurrency=1", "--test-name-pattern", exact,
            "tests/ui/desktop/http-wire-boundary.test.mjs"]
    out = case / "node.stdout.raw"
    err = case / "node.stderr.raw"
    started = now()
    observed = {}
    with out.open("xb") as stdout, err.open("xb") as stderr:
        child = subprocess.Popen(argv, cwd=SOURCE, env=env, stdout=stdout, stderr=stderr)
        try:
            deadline = time.monotonic() + 120
            while child.poll() is None and time.monotonic() < deadline:
                for row in process_observation(child.pid, kind):
                    observed[row["pid"]] = row
                time.sleep(0.05)
            if child.poll() is None:
                child.kill()
            code = child.wait(timeout=10)
        except BaseException:
            child.kill()
            child.wait(timeout=10)
            raise
    ended = now()
    node = {"argv": argv, "cwd": str(SOURCE), "pid": child.pid,
            "started_at_utc": started, "ended_at_utc": ended, "exit": code,
            "stdout": ref(out), "stderr": ref(err),
            "selected_environment": {k: env[k] for k in (
                "RESEARCHOS_DESKTOP_WIRE_ROOT", "RESEARCHOS_DESKTOP_CASE_RECEIPT",
                "RESEARCHOS_DESKTOP_ELECTRON", "TEMP", "TMP")}}
    save(case / "node.invocation.json", node)
    save(case / "native-process-observations.json", {"schema": "researchos.cp444-native-process-observations.v1",
         "target": kind, "observer": "psutil.process.children recursive polling", "rows": list(observed.values())})
    if code != 0:
        save(HERE / ("renderer-" + kind + ".stopped.json"), {"first_unexpected": node,
             "cause": "Exact named Node case exited nonzero; inspect immutable raw", "formal_acceptance": False})
        raise SystemExit(code)
    stdout_text = out.read_text(encoding="utf-8")
    counts = exact_summary(stdout_text, kind)
    native_invocation = case / "electron.invocation.json"
    native_stdout = case / "electron.stdout"
    native_stderr = case / "electron.stderr"
    need(native_invocation.is_file() and native_stdout.is_file() and native_stderr.is_file(), "native raw missing")
    native = json.loads(native_invocation.read_bytes())
    need(native["actualargv"] == [str(ELECTRON), str(SOURCE / "tests/ui/desktop/http-wire-boundary.test.mjs"),
         "--renderer-case=" + kind], "native exact argv mismatch")
    need(native["cwd"] == str(SOURCE) and native["exit"] == 0 and native["exited"] is True and
         native["stdoutClosed"] is True and native["stderrClosed"] is True, "native close/exit mismatch")
    need(type(native["pid"]) is int and native["pid"] in observed, "native PID or process-creation observation missing")
    need(observed[native["pid"]]["exe"].casefold() == str(ELECTRON).casefold(), "native observed executable mismatch")
    report = {"schema": "researchos.cp444-exact-renderer-native-evidence.v1",
              "kind": kind, "name_pattern": exact, "source_commit": UI,
              "source_vector": {"desktop_ui_and_new_validator": UI,
                                "core_control_and_verifier_reused": CORE, "mu_sdk": MU},
              "package_root": str(PACKAGE),
              "package_validator_sha256": VALIDATOR_HASH,
              "node_invocation": ref(case / "node.invocation.json"), "node_counts": counts,
              "native_invocation": ref(native_invocation),
              "native_stdout": ref(native_stdout), "native_stderr": ref(native_stderr),
              "native_pid": native["pid"], "native_creation": observed[native["pid"]],
              "native_process_observations": ref(case / "native-process-observations.json"),
              "numeric_native_exit": native["exit"],
              "actual_first_use": False, "formal_increment": 0}
    save(case / "case-report.json", report)
    return report

def census():
    rows = [{"path": p.relative_to(RAW).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)}
            for p in sorted(RAW.rglob("*")) if p.is_file()]
    save(RAW / "census.json", {"schema": "researchos.cp444-renderer-supplement-raw-census.v1",
         "root": str(RAW), "self_excluded": True, "member_count": len(rows), "members": rows})

def main():
    preflight()
    reports = []
    for kind in ("react", "legacy"):
        reports.append(run_case(kind))
    census()
    save(HERE / "renderer-supplement-report.json", {
        "schema": "researchos.cp444-renderer-supplement-report.v1",
        "status": "TWO_EXACT_RENDERER_NATIVE_EXITS_OBSERVED",
        "original_manifest": ref(HERE / "manifest.json"),
        "original_shared_raw_limitation": "Original HTTP216 case overwrote React electron files with legacy. Old files are unchanged and retained.",
        "new_raw_root": str(RAW), "raw_census": ref(RAW / "census.json"),
        "package_root": str(PACKAGE), "package_composition": ref(HERE / "composition.json"),
        "source_commit": UI, "source_tree": UI_TREE,
        "source_vector": {"desktop_ui_and_new_validator": UI,
                          "core_control_and_verifier_reused": CORE, "mu_sdk": MU},
        "package_validator_sha256": VALIDATOR_HASH,
        "cases": [{"kind": row["kind"], "case_report": ref(RAW / row["kind"] / "case-report.json"),
                   "native_invocation": row["native_invocation"],
                   "native_stdout": row["native_stdout"], "native_stderr": row["native_stderr"],
                   "native_pid": row["native_pid"], "native_creation": row["native_creation"],
                   "numeric_native_exit": row["numeric_native_exit"]} for row in reports],
        "full_253_rerun": False, "ordinary_gui_launch": False,
        "model_calls": 0, "formal_increment": 0, "parent_acceptance": False})
    print(json.dumps({"status": "TWO_EXACT_RENDERER_NATIVE_EXITS_OBSERVED",
                      "react_pid": reports[0]["native_pid"],
                      "legacy_pid": reports[1]["native_pid"],
                      "census": ref(RAW / "census.json")}, ensure_ascii=False))

if __name__ == "__main__":
    main()
