"""Root-only, one-use C registration for the frozen revision-12 visual controller.

This file is a candidate. Reading or importing it does not register or launch a run.
Only Root may invoke --register after independent review of the final build binding.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import secrets
import subprocess
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parents[1]
PREP = HERE / "product-v1-native-layout-visual-prepare-12"
CONTROL = HERE / "product-v1-owned-verification-20261104"
OUT = HERE / "product-v1-layout-visual-06-registration"
RUN = HERE / "product-v1-layout-visual-actual-run-06"
OUTER = CONTROL / "scopes/product-v1-layout-visual-06.json"
ROOT = Path("D:/作品集/ResearchOS/research-os")
WT = ROOT / ".local/worktrees/product-v1-build-14-20261105"
BUNDLE = WT / ".local/desktop-v1-build-14"
BUILD_REG = ROOT / "execution/product-v1/receipts/single-harness-20261104/build14-scope/registration.json"
BUILD_BINDING = ROOT / "execution/product-v1/receipts/single-harness-20261104/build14-scope/registration-binding.json"
BUILD_RESULT = CONTROL / "runs/product-v1-build-14/RESULT.json"
BUILD_SCOPE = CONTROL / "scopes/product-v1-build-14.json"
OWNER_SHA = "f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c"
PREP_SHA = "6a7c36a9ed8bc690c1bf4c7215fc45a781dbbc71037fd5a93c1f7f85f0080000"
REVIEW_SHA = "facfdfa3505561fd3b1de8e8402979f64e210a94d3b97541279f087ab139895f"
RUNNER_SHA = "ec13a44461bee8605308b44c1868b94ba905603dbc7a7f04d5860badc2a68e0c"
HELPER_SHA = "c0f1bf7c83fbf4efe5a9eabe2667866a622c0bcb220eb3d128f60c895644edd8"
HEAD = "360c3eefd06ba82255352357c05ece00dae00d3a"
UNION_SHA = "954c293b52e5b83dcb8a779410e89fc3c74a4bad3550d3620ba0938cc67e15c2"
OWNERS = (
    "apps/web/src/components/workbench-layout.jsx", "apps/web/src/workbench.jsx",
    "apps/web/src/workbench.css", "apps/web/src/harness.js", "apps/web/src/screens.jsx",
    "apps/web/src/harness-progress.js", "apps/web/src/activity.js",
    "apps/web/src/components/harness-run-progress.jsx",
    "apps/web/src/components/activity-rail.jsx", "apps/web/src/style.css",
    "apps/web/src/components/app-shell.jsx",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def same(path: Path, digest: str) -> None:
    assert re.fullmatch(r"[0-9a-f]{64}", digest or "") and path.is_file() and sha(path) == digest, str(path)


def write_new(path: Path, obj: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def safe_ref(ref: str) -> bool:
    return (isinstance(ref, str) and ref == PurePosixPath(ref).as_posix()
            and not ref.startswith("/") and "\\" not in ref
            and all(part not in ("", ".", "..") for part in ref.split("/")))


def git_read(cwd: Path, *argv: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "gc.auto=0", "-c", "maintenance.auto=false",
         "--no-optional-locks", *argv], cwd=cwd, stderr=subprocess.STDOUT
    ).decode("utf-8").strip()


def preflight(binding_review: Path) -> tuple[dict, dict, dict, dict, dict, dict]:
    # No output is made before the full static and producer check passes.
    assert not OUT.exists() and not OUTER.exists() and not RUN.exists()
    assert not (CONTROL / "runs/product-v1-layout-visual-06").exists()
    same(CONTROL / "owned_run.py", OWNER_SHA)
    same(PREP / "MANIFEST.json", PREP_SHA)
    same(PREP / "real-electron-flow.mjs", RUNNER_SHA)
    same(PREP / "choose-owned-folder.ps1", HELPER_SHA)
    manifest = read(PREP / "MANIFEST.json")
    assert {row["path"] for row in manifest["files"]} == {
        "real-electron-flow.mjs", "choose-owned-folder.ps1", "scope.template.json",
        "source-selection.template.json", "revision12-purechecks.mjs",
        "interaction-purechecks.mjs", "main-scroll-purechecks.mjs",
        "ancestor-clip-purechecks.mjs", "README.md", "ROOT-SELECTION.json",
    }
    for row in manifest["files"]:
        p = PREP / row["path"]
        same(p, row["sha256"])
        assert p.stat().st_size == row["bytes"]
    review_path = HERE / "product-v1-native-layout-visual12-independent-review-20261105/review-report.json"
    same(review_path, REVIEW_SHA)
    review = read(review_path)
    assert review["decision"] == "APPROVED_SOURCE_FIXTURE_ONLY"
    assert review["candidate_manifest_sha256"] == PREP_SHA
    assert review["candidate_runner_sha256"] == RUNNER_SHA
    assert review["formal_increment"] == review["product_increment"] == 0
    pure_review = HERE / "product-v1-visual12-purechecks01-independent-review-20261105/review-report.json"
    same(pure_review, "428893329a095e15529d878e2420d06bc47187f5751c10ad8f2fe861ca639a0c")
    assert read(pure_review)["decision"] == "PURE_CHECK_RUN_PASSED_AND_OWNED_JOB_STOPPED_NOT_GUI_GEOMETRY_ACCEPTANCE"
    assert binding_review.is_file() and binding_review.resolve().is_relative_to(HERE)
    br = read(binding_review)
    assert br["schema"] == "researchos.visual06-final-binding-review/1"
    assert br["decision"] == "APPROVED_FINAL_BUILD14_VISUAL06_BINDING"
    assert br["source_head"] == HEAD and br["source_union_sha256"] == UNION_SHA
    assert br["controller_manifest_sha256"] == PREP_SHA
    assert br["controller_review_sha256"] == REVIEW_SHA
    assert br["pure_review_sha256"] == sha(pure_review)
    assert br["original_job_controller_sha256"] == OWNER_SHA
    assert br["formal_increment"] == br["product_increment"] == 0

    reg, result, binding = read(BUILD_REG), read(BUILD_RESULT), read(BUILD_BINDING)
    assert reg["main_head"] == HEAD and reg["source_union_sha256"] == UNION_SHA
    assert reg["clean_worktree"] == str(WT) and reg["bundle"] == str(BUNDLE)
    assert git_read(ROOT, "rev-parse", "HEAD") == HEAD
    assert git_read(WT, "rev-parse", "HEAD") == HEAD
    assert not git_read(WT, "diff", "--name-only")
    assert not git_read(WT, "diff", "--cached", "--name-only")
    pins = reg["source_sha256"]
    assert isinstance(pins, dict) and len(pins) == 70
    assert all(safe_ref(ref) and re.fullmatch(r"[0-9a-f]{64}", digest) for ref, digest in pins.items())
    assert set(OWNERS).issubset(pins)
    canonical = json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == UNION_SHA
    assert binding["main_head"] == HEAD and binding["source_union_sha256"] == UNION_SHA
    assert binding["scope_path"] == str(BUILD_SCOPE) and binding["scope_sha256"] == sha(BUILD_SCOPE)
    assert result["scope_sha256"] == binding["scope_sha256"]
    assert result["status"] == "COMPLETED_OWNED_JOB_STOPPED" and result["root_exit_code"] == 0
    assert result["stop_proved"] and result["job_active_zero"] and result["job_assigned"] and result["resumed"]
    assert not result["errors"] and not result["input_drift"] and result["terminate_job_attempts"] == 0
    assert br["build_registration_sha256"] == sha(BUILD_REG)
    assert br["build_binding_sha256"] == sha(BUILD_BINDING)
    assert br["build_result_sha256"] == sha(BUILD_RESULT)
    for ref, digest in pins.items():
        same(WT / ref, digest)
    cp = read(ROOT / "execution/v2.4/checkpoint.json")
    assert cp["current_Main_HEAD"] == HEAD
    mf_path = BUNDLE / "development-manifest.json"
    mf = read(mf_path)
    assert br["bundle_manifest_sha256"] == sha(mf_path)
    assert mf["source"]["head"] == HEAD and mf["source"]["candidate_delta"] == []
    assert mf["bundle_root"] == str(BUNDLE)
    rows = mf["files"]
    assert len({r["path"] for r in rows}) == len(rows)
    for row in rows:
        assert safe_ref(row["path"])
        same(BUNDLE / row["path"], row["sha256"])
        assert (BUNDLE / row["path"]).stat().st_size == row["bytes"]
    actual_files = {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("*") if p.is_file()}
    assert actual_files == {r["path"] for r in rows} | {"development-manifest.json"}
    assert br["selector_source_sha256"] == {ref: pins[ref] for ref in OWNERS}
    assert br["selector_review"] == "ROOT_REVIEWED_FINAL_BUILD14_SELECTORS"
    assert br["source_roles"] == {
        "ui_owners": "11_FINAL_BUILD14_UI_OWNER_PINS_REVIEWED",
        "cli_and_tests": "PINNED_SOURCE_SET_ONLY_NO_GUI_CLI_OR_TEST_ACTIONS",
    }
    cli_tests = {ref: digest for ref, digest in pins.items()
                 if ref.startswith(("apps/cli/", "tests/"))}
    assert cli_tests and br["cli_and_test_source_sha256"] == cli_tests
    compiled = {row["path"]: row["sha256"] for row in rows
                if row["path"].startswith("apps/web/dist/") or row["path"] in {
                    "apps/desktop/main/main.js", "apps/desktop/preload/preload.js",
                    "apps/desktop/resources/control/researchos-control.exe"}}
    assert any(ref.endswith(".js") and ref.startswith("apps/web/dist/assets/") for ref in compiled)
    assert any(ref.endswith(".css") and ref.startswith("apps/web/dist/assets/") for ref in compiled)
    assert br["compiled_snapshot_sha256"] == compiled
    assert br["selection_path_set_sha256"] == hashlib.sha256(
        json.dumps(sorted(pins), ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()
    template = read(PREP / "scope.template.json")
    assert template["node"]["sha256"] == "5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6"
    assert template["windows"]["powershell_sha256"] == "362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139"
    for path, digest in (
        (Path(template["node"]["path"]), template["node"]["sha256"]),
        (Path(template["codex"]["executable"]), template["codex"]["sha256"]),
        (Path(template["windows"]["powershell"]), template["windows"]["powershell_sha256"]),
        (Path(template["playwright"]["inventory_path"]), template["playwright"]["inventory_sha256"]),
        (Path(template["contract_source"]["path"]), template["contract_source"]["sha256"]),
        (Path(template["native_picker"]["validation_warning"]["dismiss_selector"]["evidence_path"]),
         template["native_picker"]["validation_warning"]["dismiss_selector"]["evidence_sha256"]),
        (WT / "apps/desktop/launch-development.mjs", pins["apps/desktop/launch-development.mjs"]),
        (BUNDLE / "runtime/electron/electron.exe", next(r["sha256"] for r in rows if r["path"] == "runtime/electron/electron.exe")),
        (BUNDLE / "apps/desktop/resources/control/researchos-control.exe",
         next(r["sha256"] for r in rows if r["path"] == "apps/desktop/resources/control/researchos-control.exe")),
    ):
        same(path, digest)
    assert template["contract_sha256"] == template["contract_source"]["sha256"]
    assert br["electron_sha256"] == sha(BUNDLE / "runtime/electron/electron.exe")
    assert br["control_sha256"] == sha(BUNDLE / "apps/desktop/resources/control/researchos-control.exe")
    return reg, result, mf, pins, br, review


def register(binding_review: Path) -> None:
    reg, result, mf, pins, br, _ = preflight(binding_review)
    mf_path = BUNDLE / "development-manifest.json"
    selection = dict(schema="researchos.visual06-final-source-selection/1",
                     status="ROOT_VERIFIED_FINAL_BUILD14_SOURCE_SELECTION",
                     source_head=HEAD, bundle_manifest_sha256=sha(mf_path),
                     review="ROOT_INDEPENDENT_FINAL_BUILD14_SOURCE_REVIEW",
                     paths=sorted(pins))
    scope = copy.deepcopy(read(PREP / "scope.template.json"))
    assert scope["status"].startswith("NOT_RUN_") and scope["scope_nonce"] is None
    assert scope["run_root"] is None and scope["source"]["pins"] == []
    assert scope["budget"] == {"task_submissions": 0, "model_calls": 0,
                               "automatic_retries": 0, "harness_id": "codex"}
    scope.update(status="ROOT_APPROVED_REAL_RUN", scope_nonce=secrets.token_hex(24),
                 run_root=str(RUN), product_acceptance="NOT_RUN_BUILD14_VISUAL06_REGISTERED_PENDING_ACTUAL")
    scope["source"].update(head=HEAD, root=str(WT),
        pin_status="ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE",
        pins=[{"path": ref, "sha256": pins[ref]} for ref in sorted(pins)],
        selection_manifest_path=str(OUT / "source-selection.json"))
    scope["bundle"].update(root=str(BUNDLE), manifest_sha256=sha(mf_path),
        source_binding_review="ROOT_VERIFIED_COMPLETE_INTEGRATED_SOURCE",
        electron_sha256=sha(BUNDLE / "runtime/electron/electron.exe"),
        control_sha256=sha(BUNDLE / "apps/desktop/resources/control/researchos-control.exe"))
    scope["launcher"].update(path=str(WT / "apps/desktop/launch-development.mjs"),
                               sha256=pins["apps/desktop/launch-development.mjs"])
    scope["harness"].update(runner_sha256=RUNNER_SHA, folder_helper_sha256=HELPER_SHA)
    scope["selector_binding"].update(source_head=HEAD, bundle_manifest_sha256=sha(mf_path),
         independent_review="ROOT_REVIEWED_FINAL_BUILD14_SELECTORS",
         source_sha256={ref: pins[ref] for ref in OWNERS})
    scope["native_picker"]["validation_warning"]["source_sha256"] = pins["internal/host/native_folder_windows.go"]
    scope["root_supervision"]["controller_sha256"] = OWNER_SHA
    assert scope["formal_increment"] == scope["product_increment"] == 0
    assert scope["visual_profile"]["first_screen_composer"] == "FULL_FORM_TEXTAREA_AND_SEND_VISIBLE_AND_HIT_WITH_INITIAL_DOCUMENT_MAIN_TRANSCRIPT_SCROLL_ZERO"
    assert scope["visual_profile"]["reduced_viewport"] == "390x500_DESKTOP_HEIGHT_SIMULATION_NOT_REAL_OS_KEYBOARD"
    assert scope["native_picker"]["input_is_authorization"] is False
    assert scope["native_picker"]["operator_fallback"] is False
    contract = dict(schema="researchos.root-real-flow-launch-contract/1",
        decision="APPROVED_ZERO_MODEL_NATIVE_RESPONSIVE_LAYOUT_OBSERVATION",
        reviewer="codex:/root", controller_sha256=OWNER_SHA,
        independent_review_sha256=sha(binding_review), source_head=HEAD,
        source_union_sha256=UNION_SHA, bundle_manifest_sha256=sha(mf_path),
        runner_sha256=RUNNER_SHA, helper_sha256=HELPER_SHA, run_root=str(RUN),
        task_budget=0, model_budget=0, automatic_retry=0,
        root_supervision="Exact original f13 unnamed Job assigned and membership checked before Resume; original handles retained; no breakaway; bounded outer deadline; final accounting. Runner fields are not kernel proof.",
        directory_policy="Only fresh C owned fixture; real Native Shell chooser invalid warning, valid confirmation and typed Main ACTIVE exact binding. Typed path or chooser closure is not authorization.",
        payment_policy="No capability, task, submit, cancel, auth probe or model path in this zero-budget controller.",
        unknown_policy="No repeated Native post or input after uncertain action. Preserve phase and use original Job accounting.",
        close_policy="Record normal app.close resolution separately from original Job active-process-zero and stop proof.",
        formal_increment=0, product_acceptance_increment=0)

    # All checks and source reads precede the first write. Exclusive creates prevent replay.
    OUT.mkdir()
    write_new(OUT / "source-selection.json", selection)
    scope["source"]["selection_manifest_sha256"] = sha(OUT / "source-selection.json")
    write_new(OUT / "ROOT-LAUNCH-CONTRACT.json", contract)
    scope["root_supervision"]["launch_contract_sha256"] = sha(OUT / "ROOT-LAUNCH-CONTRACT.json")
    write_new(OUT / "real-flow.scope.json", scope)
    outer = copy.deepcopy(read(CONTROL / "scopes/product-v1-desktop-smoke-02.json"))
    outer.update(scope_id="product-v1-layout-visual-06", purpose="gui",
                 authorization="ROOT_REVIEWED_EXACT_COMMAND", controller_sha256=OWNER_SHA,
                 argv=[str(PREP / "real-electron-flow.mjs"), "--execute", "--scope",
                       str(OUT / "real-flow.scope.json"), "--scope-sha256", sha(OUT / "real-flow.scope.json")],
                 cwd=str(PREP), timeout_seconds=360, max_raw_bytes=16 * 1024 * 1024,
                 graceful="none", grace_seconds=0)
    files = [OUT / "real-flow.scope.json", OUT / "ROOT-LAUNCH-CONTRACT.json",
             OUT / "source-selection.json", binding_review, BUILD_REG, BUILD_BINDING,
             BUILD_RESULT, BUILD_SCOPE, mf_path, PREP / "MANIFEST.json",
             HERE / "product-v1-native-layout-visual12-independent-review-20261105/review-report.json",
             HERE / "product-v1-visual12-purechecks01-independent-review-20261105/review-report.json",
             CONTROL / "owned_run.py", Path(scope["playwright"]["inventory_path"]),
             Path(scope["launcher"]["path"]), Path(scope["node"]["path"]),
             Path(scope["codex"]["executable"]), Path(scope["windows"]["powershell"]),
             Path(scope["contract_source"]["path"]),
             Path(scope["native_picker"]["validation_warning"]["dismiss_selector"]["evidence_path"]),
             BUNDLE / "runtime/electron/electron.exe",
             BUNDLE / "apps/desktop/resources/control/researchos-control.exe"]
    files += [PREP / row["path"] for row in read(PREP / "MANIFEST.json")["files"]]
    files += [WT / ref for ref in sorted(pins)]
    unique = {str(p.resolve()).casefold(): p for p in files}
    outer["inputs"] = [{"path": str(p), "sha256": sha(p)} for p in unique.values()]
    write_new(OUTER, outer)
    write_new(OUT / "REGISTRATION.json", dict(status="REGISTERED_NOT_EXECUTED",
        outer_scope_path=str(OUTER), outer_scope_sha256=sha(OUTER),
        inner_scope_sha256=sha(OUT / "real-flow.scope.json"),
        selection_sha256=sha(OUT / "source-selection.json"),
        binding_review_sha256=sha(binding_review), source_head=HEAD,
        source_union_sha256=UNION_SHA, bundle_manifest_sha256=sha(mf_path),
        producer_stop_proved=result["stop_proved"], task_budget=0, model_budget=0,
        formal_increment=0, product_acceptance_increment=0))
    print(json.dumps(read(OUT / "REGISTRATION.json"), ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true", required=True)
    parser.add_argument("--binding-review", type=Path, required=True)
    args = parser.parse_args()
    register(args.binding_review)
