# W09 exact header correction candidate v2 independent review

Decision: **REQUEST_CHANGES**. Actual reviewer: `/root/w09_header_gate_review`.
Candidate author: `/root/resume_audit`. This review creates no recovery authority,
formal acceptance, historical verdict, or replacement delivery capture.

The exact header exception is narrow: fixed old/new hashes, 22,732-byte length,
exact semantic `openai` to `custom` transition, offset zero only, and six historical
triplets. The original 22 test methods passed independently (only their temporary
drift-file location was redirected into this review scope). Actual 18 ranges were
read and rechecked. Original Context/review/issuance references, old profile and
index pins matched. Source drift is still rejected as `NEEDS_REVALIDATION`.

## Blocking finding: executable helper is selected before independent review

Candidate `formal_profile_w09.py:207-218` accepts the helper SHA from the mutable
Root authority, executes that helper at line 216, and only then calls its
`authorize`. Every non-author review and actual-delivery check is in the newly
executed helper. There is no independent pre-execution anchor for the exact helper
bytes this review was asked to authorize.

The isolated reproduction supplies a helper at the required fixed repository
path and updates its authority SHA/byte count. It leaves `certificate_ref`,
`review_ref`, and `delivery_ref` empty. `_header_correction` nevertheless executes
the unreviewed helper and returns a correction dictionary. This uses an isolated
fixture under this review directory; Main and Canon are unchanged. A changed
helper with its old pin is correctly rejected, but repinning the changed helper
bypasses the required review entirely. A changed Canon pin must not itself serve
as proof that the newly selected code received the required independent review.

Suggested minimum repair: hard-pin the reviewed helper SHA and byte count in the
reviewed profile itself; require authority's helper reference to equal that pin;
hash the exact `raw` bytes before `exec`. Keep the independent certificate/review/
current original-delivery validation inside the now-fixed helper. Reissue the
candidate certificate to pin the changed profile, then obtain fresh source review.
Do not preapprove that future candidate through this rejected v2 review.

## Evidence and limits

`candidate22-tests.txt` records all 22 original test methods passing.
`controls-result.json` records five additional controls: old chat rejected;
current claim without real capture rejected; business source drift rejected;
repinned unreviewed helper bypass reproduced; helper drift without repin rejected.
`review_controls.py` is the reproducible source-only test. All disposable fixture
files were removed. No product, Native, consumer, or formal index execution ran.
The original full-source and business gates must still run on future adoption;
this review does not claim recovered A06/C19 or any increase above 0/42.

The frozen W09-99 card requires current source/evidence hashes and independent
verification; acceptance.json global reuse rule requires matching applicable
versions. The proposed compatibility scope can preserve that boundary only after
the loader itself cannot replace the reviewed helper through authority repinning.
