"""Prepare fresh flow-02 C scopes after separate review; never launch the flow.

This module has no top-level filesystem reads or writes.  Its entry point is
intentionally unusable until build14, a Root postcheck, and an independent
source review exist.  Running it is outside this C-only preparation task.
"""

import argparse
import hashlib
import json
import re
import secrets
from pathlib import Path


C = Path("C:/Users/yqyyds/Documents/Codex/2026-11-04/task")
D = Path("D:/作品集/ResearchOS/research-os")
HERE = Path(__file__).resolve().parent
CONTROL = C / "product-v1-owned-verification-20261104"
BASE = D / "execution/product-v1/receipts/single-harness-20261104/build14-scope"
WT = D / ".local/worktrees/product-v1-build-14-20261105"
BUNDLE = WT / ".local/desktop-v1-build-14"
PRODUCER = BASE / "producer-14"
BUILD_SCOPE = CONTROL / "scopes/product-v1-build-14.json"
BUILD_RESULT = CONTROL / "runs/product-v1-build-14/RESULT.json"
OUT = C / "product-v1-native-synthetic-flow-02-registration"
RUN_ROOT = C / "product-v1-native-synthetic-acceptance-中文-run-02"
SCOPE_ID = "product-v1-native-synthetic-flow-02"
AUTHORITY_SCOPE = CONTROL / "scopes/product-v1-native-synthetic-flow-02.json"
AUTHORITY_RUN = CONTROL / "runs/product-v1-native-synthetic-flow-02"
FIXTURE_ROOT = C / "product-v1-native-qualification-中文-root-01"
FIXTURE_S = FIXTURE_ROOT / "S"
ORIGINAL_HELPER = C / "product-v1-native-helper-build01/buildout/qualification-helper.exe"
HELPER_SHA = "4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef"
F13_SHA = "f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c"
NODE_SHA = "5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6"
CODEX_SHA = "9d563ee4e0441ff9d59d612013e0460ddf8e5709735c2d9f6b98b7ef8ca4eb42"
PWSH_SHA = "362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139"
LAUNCHER_SHA = "63c0b49e5f237f8137baf50909af3269106f697f4a5b98d7307e7650dd4912af"
PREP_RECEIPT_SHA = "e2c78d439d6b7dd69a224350d0f6cc560c98ed8594f163310dce0785c84ae7dc"
CANARIES_RECEIPT_SHA = "1a8affeaefb21738acd929e1ae709e149a4020856ad611a5c368b02842dbb2aa"
NATIVE_WARNING_SHA = "392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423"
ALLOW_SHA = "fb5a1260681aa728b71d87fb40688512acb11cc0e215f204a34fa079acf16816"
WRITE_SHA = "40d994eb11671f554c25dc4746e2336233e92645622e9346281bab9b6e25b916"
HASH = re.compile(r"[0-9a-f]{64}\Z")
SELECTORS = (
    "apps/web/src/workbench.jsx", "apps/web/src/screens.jsx",
    "apps/web/src/workbench.css", "apps/web/src/harness.js",
    "apps/web/src/harness-progress.js",
    "apps/web/src/components/harness-run-progress.jsx",
    "apps/web/src/components/workbench-layout.jsx",
)
PRELAUNCH = (
    "adapters/runtime/codex_qualification_windows.go",
    "adapters/runtime/codex_qualification_capture_windows.go",
    "internal/domain/runtime_harness_windows.go",
)
SNAPSHOT_EXCLUDED = frozenset({
    "apps/cli/main.go", "apps/cli/productv1.go", "apps/cli/productv1_test.go",
    "tests/ui/desktop/harness-workbench.test.mjs",
    "tests/ui/harness-bridge-fixture.cjs",
    "tests/ui/desktop/managed-environment.test.mjs",
    "tests/ui/desktop/assistant-startup.test.mjs",
    "tests/ui/desktop/public-health-bridge.test.mjs",
    "tests/ui/harness-progress.test.mjs",
})


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def pin(path, expected):
    require(HASH.fullmatch(str(expected)) and Path(path).is_file() and sha(path) == expected,
            f"missing or changed pin: {path}")
    return Path(path)


