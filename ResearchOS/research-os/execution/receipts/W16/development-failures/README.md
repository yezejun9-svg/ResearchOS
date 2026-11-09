The C10 output was preserved verbatim from exec session 25287 after the separate
rule-author fixture lacked the existing EXECUTOR role required to seal its own
artifact. Exit was 1. The corrected fixture grants that principal the existing
artifact-producing role; it remains distinct from the candidate author and cannot
change the current frozen suite. This was a test setup failure, not a passing
acceptance. Later full-run receipts retain their own captured stdout/stderr.
