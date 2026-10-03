# W05-01 resume note

Round 3 entry point, written at 2026-10-03T08:07:48.339070+00:00 (HEAD 9efeabb1).

- Round 1: REWORK_REQUIRED by qoder-desktop:/root/w0501_verifier_r1 (3 blocking issues), frozen at git commit 477e9226.
- Round 2: REWORK_REQUIRED by qoder-desktop:/root/w0501_verifier_r2 (3 blocking issues, 9 reservations) against the receipt at code HEAD 5c8306f3 (29 assertions, 17 matrix cases all caught, 7 disclosed rows). Its verdict is committed verbatim, not edited.
- Round 1 was accepted as closed on all three items. What remains is completeness of disclosure against the card text, plus the two further issues this reviewer raised:
  - **W0501-R2-B-03** (medium): the new provider disclosure names the wrong blocked resource, pointing the remediation at the pinned executor binary when step 1 is blocked by an unbound client surface owned by other cards
      owed: add W0501-MODEL-SUBSTITUTION-NOT-DETECTED and W0501-FAILURE-CLASS-EXPLICIT-PROTOCOL-ERROR skip rows with the measured reason (ModelRevision declared at codex.go:17 and never populated; no row or mutant touches request_failed), restate W0501-FAILURE-CLASS-AUTH-RATELIMIT-UNSUPPORTED-TOOL-CALLING so each of the card's five classes maps to exactly one asserted or one disclosed row, and if the format-e
      owed: delete the sentence, or extend the --capture path so the two selector rows are captured at the receipt HEAD and the note cites those logs by key.
      owed: restate the row's reason as measured (provider.models and provider.probe are PLANNED and unbound in client_mapping.json, owned by W02-03 and W08-01; no provider.* command key exists in either registry; provider.configure is not in the registered protocol), keep the blocked resource authorized_product_model_backend as a second independent reason, and keep the NOT_RUN grading - nothing about the dis

Next, in order:

1. Treat each blocking issue above as a measurement task. The first is partly prose and partly product: the model-substitution property needs the decoder to carry the model identity it received (adapters/runtime/codex.go declares Protocol.ModelRevision and Parse never assigns it) before any row can compare a requested model with an answered one; where it stays unimplemented it must appear as a NOT_RUN row naming the reason, and the same for the fifth failure class, which the current skip row enumerates wrongly.
2. Re-run the whole chain serially: python execution/v2.4/receipts/W05/W05-01/run_evidence_chain_w0501.py (two binding runs, freeze, matrix, capture, receipt). Never beside another heavy Go suite.
3. Re-run the self-audit (audit_receipt_w0501.py) and commit the round-3 evidence before asking.
4. Review request round 3 from a third identity: python execution/v2.4/receipts/W05/W05-01/make_review_request_w0501.py round3. Wait for the verdict to appear AND settle for about 90 seconds before pinning; a missing artifact is not a dead reviewer.
5. Register only on a verdict with an empty blocking_issues array: python execution/v2.4/receipts/W05/W05-01/register_w0501_accepted.py (refusal path measured: exit 1, zero writes).

Known small defects, fixable only as new files: the tail print of make_review_request_w0501.py still names review_request_round1.json whatever the round, and executor_identity_measurement.json still lists a profile or manifest model substitution refusal among what this card may assert, which the round-2 reviewer read as evidence that an assertable refusal was known and left undisclosed.

Owed outside this card: W06-01 test.orchestration before-baseline; W12-99 DAILY/MONTHLY windows; W07-01 source connection; the 42-case selector debt; the W12-01 nit list, which can only arrive as new files because all 33 of its evidence rows are hash-pinned.

Audit standing: 16 of 71 cards accepted, 0 of 22 parent tasks, 0 of 42 formal cases. Not complete.
