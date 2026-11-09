# CP368 W05 Source review

Decision: REQUEST_CHANGES.

P1 CP368-W05-P1-SHARED-LIVE-STALE: the pure writer transform leaves shared current live fields at ordinal952 and an empty pending list. With validated live954/pending953, only the new mu_sdk_r368 block updates. A continuation reading the unversioned shared fields can reuse a previously assigned ordinal and miss pending evidence. Update both shared fields from the same validated live input; restore the entire old work_in_progress in the inverse. Preserve revision-named historical cutoffs and mu_sdk_r367.

45 independent checks and 12 negative controls completed successfully, with 187 finite inputs held by SourceReadGuard and all handles closed. The full inverse, old949 raw and semantic prefix, original952 append, original W05 parent owner, two active parents, seven-target adoption proof, W05 Source/review and external caller argument contract were verified. The actual transaction and W05/product callers were not executed. Trusted helper validation used only its original AST prelude through a stubbed WinDLL boundary.

Reviewer read failure953 is preserved separately with original tool call and output; SourcePython/Go/Native/Model were not invoked. Root current live954, pending953; Sourcecut952/next953 remains immutable. This successful Source finding is not another original execution failure. No Main, Canon or prior Source package was modified.

