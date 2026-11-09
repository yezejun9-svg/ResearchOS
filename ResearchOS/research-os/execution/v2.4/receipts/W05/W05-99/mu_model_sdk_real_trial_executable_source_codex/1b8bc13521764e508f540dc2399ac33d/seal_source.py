"""Pure IO/AST source receipt sealer. Never imports candidate or invokes product tools."""

import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = Path("D:/作品集/ResearchOS/research-os")
SOURCES = (
    ("internal/domain/runtime_qualification.go", "runtime_qualification.unlimited.v2.proposed.go", "runtime_qualification.unlimited.v2.patch"),
    ("internal/host/vault.go", "internal_host_vault.go.proposed.go", "internal_host_vault.go.patch"),
    ("internal/host/host.go", "internal_host_host.go.proposed.go", "internal_host_host.go.patch"),
    ("apps/control/main.go", "apps_control_main.go.proposed.go", "apps_control_main.go.patch"),
)


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def write_new(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with (HERE / name).open("xb") as out:
        out.write(raw)
    return pin(HERE / name)


candidate = HERE / "mu_sdk_trial.proposed.py"
source = candidate.read_text(encoding="utf-8")
ast.parse(source, filename=str(candidate))
compile(source, str(candidate), "exec", dont_inherit=True)
assert "MAX_PROVIDER_REQUESTS = 3" in source
assert "MAX_WALL_SECONDS = 300" in source
assert "MAX_OUTPUT_TOKENS_PER_REQUEST = 2730" in source
assert "cli, \"run\"" in source and "session.send" in source
assert "urllib" not in source and "requests." not in source
for name in ("input.template.json", "public_route.template.json", "failure-origin-001.json", "failure-origin-002.json", "failure-origin-003.json", "failure-origin-004.json"):
    json.loads((HERE / name).read_text(encoding="utf-8"))

planned_inverse = []
for target, proposal, patch in SOURCES:
    original_path = ROOT / target
    proposed_path = HERE / proposal
    original = original_path.read_text(encoding="utf-8")
    proposed = proposed_path.read_text(encoding="utf-8")
    expected = "".join(difflib.unified_diff(original.splitlines(keepends=True), proposed.splitlines(keepends=True), fromfile="a/" + target, tofile="b/" + target))
    assert expected == (HERE / patch).read_text(encoding="utf-8"), "forward patch differs: " + target
    inverse_text = "".join(difflib.unified_diff(proposed.splitlines(keepends=True), original.splitlines(keepends=True), fromfile="a/" + target, tofile="b/" + target))
    inverse_path = HERE / (proposal + ".inverse.patch")
    assert not inverse_path.exists(), "inverse path already occupied: " + target
    planned_inverse.append((target, original_path, proposed_path, patch, inverse_path, inverse_text))

inverse = []
for target, original_path, proposed_path, patch, inverse_path, inverse_text in planned_inverse:
    with inverse_path.open("xb") as out:
        out.write(inverse_text.encode("utf-8"))
    inverse.append({"target": target, "original": pin(original_path), "candidate": pin(proposed_path), "forward_patch": pin(HERE / patch), "inverse_patch": pin(inverse_path)})

inverse_ref = write_new("source_inverse.json", {"schema": "researchos.mu-sdk-trial.source-inverse.v1", "main_untouched": True, "source_commit_claim": "e2ee22a0", "selected": inverse})
report = {
    "schema": "researchos.mu-sdk-trial.source-report.v1",
    "status": "SOURCE_PREPARATION_ONLY",
    "source_commit_claim": "e2ee22a0",
    "main_modified": False,
    "go_or_product_executed": False,
    "provider_requests_sent": 0,
    "formal_case_accepted": 0,
    "source_acceptance": False,
    "model_route": {"provider": "opencode-go", "model": "deepseek-v4.1-flash", "base_url": "https://opencode.ai/zen/go/v1", "api": "openai-completions", "credential_ref_only": "cred-opencode_go-api_key-1791292735825831100-02e9207a-d97edec4"},
    "limits": {"total_model_requests": 3, "qualification_model_requests": 1, "ordinary_model_requests": 2, "requested_output_tokens_total": 8192, "enforced_requested_output_tokens_per_request": 2730, "total_wall_seconds": 300, "no_retry": True, "workspace_tool": "read:evidence.txt", "tool_calls": 1},
    "money": {"default_policy": "UNLIMITED_AMOUNT", "cap": None, "recorded_operation": "UNKNOWN", "actual_cost": None, "capped_and_strict_reservation_unchanged": True, "old_strict_frozen_scope_reused": False},
    "spec_basis": [
        {"path": "D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/07_OPERATIONS_AND_EVOLUTION.md", "lines": "83-85", "finding": "default UNLIMITED_AMOUNT cap:null, unknown cost recorded; CAPPED needs reliable upper bound and reserve"},
        {"path": "D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/08_AGENT_EXECUTION_GOAL.md", "lines": "111-115", "finding": "authorized resources and finance controls; no new purchase"}
    ],
    "source_chain": ["apps/cli/cli_contract.go:322-415", "apps/cli/cli_verbs.go:148-166", "apps/control/main.go", "adapters/runtime/mu/worker.mjs", "internal/domain/runtime_model.go:140-185", "internal/domain/runtime_model_windows.go:48-170"],
    "selected_source_inverse_ref": inverse_ref,
    "trial_runner_ref": pin(candidate),
    "qualification_setup": "Root must independently create and admit the trusted RuntimeRegistration, sealed profile Artifact, runtime_qualification Task/Run and RegisterRuntimeQualificationPlan; no CLI verb exists for this trusted operation. The proposed runner waits for that exact live qualification and verifies one MODEL effect. No source-only artifact grants execution authority.",
    "protected_vault_seam": "One existing sealed ref is read only by future host runtime; source proposal does not unseal or copy key. New isolated product DB has its own host directory and a scoped read-only credential view.",
    "SSE_and_cancel": "Future run captures original broker effect facts and complete SSE body hashes; typed cancel is an independently pinned local fixture and is not claimed as a live provider cancellation.",
    "limits_of_evidence": ["No actual Root grant, runtime profile, CLI binary, route manifest, job contract or local cancel receipt has been supplied for execution.", "The finite 8192 bound is on requested output tokens. Actual provider billing and cost remain UNKNOWN/null; a response overrun must fail qualification and preserve raw facts.", "Static Python compile and patch inverse passed; Go compile, product execution, SDK, CLI, provider and paid inference were not run."],
    "hold_fixed_codex_cli_live_cases": True,
    "tool_failures_in_branch": [pin(HERE / ("failure-origin-%03d.json" % i)) for i in range(1, 5)],
}
report_ref = write_new("report.json", report)
entries = [pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name not in {"manifest.json", "handoff.json"}]
manifest_ref = write_new("manifest.json", {"schema": "researchos.mu-sdk-trial.source-manifest.v1", "members": entries, "member_count": len(entries), "main_untouched": True, "source_only": True})
handoff_ref = write_new("handoff.json", {"schema": "researchos.mu-sdk-trial.source-handoff.v1", "status": "SOURCE_PREPARATION_ONLY", "report_ref": report_ref, "manifest_ref": manifest_ref, "trial_runner_ref": pin(candidate), "source_inverse_ref": inverse_ref, "precheck": ["PinnedPython -I -S -X utf8 mu_sdk_trial.proposed.py precheck-bootstrap INPUT.json", "PinnedPython -I -S -X utf8 mu_sdk_trial.proposed.py precheck-execute INPUT.json"], "future_root_action": "Independent source review, fresh authority registration and 300s Windows Job, selected product patch integration after Desktop lease, trusted qualification setup, then at most three genuine Mu SDK MODEL effects under own CLI. Do not use the fixed two Codex CLI HOLD cases as substitute.", "formal_acceptance": 0})
print(json.dumps({"report": report_ref, "manifest": manifest_ref, "handoff": handoff_ref, "members": len(entries)}, ensure_ascii=False))