def same(a, b):
    return str(a).replace("/", "\\").casefold() == str(b).replace("/", "\\").casefold()


def put_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def safe_relative(name):
    p = Path(name)
    require(not p.is_absolute() and ".." not in p.parts and len(p.parts) > 0,
            f"unsafe relative path: {name}")
    return p


def source_and_build(postcheck_path, postcheck_sha):
    cp = read(D / "execution/v2.4/checkpoint.json")
    state = read(D / "execution/product-v1/state.json")
    reg = read(BASE / "registration.json")
    binding = read(BASE / "registration-binding.json")
    build_scope_sha = sha(BUILD_SCOPE)
    build_scope = read(BUILD_SCOPE)
    build_result = read(BUILD_RESULT)
    require(reg["status"] == "REGISTERED_NOT_EXECUTED" and
            binding["scope_sha256"] == build_scope_sha and
            same(binding["scope_path"], BUILD_SCOPE) and
            binding["source_union_sha256"] == reg["source_union_sha256"] and
            cp["current_Main_HEAD"] == reg["main_head"] == binding["main_head"] and
            re.fullmatch(r"[0-9a-f]{40}", reg["main_head"]),
            "build14 checkpoint/registration drift")
    pins = reg["source_sha256"]
    require(isinstance(pins, dict) and len(pins) == 70 and
            all(HASH.fullmatch(v or "") for v in pins.values()),
            "exact 70 integrated source pins required")
    union = hashlib.sha256(json.dumps(pins, sort_keys=True,
                                   separators=(",", ":")).encode()).hexdigest()
    require(union == reg["source_union_sha256"], "build14 source union mismatch")
    current = {ref: digest for item in state["integrated_source"]
               for ref, digest in item["source_sha256"].items()}
    require(current == pins, "current integrated source set changed")
    for name, digest in pins.items():
        relative = safe_relative(name)
        pin(WT / relative, digest)
        pin(D / relative, digest)
    require(build_scope["schema"] == "researchos.owned-windows-run/1" and
            build_scope["scope_id"] == "product-v1-build-14" and
            build_scope["purpose"] == "build" and build_scope["controller_sha256"] == F13_SHA and
            build_scope["graceful"] == "none" and build_scope["grace_seconds"] == 0 and
            build_scope["cleanup_seconds"] == 5 and build_scope["timeout_seconds"] == 1200 and
            same(build_scope["cwd"], WT) and
            build_scope["argv"][:4] == ["-B", "-X", "utf8", str(C / "product-v1-build14-prep-rev2-20261105/build_desktop_serial14.py")],
            "build14 original f13 command changed")
    require(build_result["status"] == "COMPLETED_OWNED_JOB_STOPPED" and
            build_result["scope_id"] == "product-v1-build-14" and
            build_result["scope_sha256"] == build_scope_sha and
            build_result["root_exit_code"] == 0 and build_result["stop_proved"] is True and
            build_result["job_active_zero"] is True and
            build_result["input_drift"] is False and build_result["timed_out"] is False and
            build_result["raw_limit_exceeded"] is False and not build_result["errors"] and
            build_result["terminate_job_attempts"] == 0 and
            build_result["terminate_original_root_attempts"] == 0 and
            build_result["automatic_retry"] is False,
            "original build14 Job did not stop cleanly")
    before = read(PRODUCER / "source.before.json")
    require(before == read(PRODUCER / "source.after.json") and
            before["head"] == reg["main_head"] and not before["candidate_delta"],
            "build14 compiled snapshot changed")
    built = {row["path"]: row["sha256"] for row in before["files"]}
    require(len(built) == len(before["files"]) and len(built) == 61 and
            set(pins) - set(built) == SNAPSHOT_EXCLUDED and
            all(built.get(name) == digest for name, digest in pins.items()
                if name not in SNAPSHOT_EXCLUDED),
            "compiled snapshot must be 61 pins plus exactly nine excluded CLI/UI tests")
    producer = read(PRODUCER / "result.json")
    manifest_path = BUNDLE / "development-manifest.json"
    manifest_sha = sha(manifest_path)
    manifest = read(manifest_path)
    post = read(pin(postcheck_path, postcheck_sha))
    require(post["status"] == "BUILD14_COMPLETE_SOURCE_AND_BUNDLE_VERIFIED_NOT_NATIVE_TESTED" and
            post["main_head"] == reg["main_head"] and
            post["scope_sha256"] == build_scope_sha and
            post["original_job_result_sha256"] == sha(BUILD_RESULT) and
            post["manifest_sha256"] == manifest_sha and
            post["source_pins_verified"] == 70 and
            post["source_canaries_unchanged"] is True and
            post["no_force_timeout_or_drift"] is True and
            post["new_app_helper_native_model_calls"] == 0,
            "Root build14 postcheck missing or failed")
    require(producer["status"] == "BUILT_NOT_NATIVE_TESTED" and
            producer["qualification_enabled"] is True and
            producer["source_drift"] is False and
            producer["manifest_sha256"] == manifest_sha and
            same(producer["output"], BUNDLE), "build14 producer mismatch")
    require(manifest["mode"] == "DEVELOPMENT_ONLY_BUILT_NOT_NATIVE_TESTED" and
            manifest["formal_acceptance"] is False and
            manifest["product_acceptance"] is False and
            same(manifest["bundle_root"], BUNDLE) and
            manifest["source"]["head"] == reg["main_head"] and
            not manifest["source"]["candidate_delta"] and
            manifest["source"]["digest"] == before["digest"],
            "build14 bundle source mismatch")
    q = manifest["qualification"]
    require(q["enabled"] is True and q["status"] == "BUILD_BOUND_NOT_NATIVE_TESTED" and
            same(q["root_original"], FIXTURE_ROOT) and
            same(q["source_derived"], FIXTURE_S) and
            same(q["helper_original"], ORIGINAL_HELPER) and
            q["helper_actual_sha256"] == HELPER_SHA and
            q["helper_copied_sha256"] == HELPER_SHA and
            q["helper_linked_sha256"] == "sha256:" + HELPER_SHA,
            "build14 qualification binding mismatch")
    root_symbol = "researchos.local/research-os/internal/host.codexQualificationApprovedRoot"
    helper_symbol = "researchos.local/research-os/internal/host.codexQualificationHelperSHA256"
    require(q["core_linker_values"] == {root_symbol: q["root_original"],
                                        helper_symbol: "sha256:" + HELPER_SHA} and
            manifest["core"]["build_argv"].count("-ldflags") == 1 and
            manifest["core"]["build_argv"][manifest["core"]["build_argv"].index("-ldflags") + 1] == q["core_linker_flags"],
            "build14 Core linker values mismatch")
    rows = manifest["files"]
    require(len(rows) == producer["files"] and
            len({row["path"] for row in rows}) == len(rows), "bundle inventory malformed")
    for row in rows:
        relative = safe_relative(row["path"])
        pin(BUNDLE / relative, row["sha256"])
        require((BUNDLE / relative).stat().st_size == row["bytes"], "bundle byte count changed")
    require({p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("*") if p.is_file()} ==
            {row["path"] for row in rows} | {"development-manifest.json"},
            "bundle has extra or missing files")
    require(sha(BUNDLE / "apps/desktop/resources/control/researchos-control.exe") == manifest["core"]["sha256"] and
            post["core_sha256"] == manifest["core"]["sha256"] and
            post["bundle_files_verified"] == len(rows), "Core or Root inventory mismatch")
    return reg, pins, manifest, manifest_sha, build_scope_sha


