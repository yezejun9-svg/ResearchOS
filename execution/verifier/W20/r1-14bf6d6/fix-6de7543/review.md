# R1 fixture package independent review

PASS_R1_FIXTURE_PACKAGE_SLICE at 6de7543da751ace1d2d603a751f520e5fed71caa.

The two P1 findings are resolved for this slice. Two independent offline builds match the author archive SHA-256 2fe064a581bf5f75608831bc696074bda5cee581deaf01e5810e54e2c643a50a. All 385 manifest entries were checked; all 344 bundled source/script entries match the frozen Git version with exact Git blob bytes. Three modified/untracked-input attempts are rejected. Eleven build assertions and 34 final fixture assertions pass.

Wrong PID, creation time, copied identity/data binding, launch GUID and release root each refuse stopping, retain the identity record and leave both owned hosts alive. Valid stop kills only the intended held process and preserves its database. A stale stopped identity also refuses.

The first fixture attempt remains 15 PASS / 1 FAIL: its health-only assertion failed after correctly refusing the wrong creation time. The original helper did not retain the HTTP exception, so the cause is undiagnosed. A fresh run of the same product using recorded direct HTTP observations and independent OS process identity checks passes; no product patch occurred between these runs.

This approves only the R1 fixture-package slice. It does not qualify W20, A15, clean Windows, final-schema upgrades or LIVE. The manifest still discloses 27 license gaps. Author-only tests are identified separately in review.json.
