# Authorized historical fixture evidence

Minimal source candidate `3dffadd250cb4e5c312baf87e9136f7cfa8ba40a` changes only original `backup_upgrade_test.go:975–981`. Both protected exterior byte hashes match. Strict opt-in uses the pinned schema14 artifact, verifies/stages its bytes, verifies the actual locked Go and exact buildinfo, and preserves the no-env build branch.

Current upgrade CLI with fixed historical14 target: **1 test PASS / 0 skip**, all **5 original assertions PASS**. Missing artifact and wrong hash each produce the expected exit1/refusal before execution.3706 compiled/contract inputs remain unchanged.

Separate disposable historical lanes:

* schema14 original ActiveRecovery: **1 PASS / 0 skip**, **7 original assertions PASS**,226 source files and3394 compilation dependencies unchanged.
* schema20 original ReplayNative and BusinessNoGain: **2 PASS / 0 skip**, **21 original assertions PASS**,355 source files and3573 compilation dependencies unchanged. All206 recorded production inputs match; every extra source/test/helper/embed has explicit historical Git provenance.

Test executables are hash-pinned. The real fresh control built inside original tests matches a separately rebuilt same-source image: `92b788bcabdd06f23613890f8f69f8f6c086bbf132e335538b5c86450fdd0b1b`. Old203fe image is provenance only; absent4276 image remains absent. Original public fixtures and canary are newly generated; no old authority/private store is opened.

`historical-final-audit.json` is the consolidated audit. Two reporting-only parser mistakes are retained and explicitly corrected there using unchanged raw: initial W17 assertion-prefix parsing; baseline_hash versus actual stable_hash key. No product test was rerun to mask those mistakes.

These results prove historical contracts and the narrow current upgrade CLI targeting historical14. The four original current-main failures remain in their original receipts. Q10, current22 source qualification, LIVE/provider and formal/parent acceptance are not closed by this evidence.