def fixed_inputs(review_path, review_sha):
    review = read(pin(review_path, review_sha))
    require(review["decision"] == "APPROVED_SOURCE_FIXTURE_ONLY" and
            review["formal_increment"] == 0 and not review["pending_blockers"],
            "independent flow02 source review absent")
    pin(HERE / "MANIFEST.json", review["candidate_manifest_sha256"])
    for name in ("real-electron-flow.mjs", "choose-owned-folder.ps1",
                 "scope.template.json", "register_flow02.py",
                 "verify-poststop.mjs", "poststop.scope.template.json"):
        pin(HERE / name, review["source_sha256"][name])
    require(review["source_sha256"]["register_flow02.py"] == sha(__file__),
            "registrar self pin mismatch")
    pin(CONTROL / "owned_run.py", F13_SHA)
    pin(FIXTURE_S / "README.md", "bbf19460eb93f739649abce74a96c045bb03dfebe500220d6b1c7c75e768dbb9")
    pin(FIXTURE_S / "probe.txt", "c22341092e51220d3dc26a8a13dbec78b9e65b40096cf1365363cf8471bddfd3")
    pin(FIXTURE_S / "qualification-helper.exe", HELPER_SHA)
    pin(ORIGINAL_HELPER, HELPER_SHA)
    require({p.name for p in FIXTURE_S.iterdir()} ==
            {"README.md", "probe.txt", "qualification-helper.exe"},
            "fixed S is not the untouched three-file fixture")
    require(not any(p.exists() for p in (OUT, RUN_ROOT, AUTHORITY_SCOPE, AUTHORITY_RUN)),
            "flow02 registration, run root, or authority already exists")
    return review


