# C7 seal audit assertion failure 709

The first read-only post-seal audit failed because its command hard-coded 14 manifest members. The sealed manifest actually contains 16; the diagnostic found zero digest mismatches, and a corrected read-only check matched every manifest member to the actual sealed directory and verified 6 input and 8 source pins. The C7 Source, handoff, and manifest were not edited.

This packet exports complete stored commandExecution projections for the failed assertion, diagnostic, and corrected audit. Stored aggregatedOutput is not split stdout/stderr or raw console bytes. No bytes are reconstructed.
