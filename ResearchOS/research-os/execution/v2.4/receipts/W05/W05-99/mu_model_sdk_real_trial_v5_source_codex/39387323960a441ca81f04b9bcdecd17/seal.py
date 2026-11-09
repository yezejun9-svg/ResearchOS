"""Exclusive evidence seal for the source-only SDK v5 proposal."""
import ast
import difflib
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path("D:/作品集/ResearchOS/research-os")
HERE = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17"
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v4_source_codex/87c5a05ce5054e3c9ffa2f62ba898c57"
REVIEW = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v4_independent_source_review_codex/89c2e725513f4a5c8278433c617b6ad1/review.json"


def ref(path):
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def dump(name, payload):
    path = HERE / name
    raw = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(raw)
    assert path.read_bytes() == raw
    return ref(path)


old_runner = OLD / "mu_sdk_trial.v4.proposed.py"
new_runner = HERE / "mu_sdk_trial.v5.final.proposed.py"
old_cli = ROOT / "apps/cli/cli_stream.go"
new_cli = HERE / "cli_stream.context_receipt.v5.proposed.go"
assert ref(old_runner)["sha256"] == "216d7a68504a4d0028028627a39e029060b3299dfc81c2347eb53d97501e6def"
assert ref(REVIEW)["sha256"] == "51ec7c9267853a9eae39301099e75b9fd8faac36e66f561d67635ea797092831"
assert ref(OLD / "handoff.json")["sha256"] == "62de783e7f4bfe86d1b00659477dc121100ac69d54661c2f019f848a5fae2afd"
runner_diff = "".join(difflib.unified_diff(
    old_runner.read_text(encoding="utf-8").splitlines(keepends=True),
    new_runner.read_text(encoding="utf-8").splitlines(keepends=True),
    fromfile="v4/mu_sdk_trial", tofile="v5/mu_sdk_trial"))
cli_diff = "".join(difflib.unified_diff(
    old_cli.read_text(encoding="utf-8").splitlines(keepends=True),
    new_cli.read_text(encoding="utf-8").splitlines(keepends=True),
    fromfile="Main/apps/cli/cli_stream.go", tofile="v5/cli_stream.go"))
with (HERE / "runner.v4-to-v5.diff").open("xb") as stream:
    stream.write(runner_diff.encode("utf-8"))
with (HERE / "cli_stream.main-to-v5.diff").open("xb") as stream:
    stream.write(cli_diff.encode("utf-8"))
old_tree = ast.parse(old_runner.read_text(encoding="utf-8"))
new_tree = ast.parse(new_runner.read_text(encoding="utf-8"))
old_defs = {n.name: ast.dump(n, include_attributes=False) for n in old_tree.body if isinstance(n, ast.FunctionDef)}
new_defs = {n.name: ast.dump(n, include_attributes=False) for n in new_tree.body if isinstance(n, ast.FunctionDef)}
changed = sorted(k for k in old_defs.keys() & new_defs.keys() if old_defs[k] != new_defs[k])
added = sorted(new_defs.keys() - old_defs.keys())
assert changed == ["after_child_consumed_states", "command_once"]
assert added == ["verified_cli_context_transition"]
go_pairs = []
for name in ("internal_host_vault.v4.proposed.go", "internal_host_host.v4.proposed.go",
             "apps_control_main.v4.proposed.go", "runtime_qualification.unlimited.v5.proposed.go"):
    candidate = HERE / name.replace(".v4.proposed.go", ".v5.proposed.go")
    original = OLD / name
    assert original.read_bytes() == candidate.read_bytes()
    go_pairs.append({"prior": ref(original), "candidate": ref(candidate)})