def make_scopes(reg, pins, manifest, manifest_sha, review_path, review_sha,
                postcheck_path, postcheck_sha):
    scope = read(HERE / "scope.template.json")
    runner_sha = sha(HERE / "real-electron-flow.mjs")
    helper_script_sha = sha(HERE / "choose-owned-folder.ps1")
    scope.update(status="ROOT_APPROVED_REAL_RUN", scope_nonce=secrets.token_hex(24),
                 run_root=str(RUN_ROOT), project_display_name="ResearchOS synthetic readonly qualification")
    scope["source"] = {"root": str(WT), "head": reg["main_head"],
                       "union_sha256": reg["source_union_sha256"],
                       "pin_status": "ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE",
                       "pins": [{"path": name, "sha256": pins[name]} for name in sorted(pins)]}
    scope["bundle"] = {"root": str(BUNDLE), "manifest_sha256": manifest_sha,
                       "electron_sha256": sha(BUNDLE / "runtime/electron/electron.exe"),
                       "control_sha256": manifest["core"]["sha256"],
                       "source_binding_review": "ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE"}
    scope["launcher"] = {"path": str(WT / "apps/desktop/launch-development.mjs"),
                         "sha256": LAUNCHER_SHA}
    scope["node"] = {"path": "C:/nvm4w/nodejs/node.exe", "sha256": NODE_SHA}
    scope["codex"] = {"executable": "C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe",
                      "sha256": CODEX_SHA,
                      "version_evidence": "0.166.0 image only; fresh typed ChatGPT capability is mandatory"}
    scope["harness"] = {"runner_sha256": runner_sha, "folder_helper_sha256": helper_script_sha}
    scope["selector_binding"] = {"source_head": reg["main_head"],
                                  "bundle_manifest_sha256": manifest_sha,
                                  "source_sha256": {name: pins[name] for name in SELECTORS}}
    warning = scope["native_picker"]["validation_warning"]
    warning["source_sha256"] = pins["internal/host/native_folder_windows.go"]
    warning["status"] = "ROOT_FRESH_SOURCE3_WARNING_PINNED"
    q = scope["qualification"]
    q.update(status="ROOT_REVIEWED_SOURCE3_BINDING", root=str(FIXTURE_ROOT),
             synthetic_source=str(FIXTURE_S), build_binding_sha256=manifest_sha,
             prelaunch_intent_gate="INTEGRATED_REVIEWED_HOST_DURABLE_PREPARED_BEFORE_NATIVE",
             allowed_additions={"allow.txt": ALLOW_SHA, "write-existing.txt": WRITE_SHA},
             prelaunch_source_pins={name: pins[name] for name in PRELAUNCH},
             final_receipt_path=None, final_receipt_sha256=None)
    scope["execution_gate"] = "ROOT_REVIEWED_EXACT_ONE_SHOT_CONDITIONAL_REAL_RUN"
    require(scope["budget"] == {"task_submissions": 1, "native_qualification_processes": 1,
                                  "rpc_appserver_processes": 1, "new_user_turns": 1,
                                  "cancel_control_actions": 1, "model_calls": 1,
                                  "automatic_retries": 0, "harness_id": "codex"} and
            scope["deadlines"] == {"flow_ms": 1050000, "picker_ms": 60000,
                                    "cancel_wait_ms": 30000, "close_ms": 30000} and
            scope["root_supervision"]["outer_deadline_ms"] == 1200000,
            "one-shot budget or deadline changed")
    for path, digest in ((scope["contract_path"], scope["contract_sha256"]),
                         (scope["node"]["path"], NODE_SHA),
                         (scope["codex"]["executable"], CODEX_SHA),
                         (scope["windows"]["powershell"], PWSH_SHA),
                         (scope["launcher"]["path"], LAUNCHER_SHA),
                         (scope["playwright"]["inventory_path"], scope["playwright"]["inventory_sha256"]),
                         (q["preparation_receipt_path"], PREP_RECEIPT_SHA),
                         (q["canaries_receipt_path"], CANARIES_RECEIPT_SHA),
                         (warning["dismiss_selector"]["evidence_path"], NATIVE_WARNING_SHA)):
        pin(path, digest)
    sdk = read(scope["playwright"]["inventory_path"])
    require(scope["playwright"]["version"] == sdk["version"] == "1.62.1" and
            same(sdk["root"], scope["playwright"]["root"]) and
            len(sdk["files"]) == 111, "reviewed SDK inventory mismatch")
    sdk_root = Path(sdk["root"])
    for row in sdk["files"]:
        relative = safe_relative(row["path"])
        pin(sdk_root / relative, row["sha256"])
        require((sdk_root / relative).stat().st_size == row["bytes"], "SDK bytes changed")
    require({p.relative_to(sdk_root).as_posix() for p in sdk_root.rglob("*") if p.is_file()} ==
            {row["path"] for row in sdk["files"]}, "SDK has extra or missing files")
    scope["root_supervision"]["controller_sha256"] = F13_SHA
    contract = {"schema": "researchos.root-real-flow-launch-contract/1",
                "decision": "APPROVED_ONE_FRESH_CONDITIONAL_SYNTHETIC_RUN",
                "scope_id": SCOPE_ID, "reviewer": "codex:/root",
                "controller_sha256": F13_SHA, "source_review_sha256": review_sha,
                "build_postcheck_sha256": postcheck_sha,
                "source_head": reg["main_head"], "source_pin_count": 70,
                "source_union_sha256": reg["source_union_sha256"],
                "bundle_manifest_sha256": manifest_sha, "runner_sha256": runner_sha,
                "folder_helper_sha256": helper_script_sha,
                "poststop_verifier_sha256": sha(HERE / "verify-poststop.mjs"),
                "poststop_scope_template_sha256": sha(HERE / "poststop.scope.template.json"),
                "run_root": str(RUN_ROOT), "synthetic_source": str(FIXTURE_S),
                "budgets": scope["budget"], "confirmed_historical_host_task_submissions": 2,
                "prior_flow01": "CONSUMED_FAILED_BEFORE_MODEL_JOB_FORCED_STOPPED",
                "automatic_retry": 0,
                "native_model_readiness": "FRESH_TYPED_LOGGED_IN_CHATGPT_AND_REAL_CONTROLS_REQUIRED",
                "source_policy": "Only fixed synthetic S; README and probe prompt, no canary; no credential or outside path reads",
                "result_policy": "UNKNOWN, FAILED, cancel-requested or no assistant stops new submissions; original request retained",
                "poststop_policy": "Revised verifier must be separately scoped after original f13 Job stop; registrar does not run verifier",
                "formal_increment": 0, "product_acceptance_increment": 0}
    return scope, contract


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--review-sha256", required=True)
    parser.add_argument("--build-postcheck", type=Path, required=True)
    parser.add_argument("--build-postcheck-sha256", required=True)
    args = parser.parse_args()
    fixed_inputs(args.review, args.review_sha256)
    reg, pins, manifest, manifest_sha, _ = source_and_build(args.build_postcheck,
                                                              args.build_postcheck_sha256)
    scope, contract = make_scopes(reg, pins, manifest, manifest_sha,
                                  args.review, args.review_sha256,
                                  args.build_postcheck, args.build_postcheck_sha256)
    require(not any(p.exists() for p in (OUT, RUN_ROOT, AUTHORITY_SCOPE, AUTHORITY_RUN)),
            "flow02 ceased to be fresh")
    OUT.mkdir()
    contract_path = OUT / "ROOT-LAUNCH-CONTRACT.json"
    put_new(contract_path, contract)
    scope["root_supervision"]["launch_contract_sha256"] = sha(contract_path)
    inner_path = OUT / "real-flow.scope.json"
    put_new(inner_path, scope)
    input_paths = [Path(__file__), args.review, args.build_postcheck,
                   HERE / "real-electron-flow.mjs", HERE / "choose-owned-folder.ps1",
                   HERE / "scope.template.json", BUILD_SCOPE, BUILD_RESULT,
                   BASE / "registration.json", BASE / "registration-binding.json",
                   PRODUCER / "result.json", PRODUCER / "source.before.json",
                   PRODUCER / "source.after.json", BUNDLE / "development-manifest.json",
                   BUNDLE / "runtime/electron/electron.exe",
                   BUNDLE / "apps/desktop/resources/control/researchos-control.exe",
                   BUNDLE / "apps/desktop/resources/control/native-qualification/qualification-helper.exe",
                   contract_path, inner_path, CONTROL / "owned_run.py",
                   Path(scope["node"]["path"]), Path(scope["codex"]["executable"]),
                   Path(scope["windows"]["powershell"]),
                   Path(scope["playwright"]["inventory_path"]),
                   Path(scope["launcher"]["path"]), Path(scope["contract_path"]),
                   ORIGINAL_HELPER, FIXTURE_S / "README.md", FIXTURE_S / "probe.txt",
                   FIXTURE_S / "qualification-helper.exe",
                   Path(scope["qualification"]["preparation_receipt_path"]),
                   Path(scope["qualification"]["canaries_receipt_path"]),
                   Path(scope["native_picker"]["validation_warning"]["dismiss_selector"]["evidence_path"]]
    input_paths.extend(WT / name for name in sorted(pins))
    input_paths = list(dict.fromkeys(input_paths))
    outer = {"schema": "researchos.owned-windows-run/1", "scope_id": SCOPE_ID,
             "purpose": "gui", "authorization": "ROOT_REVIEWED_EXACT_COMMAND",
             "controller_sha256": F13_SHA, "executable": scope["node"]["path"],
             "executable_sha256": NODE_SHA,
             "argv": [str(HERE / "real-electron-flow.mjs"), "--execute", "--scope",
                      str(inner_path), "--scope-sha256", sha(inner_path)],
             "cwd": str(HERE), "timeout_seconds": 1200,
             "graceful": "none", "grace_seconds": 0, "cleanup_seconds": 5,
             "process_limit": 48, "memory_mib": 6144, "max_raw_bytes": 16 * 1024 * 1024,
             "env": {},
             "inputs": [{"path": str(path), "sha256": sha(path)} for path in input_paths]}
    put_new(AUTHORITY_SCOPE, outer)
    (OUT / "outer.scope.review-copy.json").write_bytes(AUTHORITY_SCOPE.read_bytes())
    require(sha(OUT / "outer.scope.review-copy.json") == sha(AUTHORITY_SCOPE),
            "outer review copy differs")
    put_new(OUT / "REGISTRATION.json",
            {"status": "REGISTERED_NOT_EXECUTED", "scope_id": SCOPE_ID,
             "outer_scope_path": str(AUTHORITY_SCOPE), "outer_scope_sha256": sha(AUTHORITY_SCOPE),
             "inner_scope_path": str(inner_path), "inner_scope_sha256": sha(inner_path),
             "launch_contract_sha256": sha(contract_path), "source_head": reg["main_head"],
             "source_pin_count": 70, "source_union_sha256": reg["source_union_sha256"],
             "bundle_manifest_sha256": manifest_sha, "run_root": str(RUN_ROOT),
             "run_root_created": False, "confirmed_historical_host_task_submissions": 2,
             "actual_task_submissions_by_registrar": 0, "actual_model_calls_by_registrar": 0,
             "formal_increment": 0, "product_acceptance_increment": 0})
    print(json.dumps({"status": "REGISTERED_NOT_EXECUTED", "scope_id": SCOPE_ID,
                      "outer_scope_sha256": sha(AUTHORITY_SCOPE)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
