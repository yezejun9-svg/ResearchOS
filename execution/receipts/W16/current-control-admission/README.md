# W16 current-control admission fixture

Implementation source commit: `36956330065ef7dc9e91005850ee19e1dea69a48`.

The first invocation that entered EVALUATE was attempt 10. It passed the five private phases against one actual `apps/control` process, followed by normal Run/report, independent Acceptance, Experiment/result and the ordinary no-gain rejection. At SEAL: current=true, owner_matches=true, OS qualified=false, candidate=REJECTED, host=STABLE. There was exactly one durable current-evaluation reservation and completion. The second EVALUATE request returned the sealed existing result without executing again.

This is a same-user synthetic fixture. It is not positive gain, SCM isolation, G2 current cutover, W18 current restore, or normal release authorization. The disposable process has been stopped after proof capture; `current=true` describes freshness at SEAL, not after cleanup. ShutdownFixture refused drain because the ordinary fixture zero-cost RESERVE remained outstanding; cleanup stopped only this spawned PID/creation/image identity. No drain or cutover success is claimed.

## Execution identity

`attempt-10-first-evaluation/source-before.json` records the actual pre-execution HEAD and dirty file inventory. `source-after.json` proves that every recorded byte was unchanged during that attempt. Source commit 3695633 was made afterward; it is not represented as the execution-time HEAD. No provider calls occurred.

The fixed recipe builds the actual control image with pinned Go, readonly modules, no network module resolution, trimpath and no VCS/build-ID dependence. SAMPLE independently rebuilds approved source and requires byte equality. The source inventory is `sha256:a00e0f4eb8e6b4071ee3519767f1cc8b7186b64e4d48c540a98d63831fde4971`. Actual image, database CODE artifact bytes, build hash and protected actual owner image all equal `sha256:203fe4d5208de7c571392b345ec580e007ec3713799a8d2042e921393dcae14c`. The release journal stores this hash without the `sha256:` prefix; the read-only audit normalizes that representation explicitly.

## Preserved evidence

- `attempt-10-first-evaluation/raw.log`: complete actual test output, including cleanup refusal.
- `actual-build.json`, `phases.json`, `current-control-native.json`: build provenance, exact phase replies, normal Acceptance/Candidate/Experiment and one-reservation checks.
- `private-locators.json`: absolute local locators for the preserved original authority DB, exact same-user Canary store, and evaluation root. Private contents are not copied into Git.
- `persisted-binding-audit.json`: read-only verification of all three snapshot descriptors, every ordered chunk hash/size, whole snapshot hashes, proof hash and CODE/actual image equality.
- `audit_persisted.py`: reproducible hash audit; it does not evaluate candidate code or qualify current authority.

The final private proof is ticket `ps1:8e776706c93226d15055839353649c5a`, hash `sha256:52e11691cd7d336868d285bcf403afc5ae26e88d8e8008d4959cfbd209491a9c`, in the exact Canary store named by the locator. It contains complete B0/G0/G1 descriptors and preparation/evaluation row deltas. Each snapshot also has a separately retained private descriptor created immediately after its chunks. Chunk order for the final proof comes from these descriptors, never file timestamps.

G0 generation is `sha256:778b6ad880efe4a4b7074c0fe115d823085ade58b1a02988ca7e58adaedaf034`; G1 is `sha256:3380e7ba932b467aff2f3d30f639e63750890143d00920e8996e18d06fad2a42`. G0-to-G1 has 221 explicit row changes, hash `sha256:84592a1315e754374d982940e4df1d194bf7d61357b1d6f8d6eeb9bce37f1ae9`. All authority, policies, business-cycle data, source and owner bindings remain frozen; only named run/acceptance metadata is admitted.

## Preparation diagnostics and limitations

Attempts 01-09 never called EVALUATE. They are not native evaluation failures or reservation results. All attempts used newly generated synthetic databases; no old historical CONTROL helper was rerun.

| Attempt | Last phase / actual rejection | Correction or observation | Retention |
|---|---|---|---|
| 01 | SAMPLE / CONTROL_REBUILD_TOOL_HASH | Locked tool hash is bare SHA256; domain Digest has a prefix. | Terminal excerpt only; execution file inventory, image and full DB were not retained. Cannot independently recompute this attempt. |
| 02 | REGISTER / CONTROL_DATASET_ID_SCOPE | Producer case IDs must use existing public-control-/private-control- prefixes. | Terminal excerpt only; exact execution inventory and full DB unavailable. |
| 03 | START_EVALUATION / HTTP 403 role not authorized | Producer must use its pre-issued release token. | Terminal excerpt only; exact execution inventory and full DB unavailable. |
| 04 | FREEZE / CONTROL_CURRENT_BUSINESS_READSET_CHANGED | Unresolved at this attempt; later retained diagnostic identified the standard Experiment budget addition. | Terminal excerpt only; exact execution inventory and full DB unavailable. No retrospective byte claim. |
| 05 | Before child startup / PROTECTED_BOUNDARY_INVALID | Explicit preserved Canary locator needed native canonical path separators. | Complete raw and source-before retained. No child/sample. |
| 06 | FREEZE / newly added current Experiment BudgetPolicy | Permit exactly one default child policy, bound to the new Experiment and existing parent. Every existing and unrelated policy remains frozen. | Raw/source-before/original DB/new Canary retained. |
| 07 | FREEZE / exact ContextBundle ImpactLink | Bind DEPENDS_ON to the named Task historical version, exact bundle evidence and version_vector target. | Raw/source-before/original DB/new Canary retained. |
| 08 | FREEZE / existing Goal task_ids append | Permit exactly the current Task appended once, revision+1, other Goal fields unchanged. | Raw/source-before/original DB/new Canary retained. |
| 09 | FREEZE / zero-cost fixture BudgetLedgerEntry | Complete offline row census also identified exact empty orchestration dependencies, sealArtifact operation spelling and nested struct/map host JSON ordering. | Raw/source-before/original DB/new Canary retained. No further native diagnostic sessions. |

`offline-preparation` reads attempt 09's original B0/DB without constructing an owner or running candidate code. Historical B0 chunk order was reconstructed by writer times and verified against the original SAMPLE whole hash before row analysis; this is diagnostic evidence only. The full preparation delta then passed. Negative tests reject wrong budget parent/default/scope and any additional policy, plus authority changes. No whole policy table or auth table is ignored.

The early terminal excerpts in `early-terminal-excerpts.json` are explicitly partial and do not replace missing raw execution manifests. Later successful execution does not retroactively qualify them.

## Checks

`final-targeted-tests.log`: snapshot purpose/project/stage/order/hash rejects, exact-budget rejects, test-process-owner rejection, and existing preparation authority-change counterexamples passed. `final-compile.log`: domain, evaluation, supervisor and actual control packages compile. These checks do not repeat the old native matrix. Independent review is still required; this document is execution evidence, not self-acceptance.
