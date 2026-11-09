"""Seal existing public/contract evidence only; no network, product, or model calls."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
root = Path(__file__).resolve().parents[7]
spec = Path("D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4")
prior = root / "execution/v2.4/receipts/W05/W05-99"

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def seal(name, body):
    raw = (json.dumps(body, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with (here / name).open("xb") as stream:
        stream.write(raw)
    return pin(here / name)

spec_refs = {
    "goal08": pin(spec / "08_AGENT_EXECUTION_GOAL.md"),
    "operations07": pin(spec / "07_OPERATIONS_AND_EVOLUTION.md"),
    "acceptance_contract": pin(spec / "contracts/acceptance.json"),
    "domain_schema": pin(spec / "contracts/domain.schema.json"),
}
prior_refs = {
    "strict_budget_conclusion": pin(prior / "provider_budget_resource_readonly_codex/budget-4d5e48bb6b764a34ac537990b10290f2/conclusion.json"),
    "targeted_strict_report": pin(prior / "b01_targeted_resource_path_codex/dcd0fe29cc2946f48474cb8e79b5b680/report.json"),
    "zero_charge_alternative_report": pin(prior / "b01_zero_charge_alternative_resource_review_codex/8a6e82bb4ec543a4960418f42c04223f/report.json"),
}
public_base = prior / "provider_budget_resource_readonly_codex/budget-4d5e48bb6b764a34ac537990b10290f2/raw"
public_source_refs = {
    name: pin(public_base / filename) for name, filename in {
        "go_route": "go-route/response.raw",
        "deepseek_model_toml": "models-go-model/response.raw",
        "handler": "handler/response.raw",
        "openai_compatible": "openai-compatible/response.raw",
        "request_body": "request-body/response.raw",
    }.items()
}
web_io = [pin(here / f"public-web-{i}.json") for i in (1, 2, 3)]
failure_origins = []
for i in (1, 2, 3, 4):
    folder = here / f"failure-origin-{i:03d}"
    failure_origins.append({"index": i, "input": pin(folder / "input.json"),
                            "result": pin(folder / "result.json"),
                            "origin": pin(folder / "origin.json")})

report_ref = seal("report.json", {
    "schema": "researchos.b01-contract-and-billing-public-readonly.v1",
    "stage": "RESOURCE_READONLY_STOPPED",
    "basis": {"spec": spec_refs, "prior": prior_refs,
               "observed_checkpoint_snapshot": {"path": str(root / "execution/v2.4/checkpoint.json"),
                    "sha256": "a7e9ddf6c86cfdef441173b936d898f4b8386c88a4fac2a455895e0f16235f4a",
                    "bytes": 2793296},
               "nonsecret_current_policy_pointer_io": pin(here / "current-policy-pointer-read.json")},
    "frozen_contract": {
        "goal08_section1": "Default amount mode has cap=null; known or unknown cost is recorded. Unlimited amount does not authorize buying, recharging or a new subscription.",
        "operations07_section5_1": "UNLIMITED_AMOUNT cap=null with accounting; only CAPPED/STRICT requires a reliable upper bound and atomic pre-dispatch reservation, else that new call is blocked.",
        "domain_schema": "UNLIMITED_AMOUNT requires ACCOUNTING_ONLY and ALLOW_AND_RECORD; STRICT requires unknown_cost_action=BLOCK.",
        "acceptance_C13_01": "Unknown cost remains unknown/null and unset amount cap does not block an otherwise authorized task.",
        "acceptance_C14_02": "A strict cap blocks a request whose cost has no reliable upper bound, without silently converting currency or cost to zero.",
        "current_active_global_project_goal_run_policy_mode": None,
        "current_active_cap_usd": None,
        "why_unknown": "The read-only current checkpoint projection exposes the old live_budget_resource_ref but no active BudgetPolicy pointer. Product policy state was not inspected; absence of a checkpoint pointer is not proof that no active cap exists.",
        "old_0_50_status": "Prior targeted report proposed a USD 0.50 strict per-model reserve for one LIVE qualification. It is not evidence of an active user-set global/project/Goal cap and cannot be silently applied to every B01 request or reused as a new grant.",
        "old_strict_scope_status": "OPEN for that frozen scope. This report neither rewrites nor lowers C14, its guard, or its failure history."
    },
    "current_official_go_route": {
        "provider_id": "opencode-go", "preferred_model_id": "deepseek-v4.1-flash",
        "chat_completions_url": "https://opencode.ai/zen/go/v1/chat/completions",
        "sdk_package": "@ai-sdk/openai-compatible",
        "official_doc_url": "https://opencode.ai/docs/go/",
        "public_route_source_url": "https://github.com/anomalyco/opencode/blob/3f393d78bfc3f0826b2c7080e57964c235704695/packages/console/app/src/routes/zen/go/v1/chat/completions.ts",
        "public_model_metadata_ref": public_source_refs["deepseek_model_toml"],
        "same_credential_exact_current_policy_or_billing_branch": None,
        "qualification_or_paid_request_authorized_by_this_report": False
    },
    "public_billing_code_inference": {
        "handler_source_url": "https://github.com/anomalyco/opencode/blob/3f393d78bfc3f0826b2c7080e57964c235704695/packages/console/app/src/routes/zen/util/handler.ts",
        "handler_ref": public_source_refs["handler"],
        "facts": [
            "Go lite validation returns the lite billing branch while within allowance; after a limit it may route to balance only if the account's Use balance setting allows it.",
            "The pinned handler's occurred-cost response is zero outside balance and its balance debit is based on calculated token cost; this is source behavior, not a deployed-version/account attestation.",
            "The pinned cost calculation multiplies input, output, cache-read and configured cache-write token rates. It extracts reasoningTokens but does not separately add that field to the displayed formula.",
            "The pinned OpenAI-compatible adapter forwards body.max_tokens and maps completion_tokens to outputTokens; the gateway request body otherwise passes through with model replacement. No pre-dispatch per-request USD hard cap is proved by those lines."
        ],
        "openai_adapter_ref": public_source_refs["openai_compatible"],
        "request_body_ref": public_source_refs["request_body"],
        "actual_deployed_build_matches_pinned_source": None,
        "reasoning_in_completion_tokens_for_exact_upstream": None,
        "current_use_balance_setting": None,
        "provider_enforced_per_request_usd_cap": None
    },
    "free_alternative": {
        "model_id": "longcat-2.5-preview-free",
        "same_go_chat_completions_route_documented": True,
        "official_doc_url": "https://opencode.ai/docs/go/",
        "official_model_toml_url": "https://raw.githubusercontent.com/anomalyco/models.dev/b5dc3899724894a20f7476d16a3ef432087fc76a/providers/opencode-go/models/longcat-2.5-preview-free.toml",
        "published_input_output_cache_read_rates": "zero",
        "published_cache_write_rate": None,
        "limited_time_end": None,
        "exact_current_credential_model_access": None,
        "actual_deployment_free_branch": None,
        "conditional_source_inference": "Pinned handler returns lite for a zero-valued model cost object before balance fallback; the official TOML and docs list three zero categories, but this does not establish current deployed cost object, promotion lifetime, account branch or every charge category.",
        "adopted_as_new_model_profile": False,
        "strict_zero_cost_qualified": False
    },
    "strict_money_bound_if_active": {
        "state": "NOT_ESTABLISHED_FOR_PREVIOUS_0_50_SCOPE",
        "required_for_exact_deepseek_scope": [
            "provider/model/route and current deployment binding",
            "all billable input including cache/tool/prefix, and all reasoning plus visible output, with enforced request hard caps",
            "applicable maximum rates or provider-enforced USD cap including cache creation, internal attempts/fallbacks and any fixed charge",
            "current account balance fallback/plan state if relying on subscription-only marginal charge"
        ],
        "published_monthly_5hour_weekly_quota_is_per_request_usd_cap": False,
        "historical_conditional_0_3244032_is_proven_upper": False,
        "unknown_cost_is_zero": False
    },
    "root_next_action": [
        "Before a fresh LIVE model dispatch, obtain an authorized, nonsecret effective BudgetPolicy snapshot for global/project/Goal/run and its revision; compare all active parents. This report does not provide that snapshot.",
        "If the effective policy is UNLIMITED_AMOUNT/ACCOUNTING_ONLY with cap=null and existing model credential is authorized, create a fresh finite LIVE qualification scope on the preferred DeepSeek route, limiting time, requests, tokens, retries and resources; record actual or unknown cost as NULL and do not claim free service or strict upper-bound PASS.",
        "If any effective parent is CAPPED/STRICT, retain the relevant strict call BLOCKED until the exact deployed per-request bound or provider-enforced cap is independently pinned and reserved before PREPARED.",
        "Do not replay the old 401/UNKNOWN effect, switch model silently, buy/recharge/subscribe, or treat a public source/SDK probe as product qualification."
    ],
    "public_web_tool_io_refs": web_io,
    "official_urls_used": [
        "https://opencode.ai/docs/go/",
        "https://raw.githubusercontent.com/anomalyco/models.dev/b5dc3899724894a20f7476d16a3ef432087fc76a/providers/opencode-go/models/longcat-2.5-preview-free.toml",
        "https://raw.githubusercontent.com/anomalyco/opencode/3f393d78bfc3f0826b2c7080e57964c235704695/packages/console/app/src/routes/zen/util/handler.ts",
        "https://raw.githubusercontent.com/anomalyco/opencode/3f393d78bfc3f0826b2c7080e57964c235704695/packages/console/app/src/routes/zen/util/provider/openai-compatible.ts",
        "https://raw.githubusercontent.com/anomalyco/opencode/3f393d78bfc3f0826b2c7080e57964c235704695/packages/console/app/src/routes/zen/util/requestBody.ts"
    ],
    "public_source_refs": public_source_refs,
    "new_failure_origins": failure_origins,
    "new_failure_count_delta": 4,
    "state": {"source_qualification": False, "sdk_qualification": False,
              "formal_case_accepted_delta": 0, "model_or_paid_requests": 0,
              "private_or_credential_reads": 0, "product_or_canonical_changes": 0,
              "old_failed_effect_retried": False, "fixed_parent_cut_mutated": False}
})
members = [pin(path) for path in sorted(here.rglob("*")) if path.is_file() and path.name not in
           {"manifest.json", "handoff.json"}]
manifest_ref = seal("manifest.json", {
    "schema": "researchos.b01-public-readonly-members.v1", "stage": "RESOURCE_READONLY_STOPPED",
    "namespace": str(here), "members": members, "member_count": len(members),
    "report_ref": report_ref, "new_failure_count_delta": 4,
    "source_qualification": False, "formal_case_accepted_delta": 0
})
handoff_ref = seal("handoff.json", {
    "schema": "researchos.b01-contract-and-billing-public-handoff.v1",
    "stage": "STOPPED_RESOURCE_READONLY", "report_ref": report_ref,
    "manifest_ref": manifest_ref, "web_io_refs": web_io,
    "failure_origins": failure_origins, "new_failure_count_delta": 4,
    "effective_active_policy_mode": None, "previous_strict_scope_still_open": True,
    "fresh_live_scope_authorized_by_this_report": False,
    "source_qualification": False, "sdk_qualification": False,
    "formal_case_accepted_delta": 0
})
print("B01_PUBLIC_READONLY_SEALED", report_ref["sha256"], report_ref["bytes"],
      manifest_ref["sha256"], manifest_ref["bytes"], handoff_ref["sha256"],
      handoff_ref["bytes"], len(members))
