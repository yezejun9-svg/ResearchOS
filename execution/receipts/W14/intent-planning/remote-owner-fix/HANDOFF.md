# I1 remote Owner authority correction

Source: `867dfa7c24828f935234d047cbe32c64451c6384`, based on frozen I1 source
`edb9543` and evidence `82dee92`. Status: execution reported; independent delta
review pending. The original source manifest and evidence remain unchanged.

The reviewer confirmed that `planningOwner` reconstructed a remote device's
stored roles/grants without intersecting them with the issuing Owner's current
authority. `planningSnapshot`, `compileIntentPlan` and `advanceIntentProject`
all call this shared helper. It now closes the grants cursor and calls the existing
`constrainRemotePrincipal` before checking the resulting Owner role/project grant,
matching authentication's current-source behavior. Only two domain files changed.

## Directed verification

Pinned Go executable: `D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe`.
Environment: `GOENV=off`, `GOTOOLCHAIN=local`.

- Before fix: `go test ./internal/domain -run '^TestIntentRemoteOwnerCurrentIssuerAuthority$' -count=1 -json`
  exited 1. `before-fix-test.jsonl` retains the positive case PASS and both revoked/
  removed-grant cases FAIL because Goal acceptance incorrectly returned 201.
- After fix: `go test ./internal/domain -run '^TestIntent(RemoteOwnerCurrentIssuerAuthority|StaleAuthorityCannotAcceptOrCompile)$' -count=1 -json`
  exited 0. `after-fix-test.jsonl` contains two top-level PASS tests and three
  remote-authority subcases. `git diff --check` passed.

The new test pairs a real fixture device through HTTP, explicitly grants OWNER,
submits/accepts an INTENT through that credential, asserts the actor is the device
ID, produces a fixture GoalBrief and independently accepts its Task. It then
changes only the issuer authority before attempting Goal acceptance with the
still-authorized independent verifier. The device's own grant remains active.
Current issuer returns 201 and creates one business Goal; revoked issuer returns
401 and removed project grant returns 403. Both rejected cases persist neither a
business Goal nor a Goal AcceptanceReceipt. The prior local Owner revocation
regression also passes.

This is domain/HTTP fixture coverage. No native, browser, model/provider or full
suite rerun was needed for this correction. No S2/R2 paths, original evidence,
production state or policy-blocked cleanup path were changed. The previously
reported hygiene blocker remains exactly as documented in the parent HANDOFF.
