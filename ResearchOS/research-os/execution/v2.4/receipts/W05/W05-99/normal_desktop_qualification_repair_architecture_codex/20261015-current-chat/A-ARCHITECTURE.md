# A — Qualification execution projection, implementation contract

Status: ARCHITECTURE_ONLY; no source change, product write, qualification or process operation. This package authorizes a proposed source scope only after Root records its implementation card.

Authoritative Main SHA: `4f4023c956f84d65743f39ce77d6c8899a21ada1`. Source25 composition `2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02` is a separate later adaptation. Do not import its migration/startup changes into this repair. SDK8df worker resources, installed bundle, coding profile Artifact/ref/hash and configuration records remain frozen.

## Required result

For a newly prepared qualification dispatch with fully bound qualification authority, stage an effective model configuration with `max_calls=1` and `tools=[]`. Persistent coding configuration stays byte-identical, including `max_calls=8` and its four tool schemas. Ordinary `mu_turn` uses the original coding configuration. Historical dispatches without the projection marker retain their old interpretation. This repairs input exposure; it neither resolves the existing UNKNOWN Run nor guarantees a model will obey its available tools. Provider misbehavior remains subject to the separate B failure-closure design.

## Production chain and exact change points

| File / current production caller | Required change |
| --- | --- |
| `internal/domain/runtime_dispatch.go:97-111`, `prepareRuntimeDispatch` | After assigning dispatch_key and before final manifest hash/INSERT, produce a versioned projection marker for a newly prepared qualification only. Validate actual Task type and immutable plan binding here. |
| NEW `internal/runtimepolicy/qualification_projection.go` | Pure shared derivation and verification, no DB, provider, filesystem, clock or mutation. Used by domain and runtime adapter, avoiding import cycles. Return an owned deep copy of effective config plus binding metadata; never mutate any nested source object. |
| `internal/domain/runtime_model_windows.go:19-45`, `stageRuntimeProgram` | Derive config from verified manifest; serialize that result to worker.json. Frozen bundle validation remains exact. |
| `adapters/runtime/bridge_program.go:10`, `validateBridgeProgram`; `adapters/runtime/bridge_windows.go:196`, `StartBridge` | Pass the already hash-verified complete manifest into program validation. Recompute projection and require exact staged worker.json bytes/hash for that effective config. Continue exact frozen bundle, argv, backend/model checks. |
| `internal/domain/runtime_broker_windows.go:183`, pre-prepare model validation and call gate | Recompute effective config from the exact dispatch; validate SDK request and count against it before effect preparation. `providerRoute:105` must still compare the registered provider's config against ORIGINAL profile.model_config. Do not overwrite provider registry config with projection. Qualification-specific `model_qualification.max_calls=1` gate remains active. |
| `internal/domain/runtime_model_windows.go:49`, `brokerModel` | Independently obtain effective config from dispatch and validate complete wire request before HTTP construction. No prompt rewriting, SDK request re-encoding or provider identity change. |
| `internal/domain/runtime_model_verification.go:399,408,648`, `verifyMuTurn` | Derive effective config from the dispatch in the already bound snapshot. Compare source profile/ref/config and marker, then use effective config for wire request/schema checks and applicable bounds. Ordinary turn verification keeps existing source config. Existing qualification prohibition of tool effects and max-call checks stay active. |
| `internal/domain/runtime_drain_windows.go:207-236`, `completedLocalUnknownCost` | Preserve original profile Artifact check; recompute effective config from exact manifest for confirmed model request validation. Do not turn UNKNOWN monetary cost into zero, release it, remove ledger entries or weaken native-closure checks. |

No worker.mjs edit is needed: existing parseConfig accepts tools=[] and max_calls=1; makeTools maps that list, onPayload injects it, and Agent receives no coding customTools. This must be demonstrated using the frozen worker artifact, not only a mocked config consumer. No SDK/build/bundle hash change is permitted in A.

## Projection binding v1

Use a new private manifest field, e.g. `model_execution_projection`, with schema `researchos.qualification-model-projection.v1`. Its exact JSON field set must be fixed in code and reject unknown versions/fields. Required bindings: project_id, task_id, run_id, epoch, runtime_id, dispatch_key, profile_ref, profile_hash, source_model_config_hash, qualification_plan_hash, permission_hash, effective_model_config_hash, and policy `{max_model_calls:1,max_tool_calls:0}`. Include source profile body hash if profile_hash continues its current meaning Hash(profile_ref). Never relabel that existing field as profile content hash. Do not include the final manifest hash inside the marker: this would create a hash cycle. The immutable outer manifest hash binds the entire marker.

Eligibility is conjunctive: Mu backend, admission.qualification_bootstrap=true, permission.purpose=runtime_qualification, nonempty bound permission.plan_hash, actual Task runtime_qualification at creation, profile/ref/hash validated by existing admission, profile.model_qualification exactly tied to original model config hash and route, and qualification.max_calls exactly 1. Any partial or contradictory marker/qualification tuple fails closed. A model_qualification.max_calls=2 profile is outside v1; reject preparing its v1 projection rather than silently reinterpret it. An ordinary non-qualification manifest must not carry this marker.

The transformation deep-copies the original config and changes exactly two fields: max_calls to 1 and tools to an empty array. ref/api/provider/model/endpoint/route/max_output_tokens and all other accepted config fields stay identical. Apply the same canonicalization and sha256 prefix convention as current manifest/config hashing. A package-level golden test must prove hashes match existing domain and adapter conventions for decoded json.Number values. Return errors on invalid numeric types instead of treating missing/zero as 1.

Legacy absence is an explicit compatibility branch: without marker, every consumer uses original model_config exactly as before, including an old qualification dispatch. Presence with invalid marker is NEVER a fallback. The production preparation path MUST emit the marker for every eligible new qualification; caller tests prevent future omissions. No historical manifest or journal is modified, and this design does not newly authorize historical replay.

Existing `validateRuntimeModelRequest` can remain unchanged because each relevant caller now supplies the correct effective config. Existing provider route identity still uses original config. Staging uses the effective config; the SDK decides actual messages and request serialization; host/verifier merely validate the complete bound request. This is not satisfied by changing tools alone or substituting a prompt instruction.

## Scope and evidence boundary

Only source/test paths in A-exact-scope.json may change. Test edits must be meaningful additions to current package fixtures; do not rebuild installed product resources. Tests use isolated roots, local fixture transport, no real model, no actual data root, and no current Core/worker interaction. New Go caches and temp directories should be on D: in a new owned directory; do not remove prior receipts/caches.

Required proof is A-test-cuts.json: pure policy, all production consumers, frozen worker fixture, normal mu_turn regression, tamper rejection, unchanged source profile/bundle. An A source acceptance means only implementation and isolated fixture proof. It is not B/C acceptance, actual deployment, native old-run closure, new qualification success, independent runtime acceptance, parent-task completion, or any formal case increment. Current actual Run remains UNKNOWN/RUNNING until a separate reviewed terminal-only operation.
