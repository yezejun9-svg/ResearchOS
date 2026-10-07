# W20 final bundle independent review — PASS_BOUNDED_PACKAGE_FIXTURE

Reviewed source: `f51049149b6ba0d53c83f5bb5cf0274ea1039c24`.
Reviewer: codex:/root/control_drain. Scope: package contents, reproducibility, declared licenses and one current-user fixture invocation. This review does not issue new acceptance for the reviewer's R2 implementation; that source has a separate independent review.

Both independently inspected archives are byte-identical: SHA256 `a4b2474d445edd2b2bfea5c572689812aa1c6372262b0201024ff4d2cc78137c`, size 42,083,043 bytes. Manifest SHA256 is `6b6ed4f039ae2dd944e21a6265c955fd6ce196946814fa40c77f770a3aed7311` in both. Every ZIP file hash/size and manifest byte was independently recomputed, and ZIP CRC, order, duplicates, path containment and exact manifest inventory passed.

The 491 ZIP entries comprise 439 source/script entries, 4 Windows AMD64 executables, 11 web build assets, 18 Go license texts, 18 npm license texts and the manifest. All 439 source/script entries match exact frozen Git blobs at f510491; the three scripts/ aliases match their ops/release originals. The independent expected source inventory confirms no missing eligible product source. The archive contains all twenty exact frozen migrations and declares fresh/final schema20 with populated activation still blocked. The four binaries are control/runtime/backup/release_host. Their PE architecture, actual Go 1.27.1 module/toolchain build metadata, GOOS/GOARCH, trimpath and CGO settings were inspected without executing them. The union of 18 compiled Go dependencies exactly matches SBOM name/version/sum records.

All 43 npm lock entries appear exactly once: 18 installed packages were checked against local installed package metadata and actual license bytes; 25 are optional-not-installed, not missing required packages. There are exactly two disclosed license gaps: ResearchOS main module has no license file; @rolldown/binding-win32-x64-msvc has no license text. They remain open release gaps, not silently treated as complete licensing.

The three construction-only files tests/ui/browser_smoke.py, tests/intent/browser_intake.py and tests/evolution/control_private_recompute/main.go are absent and explicitly named in source_checkout_gap. Known developer absolute-path patterns were absent from all archive bytes in UTF-8/ASCII and UTF-16LE. No runtime credential/key/database/PID/.env files appeared in the exact package inventory. This is an inventory and known-pattern review, not a universal secret-scanner certification. Operational credentials are not needed or supplied for the fixture.

## One original fixture check

The existing frozen tests/release/check.py was invoked exactly once against archive A with --run-fixture, using hash-verified pinned Python 3.14.3. Exit 0, 28 assertions PASS. Its actual stdout/stderr and exit code are retained. It extracted to a fresh temporary root, used fresh external data directories and loopback listeners, checked two fixture instances, refused wrong-instance and wrong-creation records while both instances survived, stopped only its own recorded fixture instances, verified data preservation, and completed temporary cleanup. Integrity negatives covered modified binary, missing contract, extra file and path escape. release.reproduce stayed UNBOUND with nonzero exit.

No reserved service/process/database was accessed. No SCM, protected-store broker, production provider or populated database was activated. The fixture stop script intentionally terminates the identity-checked disposable instance; it does not prove the production normal drain/checkpoint path.

## Preserved diagnostics and limits

The earlier b894f78 build failed before producing a ZIP because tests/intent/browser_intake.py contained a developer tool path. Root preserved that build failure. f510491 adds only the exact construction-file exclusion and consistent disclosure/check updates; strict unsafe-input rejection remains.

The first supplemental read-only binary metadata audit failed in reviewer code with KeyError '-ldflags'. Go build-info did not expose that optional field. The original stderr is retained. After root authorized one correction, the second metadata-only audit passed. It records linker flags as NOT_REPORTED_BY_BUILD_INFO, without inferring them from manifest prose. The frozen builder recipe/raw invocation and two byte-identical builds support reproducibility; no linker flags are claimed independently read from absent metadata. The original product checker/native fixture was not repeated.

A15 clean Windows, independent SCM identities/ACLs, normal LIVE operation, full populated-database activation and complete actual release cutover/rollback remain NOT_RUN/OPEN/CLOSED as declared. W20 formal acceptance remains NOT_ACCEPTED. No new blocking discrepancy was found in this bounded package/current-user-fixture review. This conclusion binds the exact f510491 archives and raw outputs, not subsequent main commits.
