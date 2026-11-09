"""Prepare one reviewed C-only registration. Importing this module has no effects.

The registrar is deliberately not invoked during candidate preparation. A separate
source review must pin this file before Root may run its guarded entry point.
"""

import argparse
import hashlib
import json
import re
import secrets
from pathlib import Path


C = Path("C:/Users/yqyyds/Documents/Codex/2026-11-04/task")
D = Path("D:/作品集/ResearchOS/research-os")
BASE = D / "execution/product-v1/receipts/single-harness-20261104"
CONTROL = C / "product-v1-owned-verification-20261104"
PREP = C / "product-v1-native-conditional-controller-prep-02"
OUT = C / "product-v1-native-synthetic-flow-01-registration"
AUTHORITY_SCOPE = CONTROL / "scopes/product-v1-native-synthetic-flow-01.json"
AUTHORITY_RUN = CONTROL / "runs/product-v1-native-synthetic-flow-01"
RUN_ROOT = C / "product-v1-native-synthetic-acceptance-中文-run-01"
WT = D / ".local/worktrees/product-v1-build-13-20261105"
BUNDLE = WT / ".local/desktop-v1-build-13"
BUILD = BASE / "build13-scope"
BUILD_SCOPE = CONTROL / "scopes/product-v1-build-13-effective-v1.json"
BUILD_RESULT = CONTROL / "runs/product-v1-build-13/RESULT.json"
BUILD_POSTCHECK = C / "product-v1-build13-root-postcheck.json"
PRODUCER = BUILD / "producer-13"
PREP_REVIEW = C / "product-v1-native-conditional-controller-security-review-02/REVIEW.json"
POSTSTOP_REVIEW = C / "product-v1-native-conditional-poststop-security-review-02/REVIEW.json"
FIXTURE_ROOT = C / "product-v1-native-qualification-中文-root-01"
FIXTURE_S = FIXTURE_ROOT / "S"
ORIGINAL_HELPER = C / "product-v1-native-helper-build01/buildout/qualification-helper.exe"
HELPER_SHA = "4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef"
PREP_MANIFEST_SHA = "fe170d50bff675c3c69f37d4815562bc65f09a0f918a2a2ab3b1b091acde45a0"
PREP_REVIEW_SHA = "57b36a7b3ac0953aff7fecb48c35ba781103f87284df6b5f1de660a39fd4f520"
POSTSTOP_REVIEW_SHA = "dc2b7cfb98615d2341b8c73ba7817e6607eb644acd4e25b57c8b436b89f02bf5"
PREP_RUNNER_SHA = "746e1ff326a964904461902aa5980f9a9fdcfb619c5b1bef5ad65e52d9437587"
PREP_HELPER_SHA = "0e35560caa3ce5e9eb1af03314c67e9ea615c071758fd887139b4b02579a568e"
BUILD_SCOPE_SHA = "478fc79a6a70383714fb2f129b8ff1bcf95be2223a991f97e39ba2e227bc0275"
BUILD_POSTCHECK_SHA = "0e15693b7e53607d05de49b5d95c5394865369882e23e5f8885eb2b5f4286f1b"
EXPECTED_HEAD = "998fc6330ba735056cd31f8ebf68dd50a8251c1b"
ALLOW_SHA = "fb5a1260681aa728b71d87fb40688512acb11cc0e215f204a34fa079acf16816"
WRITE_SHA = "40d994eb11671f554c25dc4746e2336233e92645622e9346281bab9b6e25b916"
PREP_RECEIPT_SHA = "e2c78d439d6b7dd69a224350d0f6cc560c98ed8594f163310dce0785c84ae7dc"
CANARIES_RECEIPT_SHA = "1a8affeaefb21738acd929e1ae709e149a4020856ad611a5c368b02842dbb2aa"
NATIVE_WARNING_SHA = "392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423"
NODE_SHA = "5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6"
LAUNCHER_SHA = "63c0b49e5f237f8137baf50909af3269106f697f4a5b98d7307e7650dd4912af"
CODEX_SHA = "9d563ee4e0441ff9d59d612013e0460ddf8e5709735c2d9f6b98b7ef8ca4eb42"
PWSH_SHA = "362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139"
F13_SHA = "f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c"
HASH = re.compile(r"[0-9a-f]{64}\Z")
SELECTORS = (
    "apps/web/src/workbench.jsx", "apps/web/src/screens.jsx",
    "apps/web/src/workbench.css", "apps/web/src/harness.js",
    "apps/web/src/harness-progress.js",
    "apps/web/src/components/harness-run-progress.jsx",
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


def require(value, explanation):
    if not value:
        raise RuntimeError(explanation)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned(path, expected):
    require(HASH.fullmatch(str(expected)) is not None, f"bad digest pin: {path}")
    require(digest(path) == expected, f"changed input: {path}")
    return Path(path)


def read(path):
    return json.loads(Path(path).read_bytes())


def write_new(path, data):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def folded(path):
    return str(path).replace("/", "\\").casefold()


def fixed_inputs():
    """All prior documents are observations; none resets a global task counter."""
    review = read(pinned(PREP_REVIEW, PREP_REVIEW_SHA))
    pinned(PREP / "MANIFEST.json", PREP_MANIFEST_SHA)
    require(review["decision"] == "APPROVED_SOURCE_FIXTURE_ONLY"
            and review["candidate_manifest_sha256"] == PREP_MANIFEST_SHA
            and review["formal_increment"] == 0 and not review["pending_blockers"],
            "controller source review is not approved")
    for name, expected in review["source_sha256"].items():
        pinned(PREP / name, expected)
    pinned(PREP / "real-electron-flow.mjs", PREP_RUNNER_SHA)
    pinned(PREP / "choose-owned-folder.ps1", PREP_HELPER_SHA)
    post = read(pinned(POSTSTOP_REVIEW, POSTSTOP_REVIEW_SHA))
    require(post["decision"] == "APPROVED_SOURCE_FIXTURE_ONLY"
            and post["formal_increment"] == 0 and not post["pending_blockers"],
            "poststop source review is not approved")
    require(post["production_bindings"]["reviewed_controller_runner"] == PREP_RUNNER_SHA,
            "poststop review is for another controller")
    # The poststop verifier is not launched, imported, or run by this registrar.
    pinned(FIXTURE_S / "README.md", "bbf19460eb93f739649abce74a96c045bb03dfebe500220d6b1c7c75e768dbb9")
    pinned(FIXTURE_S / "probe.txt", "c22341092e51220d3dc26a8a13dbec78b9e65b40096cf1365363cf8471bddfd3")
    pinned(FIXTURE_S / "qualification-helper.exe", HELPER_SHA)
    pinned(ORIGINAL_HELPER, HELPER_SHA)
    require({p.name for p in FIXTURE_S.iterdir()} ==
            {"README.md", "probe.txt", "qualification-helper.exe"},
            "qualification S is not the untouched three-file fixture")
    for name in ("allow.txt", "write-existing.txt", "create-denied.txt"):
        require(not (FIXTURE_S / name).exists(), "qualification S has a consumed outcome")
    require(not any(path.exists() for path in (OUT, RUN_ROOT, AUTHORITY_SCOPE, AUTHORITY_RUN)),
            "registration, authority scope, prior run, or fresh GUI root already exists")
    return review, post


def verified_build():
    cp = read(D / "execution/v2.4/checkpoint.json")
    reg = read(BUILD / "registration.json")
    effective = read(BUILD / "registration.effective-v1.json")
    scope = read(pinned(BUILD_SCOPE, BUILD_SCOPE_SHA))
    require(cp["revision"] >= 681 and cp["current_Main_HEAD"] == EXPECTED_HEAD,
            "current Main no longer matches build13")
    require(reg["main_head"] == EXPECTED_HEAD and reg["scope_sha256"] == effective["original_scope_sha256"]
            and effective["scope_sha256"] == BUILD_SCOPE_SHA
            and folded(effective["scope_path"]) == folded(BUILD_SCOPE),
            "build13 registration mismatch")
    require(folded(reg["scope_path"]) == folded(effective["original_scope_path"]),
            "original build13 scope was replaced")
    pinned(reg["scope_path"], effective["original_scope_sha256"])
    pins = reg["source_sha256"]
    require(isinstance(pins, dict) and len(pins) == 67 and all(HASH.fullmatch(x or "") for x in pins.values()),
            "expected 67 source pins")
    for name, expected in pins.items():
        require(not Path(name).is_absolute() and ".." not in Path(name).parts,
                "unsafe source relative path")
        pinned(WT / name, expected)
    result = read(BUILD_RESULT)
    require(result["status"] == "COMPLETED_OWNED_JOB_STOPPED" and result["root_exit_code"] == 0
            and result["scope_id"] == "product-v1-build-13"
            and result["scope_sha256"] == BUILD_SCOPE_SHA
            and result["stop_proved"] is True and result["job_active_zero"] is True
            and result["input_drift"] is False and result["timed_out"] is False
            and result["raw_limit_exceeded"] is False and not result["errors"]
            and result["terminate_job_attempts"] == 0
            and result["terminate_original_root_attempts"] == 0
            and result["automatic_retry"] is False,
            "original f13 build13 Job completion not proved")
    require(scope["scope_id"] == "product-v1-build-13" and scope["purpose"] == "build"
            and scope["controller_sha256"] == F13_SHA and scope["graceful"] == "none"
            and scope["grace_seconds"] == 0 and scope["cleanup_seconds"] == 5,
            "build13 effective scope mismatch")
    argv = scope["argv"]
    require(argv[:4] == ["-B", "-X", "utf8", str(C / "build_desktop_serial13.py")]
            and digest(argv[3]) == effective["wrapper_sha256"],
            "effective build13 wrapper is not the reviewed wrapper13")
    require(argv[-6:] == ["--qualification-root", str(FIXTURE_ROOT),
                          "--qualification-helper", str(ORIGINAL_HELPER),
                          "--qualification-helper-sha256", HELPER_SHA],
            "build13 was not compiled with exact original helper and S root")
    require("--output" in argv and folded(argv[argv.index("--output") + 1]) == folded(BUNDLE)
            and "--receipts" in argv and folded(argv[argv.index("--receipts") + 1]) == folded(PRODUCER),
            "build13 output or receipt binding mismatch")
    require(folded(scope["cwd"]) == folded(WT), "build13 source worktree mismatch")
    source_before = read(PRODUCER / "source.before.json")
    require(source_before == read(PRODUCER / "source.after.json")
            and source_before["head"] == EXPECTED_HEAD
            and not source_before["candidate_delta"], "build13 source drift")
    built_sources = {row["path"]: row["sha256"] for row in source_before["files"]}
    require(len(built_sources) == len(source_before["files"])
            and set(pins) - set(built_sources) == SNAPSHOT_EXCLUDED
            and len(pins) - len(SNAPSHOT_EXCLUDED) == 58
            and all(built_sources.get(name) == value for name, value in pins.items()
                    if name not in SNAPSHOT_EXCLUDED),
            "registered source pins are not the exact 58 compiled plus 9 excluded source set")
    producer_result = read(PRODUCER / "result.json")
    manifest_path = BUNDLE / "development-manifest.json"
    manifest_sha = digest(manifest_path)
    m = read(manifest_path)
    postcheck = read(pinned(BUILD_POSTCHECK, BUILD_POSTCHECK_SHA))
    require(postcheck["status"] == "BUILD13_COMPLETE_SOURCE_AND_BUNDLE_VERIFIED_NOT_NATIVE_TESTED"
            and postcheck["main_head"] == EXPECTED_HEAD
            and postcheck["scope_sha256"] == BUILD_SCOPE_SHA
            and postcheck["original_job_result_sha256"] == digest(BUILD_RESULT)
            and postcheck["manifest_sha256"] == manifest_sha
            and postcheck["source_pins_verified"] == len(pins)
            and postcheck["source_canaries_unchanged"] is True
            and postcheck["no_force_timeout_or_drift"] is True
            and postcheck["new_app_helper_native_model_calls"] == 0,
            "Root build13 readback is not bound to original stopped build")
    require(producer_result["status"] == "BUILT_NOT_NATIVE_TESTED"
            and producer_result["qualification_enabled"] is True
            and producer_result["source_drift"] is False
            and producer_result["manifest_sha256"] == manifest_sha
            and folded(producer_result["output"]) == folded(BUNDLE),
            "build13 producer receipt mismatch")
    require(m["mode"] == "DEVELOPMENT_ONLY_BUILT_NOT_NATIVE_TESTED"
            and m["formal_acceptance"] is False and m["product_acceptance"] is False
            and folded(m["bundle_root"]) == folded(BUNDLE)
            and m["source"]["head"] == EXPECTED_HEAD
            and not m["source"]["candidate_delta"]
            and m["source"]["digest"] == source_before["digest"],
            "bundle is not the current clean source build")
    q = m["qualification"]
    require(q["enabled"] is True and q["status"] == "BUILD_BOUND_NOT_NATIVE_TESTED"
            and folded(q["root_original"]) == folded(FIXTURE_ROOT)
            and folded(q["source_derived"]) == folded(FIXTURE_S)
            and folded(q["helper_original"]) == folded(ORIGINAL_HELPER)
            and q["helper_actual_sha256"] == HELPER_SHA
            and q["helper_copied_sha256"] == HELPER_SHA
            and q["helper_linked_sha256"] == "sha256:" + HELPER_SHA
            and q["helper_bytes"] == 5335552
            and q["helper_copied_bytes"] == 5335552,
            "build13 Source3 qualification binding mismatch")
    root_symbol = "researchos.local/research-os/internal/host.codexQualificationApprovedRoot"
    helper_symbol = "researchos.local/research-os/internal/host.codexQualificationHelperSHA256"
    require(q["core_linker_values"] == {root_symbol: q["root_original"],
                                          helper_symbol: "sha256:" + HELPER_SHA}
            and q["core_linker_flags"] == (f"-X {root_symbol}={q['root_original']} "
                                            f"-X {helper_symbol}=sha256:{HELPER_SHA}")
            and m["core"]["build_argv"].count("-ldflags") == 1
            and m["core"]["build_argv"][m["core"]["build_argv"].index("-ldflags") + 1] == q["core_linker_flags"],
            "Core does not have exactly two reviewed linker values")
    require(q["original_build"] and
            q["original_build"]["receipt_sha256"]["scope.json"] ==
            "c1aff0bca3d4b7b63edbae04dc2c2538260d4aba64b4c4b1b11e9ad114c85350",
            "prebuilt helper has no bound original f13 scope")
    rows = m["files"]
    require(isinstance(rows, list) and len(rows) == producer_result["files"]
            and len({row["path"] for row in rows}) == len(rows), "bundle inventory invalid")
    for row in rows:
        name = Path(row["path"])
        require(not name.is_absolute() and ".." not in name.parts, "unsafe bundle entry")
        pinned(BUNDLE / name, row["sha256"])
        require((BUNDLE / name).stat().st_size == row["bytes"], "bundle file size changed")
    actual = {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("*") if p.is_file()}
    require(actual == {row["path"] for row in rows} | {"development-manifest.json"},
            "bundle extra or missing files")
    require(digest(BUNDLE / "apps/desktop/resources/control/researchos-control.exe") == m["core"]["sha256"],
            "Core hash mismatch")
    require(postcheck["core_sha256"] == m["core"]["sha256"]
            and postcheck["bundle_files_verified"] == len(rows)
            and postcheck["job_cumulative_processes"] == result["job_total_processes"],
            "Root build13 hash, inventory, or Job accounting changed")
    return pins, m, manifest_sha, result


def make_scopes(pins, m, manifest_sha, registrar_review):
    template = read(PREP / "scope.template.json")
    scope = template
    scope.update(status="ROOT_APPROVED_REAL_RUN", scope_nonce=secrets.token_hex(24),
                 run_root=str(RUN_ROOT), project_display_name="ResearchOS synthetic readonly qualification")
    scope["source"] = {"root": str(WT), "head": EXPECTED_HEAD,
                       "pin_status": "ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE",
                       "pins": [{"path": key, "sha256": pins[key]} for key in sorted(pins)]}
    scope["bundle"] = {"root": str(BUNDLE), "manifest_sha256": manifest_sha,
                       "electron_sha256": digest(BUNDLE / "runtime/electron/electron.exe"),
                       "control_sha256": m["core"]["sha256"],
                       "source_binding_review": "ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE"}
    scope["launcher"] = {"path": str(WT / "apps/desktop/launch-development.mjs"),
                         "sha256": LAUNCHER_SHA}
    scope["node"] = {"path": "C:/nvm4w/nodejs/node.exe", "sha256": NODE_SHA}
    scope["codex"] = {"executable": "C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe",
                      "sha256": CODEX_SHA,
                      "version_evidence": "0.166.0 installed bytes only; fresh typed Host capability required"}
    scope["harness"] = {"runner_sha256": PREP_RUNNER_SHA, "folder_helper_sha256": PREP_HELPER_SHA}
    scope["selector_binding"] = {"source_head": EXPECTED_HEAD, "bundle_manifest_sha256": manifest_sha,
                                  "source_sha256": {key: pins[key] for key in SELECTORS}}
    warning = scope["native_picker"]["validation_warning"]
    warning["source_sha256"] = pins["internal/host/native_folder_windows.go"]
    warning["status"] = "ROOT_FRESH_SOURCE3_WARNING_PINNED"
    warning["dismiss_selector"]["evidence_path"] = str(C / "product-v1-native-path-entry-中文-run-03/receipts/native-folder-automation.json")
    warning["dismiss_selector"]["evidence_sha256"] = NATIVE_WARNING_SHA
    qualification = scope["qualification"]
    qualification.update(status="ROOT_REVIEWED_SOURCE3_BINDING", root=str(FIXTURE_ROOT),
                         synthetic_source=str(FIXTURE_S), build_binding_sha256=manifest_sha,
                         prelaunch_intent_gate="INTEGRATED_REVIEWED_HOST_DURABLE_PREPARED_BEFORE_NATIVE",
                         allowed_additions={"allow.txt": ALLOW_SHA, "write-existing.txt": WRITE_SHA},
                         prelaunch_source_pins={key: pins[key] for key in PRELAUNCH},
                         final_receipt_path=None, final_receipt_sha256=None)
    scope["execution_gate"] = "ROOT_REVIEWED_EXACT_ONE_SHOT_CONDITIONAL_REAL_RUN"
    require(scope["budget"] == {"task_submissions": 1, "native_qualification_processes": 1,
                                  "rpc_appserver_processes": 1, "new_user_turns": 1,
                                  "cancel_control_actions": 1, "model_calls": 1,
                                  "automatic_retries": 0, "harness_id": "codex"},
            "conditional flow budgets changed")
    for path, expected in ((scope["contract_path"], scope["contract_sha256"]),
                           (scope["node"]["path"], NODE_SHA),
                           (scope["codex"]["executable"], CODEX_SHA),
                           (scope["windows"]["powershell"], PWSH_SHA),
                           (scope["playwright"]["inventory_path"], scope["playwright"]["inventory_sha256"]),
                           (scope["native_picker"]["validation_warning"]["dismiss_selector"]["evidence_path"], NATIVE_WARNING_SHA),
                           (scope["launcher"]["path"], scope["launcher"]["sha256"]),
                           (scope["qualification"]["preparation_receipt_path"], PREP_RECEIPT_SHA),
                           (scope["qualification"]["canaries_receipt_path"], CANARIES_RECEIPT_SHA)):
        pinned(path, expected)
    require(scope["playwright"]["version"] == "1.62.1" and scope["windows"]["powershell_sha256"] == PWSH_SHA,
            "SDK or PowerShell pin changed")
    inventory = read(scope["playwright"]["inventory_path"])
    require(inventory["version"] == "1.62.1" and folded(inventory["root"]) == folded(scope["playwright"]["root"]),
            "SDK inventory binding changed")
    sdk_rows = inventory["files"]
    require(len(sdk_rows) == 111 and len({row["path"] for row in sdk_rows}) == 111,
            "SDK inventory must contain the exact reviewed 111 files")
    sdk_root = Path(scope["playwright"]["root"])
    for row in sdk_rows:
        relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "unsafe SDK file name")
        pinned(sdk_root / relative, row["sha256"])
        require((sdk_root / relative).stat().st_size == row["bytes"], "SDK file size changed")
    require({p.relative_to(sdk_root).as_posix() for p in sdk_root.rglob("*") if p.is_file()} ==
            {row["path"] for row in sdk_rows}, "SDK extra or missing file")
    pinned(CONTROL / "owned_run.py", F13_SHA)
    contract = {"schema": "researchos.root-real-flow-launch-contract/1",
                "decision": "APPROVED_ONE_FRESH_CONDITIONAL_SYNTHETIC_RUN",
                "scope_id": "product-v1-native-synthetic-flow-01", "reviewer": "codex:/root",
                "controller_sha256": F13_SHA, "registrar_review_sha256": digest(registrar_review),
                "prep_review_sha256": digest(PREP_REVIEW), "poststop_review_sha256": digest(POSTSTOP_REVIEW),
                "source_head": EXPECTED_HEAD, "source_pin_count": 67,
                "bundle_manifest_sha256": manifest_sha, "runner_sha256": PREP_RUNNER_SHA,
                "helper_sha256": PREP_HELPER_SHA, "run_root": str(RUN_ROOT),
                "qualification_root": str(FIXTURE_ROOT), "synthetic_source": str(FIXTURE_S),
                "budgets": scope["budget"], "prior_cp647_real_task_invocations": 1,
                "prior_cp647_inference": "NOT_CONFIRMED", "automatic_retry": 0,
                "native_model_readiness": "MUST_BE_ESTABLISHED_BY_FRESH_TYPED_CAPABILITY_AND_REAL_CONTROLS",
                "account_policy": "Fresh typed Host LOGGED_IN/chatgpt/CLI_OWNED/workspace-read/write-false/can-submit; no API fallback or credential read",
                "source_policy": "Only fixed synthetic S, README/probe prompt without canary, exact registered helper and build",
                "result_policy": "One new Task and one user turn at most; UNKNOWN/cancel-requested is not success; no resubmit",
                "poststop_policy": "Independent post-stop verifier is not executed by this registrar",
                "formal_increment": 0, "product_acceptance_increment": 0}
    contract_path = OUT / "ROOT-LAUNCH-CONTRACT.json"
    scope["root_supervision"].update(controller_sha256=F13_SHA)
    return scope, contract, contract_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registrar-review", required=True)
    parser.add_argument("--registrar-review-sha256", required=True)
    args = parser.parse_args()
    review_path = Path(args.registrar_review)
    pinned(review_path, args.registrar_review_sha256)
    review = read(review_path)
    require(review["decision"] == "APPROVED_SOURCE_FIXTURE_ONLY"
            and review["formal_increment"] == 0 and not review["pending_blockers"]
            and review["source_sha256"][Path(__file__).name] == digest(__file__),
            "independent registrar source review or self hash mismatch")
    fixed_inputs()
    pins, manifest, manifest_sha, _ = verified_build()
    scope, contract, contract_path = make_scopes(pins, manifest, manifest_sha, review_path)
    require(not any(path.exists() for path in (OUT, RUN_ROOT, AUTHORITY_SCOPE, AUTHORITY_RUN)),
            "registration, authority scope, prior run, or fresh GUI root ceased to be fresh")
    OUT.mkdir()  # Only C registration outputs; actual GUI run root remains absent.
    write_new(contract_path, contract)
    scope["root_supervision"]["launch_contract_sha256"] = digest(contract_path)
    inner_path = OUT / "real-flow.scope.json"
    write_new(inner_path, scope)
    input_paths = [Path(__file__), review_path, PREP_REVIEW, POSTSTOP_REVIEW,
                   PREP / "MANIFEST.json", PREP / "real-electron-flow.mjs",
                   PREP / "choose-owned-folder.ps1", PREP / "scope.template.json",
                   BUILD_SCOPE, BUILD_RESULT, BUILD_POSTCHECK, BUILD / "registration.json",
                   BUILD / "registration.effective-v1.json", PRODUCER / "result.json",
                   PRODUCER / "source.before.json", PRODUCER / "source.after.json",
                   BUNDLE / "development-manifest.json",
                   BUNDLE / "runtime/electron/electron.exe",
                   BUNDLE / "apps/desktop/resources/control/researchos-control.exe",
                   BUNDLE / "apps/desktop/resources/control/native-qualification/qualification-helper.exe",
                   contract_path, inner_path,
                   CONTROL / "owned_run.py", Path(scope["node"]["path"]),
                   Path(scope["codex"]["executable"]), Path(scope["windows"]["powershell"]),
                   Path(scope["playwright"]["inventory_path"]), Path(scope["launcher"]["path"]),
                   Path(scope["contract_path"]), ORIGINAL_HELPER,
                   FIXTURE_S / "README.md", FIXTURE_S / "probe.txt", FIXTURE_S / "qualification-helper.exe",
                   Path(scope["qualification"]["preparation_receipt_path"]),
                   Path(scope["qualification"]["canaries_receipt_path"]),
                   Path(scope["native_picker"]["validation_warning"]["dismiss_selector"]["evidence_path"])]
    input_paths += [WT / name for name in sorted(pins)]
    input_paths = list(dict.fromkeys(input_paths))
    outer = {"schema": "researchos.owned-windows-run/1", "scope_id": "product-v1-native-synthetic-flow-01",
             "purpose": "gui", "authorization": "ROOT_REVIEWED_EXACT_COMMAND",
             "controller_sha256": F13_SHA, "executable": scope["node"]["path"],
             "executable_sha256": NODE_SHA,
             "argv": [str(PREP / "real-electron-flow.mjs"), "--execute", "--scope", str(inner_path),
                      "--scope-sha256", digest(inner_path)],
             "cwd": str(PREP), "timeout_seconds": 690,
             "graceful": "none", "grace_seconds": 0, "cleanup_seconds": 5,
             "process_limit": 48, "memory_mib": 6144, "max_raw_bytes": 16 * 1024 * 1024,
             "env": {}, "inputs": [{"path": str(path), "sha256": digest(path)} for path in input_paths]}
    outer_path = AUTHORITY_SCOPE
    write_new(outer_path, outer)
    review_copy = OUT / "outer.scope.review-copy.json"
    with review_copy.open("xb") as stream:
        stream.write(outer_path.read_bytes())
    require(digest(review_copy) == digest(outer_path), "outer review copy differs from authority scope")
    registration = {"status": "REGISTERED_NOT_EXECUTED", "scope_id": outer["scope_id"],
                    "outer_scope_path": str(outer_path), "outer_scope_sha256": digest(outer_path),
                    "inner_scope_path": str(inner_path), "inner_scope_sha256": digest(inner_path),
                    "launch_contract_sha256": digest(contract_path), "source_head": EXPECTED_HEAD,
                    "source_pin_count": len(pins), "bundle_manifest_sha256": manifest_sha,
                    "run_root": str(RUN_ROOT), "run_root_created": False,
                    "prior_cp647_real_task_invocations": 1, "prior_cp647_inference": "NOT_CONFIRMED",
                    "actual_task_submissions_by_registrar": 0, "actual_model_calls_by_registrar": 0,
                    "formal_increment": 0, "product_acceptance_increment": 0}
    write_new(OUT / "REGISTRATION.json", registration)
    print(json.dumps(registration, ensure_ascii=False))


if __name__ == "__main__":
    main()
