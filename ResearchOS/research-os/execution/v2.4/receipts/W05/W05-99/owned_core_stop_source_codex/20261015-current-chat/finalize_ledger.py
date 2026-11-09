"""Derive final cut ledger from preserved intermediate candidate ledger."""
from pathlib import Path

root = Path(__file__).resolve().parent
src = root / "candidate-2ed14cf7-final" / "CUT-LEDGER.md"
dst = root / "candidate-56e44e1b-final" / "CUT-LEDGER.md"
text = src.read_text(encoding="utf-8")
text = text.replace("candidate 2ed14cf7", "candidate 56e44e1b")
text = text.replace("Final five-package run: `20261015T105830.625365Z-test-owned-stop-final-acc27225`", "Final five-package run: `20261015T110425.453565Z-test-owned-stop-extended-a2b6ad4d`")
text = text.replace("Final CLI build: `20261015T105852.386809Z-build-owned-stop-after-journal-9cc5cd91`", "Final CLI build: `20261015T110453.399222Z-build-owned-stop-extended-a9a0d43b`")
text = text.replace("PARTIAL: original durable Begin/Scan history unavailable; no full schema24 safety fixture in this commit.", "PARTIAL: original durable Begin/Scan history unavailable; new schema24 safety fixture now exercises the old RUNNING/UNKNOWN subject.")
text = text.replace("Safety catalog counts PREPARED/STARTED/UNKNOWN effects in source; no complete schema24 fixture row set/assertion. | NOT PROVEN at this commit.", "`TestOwnedStopSchema24SafetyRejectsUnresolvedEffectsAndOtherDispatches` applies actual 0001–0024 SQL migrations to six new DBs. The exact old RUNNING/UNKNOWN baseline passes; additional PREPARED/STARTED/UNKNOWN effect, other PREPARED dispatch, and other RUNNING Run each fail under a reserved barrier (`20261015T110147.025245Z-test-schema24-safety-01-f3a2fe32`). | Native SQLite schema24 fixture PASS; original current census unavailable.")
text = text.replace("`TestOwnedStopOnlineBackupWALAndLogicalCAS` proves logical drift detection, and Commit source maps poststop census/authority errors to `STOP_OBSERVED_MAINTENANCE_BLOCKED`. | PARTIAL: real Commit poststop failure path fixture not exercised at this commit.", "`TestOwnedCoreStopPostflightRealLeaseBlocksLogicalDrift` uses the actual owned fixture executable, same-retained-handle Windows stop, real lease reacquisition, then a real poststop SQLite row insertion. It calls `finishAfterNativeExit`, the exact function called by Commit after barrier release, and asserts a durable `STOP_OBSERVED_MAINTENANCE_BLOCKED` receipt with two-row census rather than the one-row baseline (`20261015T110353.343840Z-test-postflight-01-c1ebf9a8`). | Native/SQLite postflight branch PASS; full Commit entry still unavailable without independent trust anchor.")
text = text.replace("Source blockers:", "Final commit `56e44e1b8a5086c26074c13db14173c5b1ab6116`, tree `38f4225f2e73246b188b79ee846fdff607e33619`, binary-safe patch SHA-256 `7b9beeace0518d73ccd931f41fe846c9cc5bb47d2a47c3846f7563df83fd4fe4`. Intermediate commit `2ed14cf7` and its ledger/patch are retained.\n\nSource blockers:")
dst.write_text(text, encoding="utf-8")
print(dst)
