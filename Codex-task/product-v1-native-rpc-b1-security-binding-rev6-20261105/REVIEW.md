# B1 rev6 final source binding

Decision: **APPROVED_SOURCE_FIXTURE_ONLY**. Pending source blockers: none. Formal increment: 0.

The final archive has 30 verified listed files, no hash mismatch and no unlisted files. Its eight full repository paths exactly match the registered lease. All five production files and two unchanged tests retain the reviewed rev5 hashes. The only change is two `textElements` → `text_elements` substitutions in `adapters/runtime/codex_rpc_protocol_test.go`; exact forward and inverse comparisons passed.

Full source hash keys are in REVIEW.json under `source_sha256`. Candidate ARCHIVE.json SHA256: `1c57e9129d6dd0201ae5ac2e5f7dbb1190272cae9f5f55a03ae2c40d08f59cce`. SOURCE.json SHA256: `2ff361290390541633a08240c9ef430734ccd6c461087fc704645686807bc7c0`.

Prior F1–F6 source resolutions are retained. The official DTO spelling correction is now resolved. Old reports are unchanged. This review does not infer Native compatibility or permission qualification from fake tests.

Test04 receipts were hash-verified as archive members only; their actual run semantics were not audited or used here. Root's final combined test scope remains pending follow-up. Patch artifacts are hash-bound but were not applied by this reviewer. Integration must validate the resulting eight paths and combined tree.

No tests, Native, model, echo or probes were run; no production or D files were written. B2/B3 integration, live qualification, original Job controls and separately authorized synthetic runtime evidence remain prerequisites. Source/fixture approval is not product acceptance or permission to replay old scopes.