assert (OLD / "input.v4.template.json").read_bytes() == (HERE / "input.v5.template.json").read_bytes()
check = json.loads((HERE / "precheck.v5.final.json").read_bytes())
assert check["all_passed"] and len(check["checks"]) == 27
inverse_ref = dump("source-inverse.final.json", {
    "schema": "researchos.mu-sdk-v5-source-inverse.v1", "prior_runner": ref(old_runner),
    "final_runner": ref(new_runner), "main_cli": ref(old_cli), "proposed_cli": ref(new_cli),
    "runner_diff_ref": ref(HERE / "runner.v4-to-v5.diff"),
    "cli_diff_ref": ref(HERE / "cli_stream.main-to-v5.diff"),
    "changed_runner_definitions": changed, "added_runner_definitions": added,
    "unchanged_runner_definitions": len(old_defs) - len(changed),
    "four_go_byte_identical": go_pairs,
    "template_byte_identical": True,
    "restoration": "Restore exact prior_runner and main_cli byte refs; the four Go proposal bytes and input template are identical to v4. Intermediate v5 runner/build-result are superseded by final_runner."})
origins = [ref(HERE / "tool-failure-origin-001.json"),
           ref(HERE / "tool-failure-origin-002.json")]
report_ref = dump("report.final.json", {
    "schema": "researchos.mu-sdk-trial-v5-source-report.v1", "decision": "SOURCE_PREPARATION_ONLY",
    "review_basis": ref(REVIEW), "v4_handoff": ref(OLD / "handoff.json"),
    "r01_v4": "CLOSED_STATIC_PROPOSAL_ONLY",
    "changed_behavior": "A successful goal/run can persist exactly five session-context fields only when one original JSONL row, the admitted operation result, the last verified session.get snapshot, the successful saveCLIContext receipt, and the exact postimage agree. An unchanged byte image also requires the same receipt. Original before/after raw config bytes are exported for both verbs and repinned before a next child.",
    "producer_delta": "Proposed cli_stream.go records the last scope-validated session.get snapshot and emits the actual persisted cliConfig context only after saveCLIContext returns success. Existing CLI JSONL fields and error path remain intact.",
    "negative_controls": "Foreign project/session/writer, revision/epoch, workspace/model/config_revision, missing snapshot and save failure are rejected in synthetic pure IO; no source/CLI/model execution occurred.",
    "preserved": ["v3 R02 qualification binding", "v3 R04 pre-initialization isolation",
                  "v4 exact binary/discovery/config byte guards", "v4 native first-cause precedence",
                  "Root absolute 300s deadline", "three provider requests and 8192 requested output tokens"],
    "main_modified": False, "canonical_modified": False, "actual_cli_runs": 0,
    "actual_provider_requests": 0, "formal_case_accepted_delta": 0,
    "source_acceptance": False, "actual_root_authority": None,
    "required_future_adoption": "Review and integrate the new cli_stream.go producer, build/pin its actual CLI binary, then grant a fresh isolated Root run. The current Main binary cannot supply the final context receipt.",
    "pure_io_precheck": ref(HERE / "precheck.v5.final.json"),
    "inverse_ref": inverse_ref, "failure_origins_new": origins,
    "inherited_v4_failure_ref": ref(OLD / "tool-failure-origin-001.json")})
members = []
for path in sorted(HERE.iterdir(), key=lambda p: p.name):
    if path.is_file() and path.name not in ("manifest.json", "handoff.json"):
        members.append(ref(path))
manifest_ref = dump("manifest.json", {"schema": "researchos.mu-sdk-v5-source-manifest.v1",
                                      "actor_id": "codex:/root/live_resource_lookup", "members": members,
                                      "original_registration_manifests_unchanged": True,
                                      "source_acceptance": False})
handoff_ref = dump("handoff.json", {"schema": "researchos.mu-sdk-v5-source-handoff.v1",
                                    "status": "STOPPED_AFTER_SEAL", "decision": "SOURCE_PREPARATION_ONLY",
                                    "report_ref": report_ref, "manifest_ref": manifest_ref,
                                    "runner_ref": ref(new_runner), "cli_producer_ref": ref(new_cli),
                                    "inverse_ref": inverse_ref,
                                    "precheck_ref": ref(HERE / "precheck.v5.final.json"),
                                    "go_refs": go_pairs, "failure_origins_new": origins,
                                    "actual_authority": None, "actual_provider_requests": 0,
                                    "formal_case_accepted_delta": 0, "source_acceptance": False})
print(json.dumps({"report": report_ref, "manifest": manifest_ref, "handoff": handoff_ref,
                  "new_origins": origins}, ensure_ascii=False))
