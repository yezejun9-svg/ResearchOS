# Coding client repair v3 candidate

Candidate `2fda8155d457784c22655be553af87b8f3b114f2` addresses the three findings in the rejected B20 review. The desktop manager retains an exact late PREPARE terminal after the caller's 45-second timeout, permits a new PREPARE only after an authoritative bound ERROR and explicit corrected retry, and rechecks live authority synchronously immediately before the CONFIRM write. The added manager and Chromium cases exercise an ERROR followed by Go resource reselection and explicit retry. Four files changed within the eight registered paths; the source worktree is clean.

`source-bundle.json` freezes the eight registered source hashes and candidate commit. `c-build-binding.json` binds those files to the C worktree, its 6,439 recorded build inputs, the native binary, descriptor, build logs, and copied test cases. Seven registered files appear in the build input inventory; the continuity browser driver is a test input captured by its invocation and source bundle. The full build had zero input drift.

Local evidence: 32/32 coding and management boundary tests, compiled Go validator tests, four Chromium synthetic scenarios with zero model calls, and 218/218 complete desktop tests including actual offscreen Electron renderer cases. `raw/v3-c-bound-all-desktop.*` preserves the first complete-suite attempt: it omitted `RESEARCHOS_DESKTOP_ELECTRON`, so two renderer cases stopped before product logic. `raw/v3-c-bound-renderer.*` and `raw/v3-c-bound-all-desktop-corrected.*` document the corrected environment and passing rerun.

This is a source-bound local candidate. Independent review, Main integration, live-provider qualification, and formal acceptance remain pending; formal and parent acceptance increments are zero.
