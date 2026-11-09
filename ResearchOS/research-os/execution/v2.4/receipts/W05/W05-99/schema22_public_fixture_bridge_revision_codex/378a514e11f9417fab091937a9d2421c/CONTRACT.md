# Schema22 fixture bridge unused-import revision

This revision removes only the eight LF-terminated bytes of the unused time import from candidate-root/internal/domain/backup_configuration_upgrade_test.go. Every other byte in that file, the current helper, both historical22 overlay files, and all assertions are unchanged from sealed Source 3d7d237d23244950a6d9008753e3fde9.

Root's existing historical regression failed during Go compilation with an unused-import diagnostic; zero tests ran. Those artifacts remain pinned and are not recounted. This Source author performed byte/hash checks only and did not run Go, native programs, SQL, models, DPAPI, signing, or production operations. Root must rerun the original complete domain compilation and historical suite without skipping or removing tests. This handoff does not independently accept the change.

source_refs keeps the existing dictionary shape: candidate-root-relative member name -> {path, sha256, bytes}. It contains two current test files. historical22_overlay_refs uses the same shape and contains the unchanged historical helper Go file and its embedded input JSON; these belong only in the isolated old22 copy. Prior build-profile and production/independent-review gates remain applicable.

Failure783 records this author's first constructor assertion, which incorrectly assumed CRLF. Its four-file partial namespace is preserved and is not a deliverable. The corrected revision uses a different namespace and deletes the actual LF line. Earlier failures779-782 and all previous accounting remain unchanged.

