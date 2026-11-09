# C evidence: normal Desktop coding PREPARE rejection diagnosis

Observed Main HEAD: 454492f78fc0536966c8c8343d4bdd2fd99250b7. Source and live DB were not edited. No GUI, Core API, private command, provider/model or second PREPARE was invoked. Evidence files only were created in this directory.

## Conclusion and limits

The original ERROR frame was not retained: Core returns error.message on the private pipe (internal/host/desktop_management_windows.go:180-183); Desktop retains only error.code (apps/desktop/main/lib/desktop-management.js:617-619), then exposes CODING_PREPARE_REJECTED. Thus the exact first live error cannot be claimed as recovered from logs.

A deterministic product checker defect is independently reproduced from the actual 326-file scope and actual authorized worktree: `selected Go check is missing same-package helper: any`. The checker omits the predeclared Go type alias `any` from its identifier whitelist, classifying valid `any(nil)` conversions as missing functions. Location-instrumented replay identifies package internal/domain. Real selected production source contains conversions at internal/domain/client_protocol.go:1245 and internal/domain/client_protocol_journal.go:306. Adding only `any` to the isolated harness whitelist makes the complete actual scope pass this validator. This is bounded local reproduction, not a recovered live ERROR or formal acceptance.

## Host and workspace identity

Discovery identifies PID61952, parent Electron65728, host-0b6cce7079a1, HTTP localhost:6700, the original data directory. The process executable is from normal-status-combined-5ddc0abb-20261014. live-host-identity.json records executable SHA256 and process creation date. Desktop starts management before ensureCore; ensureCore reporting host_launched_by_shell=false/spawns0 does not imply an old Core survived.

The DB WorkspaceBinding selects .local/worktrees/w05-own-cli-product-agent-20261012, not Main. All 326 selected paths exist; selected packages have no omitted production Go files. A preliminary Main-tree comparison found three files absent from the selection; that finding was withdrawn because Main is not the authorized workspace. Do not expand authorization based on those files.

The readonly DB projection retains one qualification operation, one SETTLED Run and one OBSERVED dispatch; host:coding-confirmation has zero records. Existing configuration remains revision1. The captured writer lease expired after the failed attempt; elapsed-time lease expiry is not evidence of the original failure. Any later UI retry needs a fresh current writer and resources bound to it.

## Smallest source repair for Root review

Exact scope:
- internal/host/runtime_coding_windows.go:324: add predeclared `any` to the existing builtin/type name set; retain missing-helper, source-inventory, import/embed, authority, budget, writer, and configuration gates.
- internal/host/runtime_coding_windows_test.go:38: add complete_predeclared_any_conversion positive case with `any(nil)` in production source; retain missing_helper negative and preferably add missing_helper_with_any_conversion to demonstrate conversion allowance does not suppress missing-helper detection.

No edits to actual authorized workspace, Go/vendor directories, UI scope, or live DB are needed for this defect. Read326/write2 remain unchanged.

Suggested targeted test command (approved Source worker's checkout and existing pinned dependencies):
`D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe test ./internal/host -run '^TestProductCodingCheckInventory$' -count=1`

Then rerun the actual-scope readonly checker against the repaired Source and rebuild the normal package under the existing controlled build workflow. Only a fresh actual Desktop PREPARE can establish that earlier/later live gates also pass; local checker PASS is not that evidence.

## Reproduction artifacts

readonly_source_checker.go extracts the current functions validateCodingCheckSources, validateCodingEmbeds, codingMissing, runtimeCheckPath, runtimeToolPlainPath, runtimeToolBytes and path policy. It substitutes the local equivalent check struct and errors.New for domain.Fail only to compile without product runtime/database dependencies; error classification logic and filesystem reads remain unchanged. It performs only local reads, no Go test of target sources, model dispatch or Core operation.

checker-result.txt: original extracted validator rejects `any`.
checker-location-result.txt: same rejection localized to internal/domain (message instrumentation only).
checker-any-candidate-result.txt: sole whitelist candidate produces CHECKER_ACCEPTED.
inputs.sha256.json binds initial UI, checker and source inputs; actual-workspace-scope-audit.json hashes all326 authorized source files; manifest.sha256.json binds final evidence.

Evidence class C: diagnosis and bounded local reproduction only. No formal acceptance increment.
