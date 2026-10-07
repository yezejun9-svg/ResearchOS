# C01 fresh model development execution

Scope: DEVELOPMENT_ONLY, not an independent W06/C01 acceptance verdict.

`model-output/` contains a real fresh ephemeral Codex session on 2026-09-30:

- Codex 0.159.0; binary SHA-256 `86e8ef1013f98df51fdeea446597f7e3ca32e454d1d4d8c0402a68b03c311d70`.
- Configured model `gpt-6-luna`, reasoning `low`; provider model revision and cost remain unknown/null.
- Thread `01a0f118-e707-7ae3-8d9b-f27ae0f365f7`; 14,654 input tokens, 219 output tokens, zero cached input tokens.
- Actual model output identifies Goal/Task, current B and historical A, source id/hash, operands 17/25, MULTIPLY, and total 425. The computation value is not supplied by the acceptance contract.
- Raw event stream contains zero tool items. Returned questions and actual database QUESTION events are both zero.
- All four C01/G02 development assertions passed, including real scoped candidate upload/report and independent deterministic service acceptance. A run-scoped LOG Artifact seals the entire model computation and source/decision/bundle trace; its ref is in the final assertion.
- W05's older binary pin was absent locally. This W06-specific candidate does not update or validate W05/A04/G03.

`initial/` is deliberately retained failed development evidence. The first host monitor treated a CLI experimental-feature diagnostic (`item.type=error`) as a tool item and cancelled the process. Inspection of its complete stream shows no model tool call. The monitor was corrected to distinguish CLI diagnostics, a regression check was added, and the unused experimental switch was removed before the successful call. The initial command's `tool_attempt_observed=true` is the obsolete monitor classification, not proof of a real tool invocation or platform rejection.

UUID subdirectories marked `RUNNER_PROTOCOL_FAULT_INJECTION_ONLY` are synthetic negative tests of the assertion parser, not model executions.

Supported controls were checked against the installed CLI `exec --help` and `features list`, and official sources:

- [OpenAI configuration schema](https://github.com/openai/codex/blob/main/codex-rs/core/config.schema.json): feature toggles, skills instructions, web search and agent controls.
- [OpenAI tool registration](https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/spec_plan.rs): shell feature gate and separate model-catalog registration of apply_patch and other tools.

These sources explain why disabling shell/web/apps is not a claim that every catalog tool disappears. No model-catalog override was introduced. Host monitoring cancelled on tool items and checked the final complete stream. This case proves an observed tool-free output, not prevention of all possible tool effects. CLI discovery still logged two global skill parsing diagnostics; no other project's credentials/configuration were copied, and this is not W17 isolation.

Auth used W05's existing protected current-user DACL mechanism, copied only auth.json into an ephemeral project-local home, and cleaned that home after execution. No credential values are in the evidence. A later host cleanup command for the unrelated ignored `.local/c01-cli-inspect` public catalog inspection directory was rejected by policy; cleanup was not retried through another tool.

The successful direct Go invocation preceded the final addition of a separate sealed-artifact metadata file and the runner metadata update. The external Verifier/root must run the integrated hash for formal acceptance.
