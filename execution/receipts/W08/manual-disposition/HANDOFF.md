# W08 manual negative disposition compatibility

Status: `EXECUTED_PENDING_INDEPENDENT_REVIEW`. This is execution evidence, not a self-issued acceptance.

Production source: `78d4de057ca9f0810d8bfe4f5aac5c4c856c44ba`.
Final source: `57ef089` (only two test fixture identities changed after the production source).

The original C05 test and its assertions are unchanged. Its public close now returns `COMPLETE` for manual `REJECT` / `WATCH` / `INCONCLUSIVE` plus independently accepted `NO_IMPROVEMENT`, while preserving zero adoption and the stable release. The compatibility path requires both permanent monitor bindings and work bindings to be absent in the same transaction. It revalidates profile, target, candidate membership, current observed evidence, durable source page, exact current snapshot, sealed bytes, current caller access, negative outcome details and current W09 support. It neither creates independent review authority nor populates monitor `support` progress keys. `ADOPT` and monitor acceptance are not relaxed. No public API, SQL migration, specification, contract or command registration changed.

## Saved attempts

- `78d4de0/`: exact original C05 plus the new matrix, actual Go exit `1`. Original C05 PASS, all 8 original structured assertions PASS, SQLite snapshot retained. New matrix had 19 passing subtests and two fixture setup failures: duplicate Evidence identity and a missing `INTENT-` submission prefix. Both failed raw outputs remain intact.
- `57ef089/`: only the new matrix rerun after fixing those fixture identities, actual Go exit `0`. All 21 subtests PASS. This includes three accepted manual negative outcomes, nil actor, profile drift, stored revision mismatch, absent target, blank reason/gap/revisit, manual ADOPT rejection, stale/simulated Evidence, stale snapshot, bad snapshot ref/hash/size, missing project grant, restricted snapshot, missing durable page, zero-work monitor binding and retired-monitor binding. The work-only negative fixture also prevents completion; it reaches the existing current-monitor gate and does not alone prove the necessity of the new work-count predicate.

Command records and raw outputs were saved before report parsing. `execution-report.json` is derived from those preserved records. `sha256-manifest.json` covers all evidence files except itself and the 12 touched source files. Source and raw evidence are separate commits.

## Integration and limits

Integrate production source `78d4de0`, fixture-only correction `57ef089`, then the evidence-only commit. The final source diff after the original C05 PASS touches only the new test fixture; C05 was deliberately not repeated. Other five previously passing R02 inputs were not rerun. The package compiled as part of the two bounded commands, but no full suite or full E2E claim is made. These are local sealed source fixtures, not live-provider research qualification. No old provider/native/private-CLI path was enabled.

Independent review owns acceptance and final integration. The first aggregate failure is preserved rather than relabeled. No unrelated cleanup or cache deletion was attempted.
