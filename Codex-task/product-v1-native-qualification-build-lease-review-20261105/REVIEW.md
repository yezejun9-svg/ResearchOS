# Qualification build-only source lease review

Decision: **APPROVED_SOURCE_LEASE_WITH_CONSTRAINTS**. The proposed exact three files are sufficient; no Host/runtime expansion is needed. This approves implementation of the design, not an implementation or execution.

- Keep all-three-or-none inputs and default closed. Only Core receives the two fixed private linker variables.
- Use an explicit CLI hash format; the linked Host value must be `sha256:<64 lowercase hex>`. Current Host rejects a bare digest.
- Validate original absolute paths and all ancestor reparse bits before resolution. Reject aliases, UNC/device/ADS/control/semicolon paths. Root must already exist; builder never creates or changes external root/S. Mark derived S as unverified if it is only derived.
- Structured argv avoids shell parsing but does not solve Go `-ldflags` tokenization. Use verified quoting or reject unsupported spaces/quotes while retaining Unicode. Clear `GOFLAGS` for every Go/nested build command; assert only two linker assignments.
- Copy the predeclared-hash helper to one fixed fresh bundle path; verify source/destination before and after. Reject collision/drift and retain failed artifacts. Never execute the helper.
- Add the helper command prefix and new pure test to source snapshots. Distinguish current source snapshot from historical prebuilt-helper provenance: Root must bind the helper build receipt/closure; a current `go list` cannot prove how that binary was built.
- Record exact paths, validation status, hashes/sizes, linker values, actual Core argv, resulting Core hash, provenance and inventory. Preserve BUILT_NOT_NATIVE_TESTED and zero acceptance.

Proposal SHA256: `aef64f09b2a2cb063efc39d9cd5b7005cc1251a1ce3fa03874b031f373037fd7`. Current source pins and detailed constraints are in REVIEW.json. No tests/builds/Native/model execution, no production or D writes. Next steps are exact-three-file author freeze, independent review, and separately registered Root build.

