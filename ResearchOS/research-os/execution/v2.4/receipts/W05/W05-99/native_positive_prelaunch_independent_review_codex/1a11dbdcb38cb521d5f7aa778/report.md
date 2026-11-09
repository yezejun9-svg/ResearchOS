# Security Audit Report

## Summary

Critical: 0; High: 0; Medium: 1; Low: 0. This exact bootstrap needs one source-integrity ordering fix before launch. Future runtime acceptance is not a precondition for attempting the isolated test.

## Findings

### [MEDIUM] Bootstrap executes supposed pinned sources before validating and holding them

- **Location:** serve_one_positive.actual_owned.py:15–24,40.
- **Description:** module(path) compiles and executes arbitrary current path bytes. ControllerSource executes at line 21, and SourceReadGuard/OriginalOwnedHelper at line 24. The FrozenInputs guard is not acquired until line 40. The config hash check, JSON decode and pin construction also use separate reads.
- **Impact:** Replacement or concurrent modification of a pinned source can execute before the later frozen-file check rejects it. This crosses the source-to-Root-process trust boundary before authentication; STRIDE Tampering / Elevation of privilege, CWE-345 / CWE-367.
- **Scenario:** Change the public ControllerSource file after preparation. On launch, its top-level code executes at line 21 before a hash mismatch could be raised by guard acquisition. This scenario was reasoned from source; no mutation or malicious target was executed.
- **Recommendation:** Create a new bootstrap revision. Verify the config's fixed hash and bytes from one buffer and decode that buffer. Verify SourceReadGuard's exact config pin before loading it. Acquire config, FrozenInputs, bootstrap and fixed Python handles before controller/helper execution. For every module, compile the same bytes whose hash/size were verified. Keep the guard through child completion and close it in finally. The child must verify pinned bytes or rely on an already-held exact parent guard.

## Positive observations

All 4091 review references match current hashes and sizes, including the 4083 frozen config inputs. The binary's actual tagged compilation provenance matches the exact harness Source; the selector runs only TestNativeMigrationAuthorityHarness once. Case is positive-replay. Controller/facts/fixed release/grant paths remain absent. The bootstrap has not executed and its namespace contains only its Source file.

The controller creates a held observed Job, publishes assigned-before-resume/resumed proofs and handles queued live-observation requests. The first release payload pauses at an explicit approval file. Bootstrap only serves, without signing or publishing approval. The harness creates its fixture through test factories, with fixture-only adapters and per-test paths; public fixture reports mark synthetic/formal=false. It performs a real backup rehearsal before first release pause. Synthetic in-process fixture credentials are distinct from production Owner authority.

## Finite runtime boundaries

Actual Source timeout values are: fixture context 1200 seconds, inner Job 1260, controller cancellation 1270, outer Job 1440 and Go test 1500. The earlier 1400 outer value was descriptive drift; the script uses 1440. Hard process timeout cannot guarantee indefinite fixture retention. Root should inspect/sign only within the separately reviewed finite phase and close/observe the Job afterward.

## Remaining scope

One minimal bootstrap fix is required. After its static review, the isolated launch can proceed to generate public phase evidence. Future child import closure, actual Job/guard cleanup, concrete payload signatures, fixture inspection/release, native result acceptance and original nine-case completion remain later evidence gates. No Go/native/SQL/private-key operation or canonical write occurred in this review. CP357 remains exact. New mechanical errors: 0 in this prelaunch review (818 belongs to the preceding canonical review).

