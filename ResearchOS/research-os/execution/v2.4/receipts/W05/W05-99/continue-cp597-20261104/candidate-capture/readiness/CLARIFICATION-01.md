# Clarification 01: the candidate is writable before this check

This is a design clarification to NEXT_SLICE.json, with the first frozen MANIFEST.json retained byte-for-byte. It changes no source, authority, scope registration or acceptance state.

The private context freezes the allowed roster, suite semantic version/hash, fixed go.mod/test hashes, policy/toolchain hashes and trusted identity snapshots. The phrase “frozen source inventory hash” in its suggested fields means that roster/fixed-input specification; it must **not** mean a candidate content digest captured at prepare/confirmation time. Candidate code is the one explicitly writable file.

The existing Host check takes its current source snapshot after the original authorized edits and constructs staging manifest B. BeforeResume must compare the final second-copy candidate bytes against this **check-time Host staging manifest B**, together with frozen fixed-file digests. It then validates and retains precisely B. No later workspace reread or reserialization from a path is allowed.

Add these temporary fixture controls to the proposed next slice:

- Prepare saw candidate A; an original authorized write produces B; this check stages B; final private copy B is accepted as a structural snapshot. This is not business PASS.
- This check stages B; final private copy C is rejected, even if C is valid Go or semantically equivalent.
- Fixed go.mod/test hash, roster, suite, binding or native identity changes are rejected rather than treated as authorized candidate edits.

This clarification prevents freezing away the legitimate repair while retaining the intended same-byte compiler-input witness. It does not construct any trusted original origin, approved business plan, native proof or factory producer.

