# CP367 / OW171 independent Source review

Decision: REQUEST_CHANGES. The v1 writer must not execute against canonical state.

P1: register_cp367.source.py transform unconditionally sets root_next_failure_ordinal_live to facts.next_failure_ordinal and later_diagnostics_observed_after_cutoff to an empty list. The sealed source-preview-proof already records Root live next 949 and pending 948, while the proposed checkpoint has live next 948 and no later pending diagnostics. The pure AST counterexample independently reproduces this loss. Preserve the immutable cut 947 / cut next 948; bind a separate current Root live-context typed ref and preserve the complete pending interval with exact original refs. Do not revise the existing cut or replay the old original call.

Verified: all 191 finite exact inputs were hashed and held by the real SourceReadGuard; all acquired handles closed, no errors, retained count 0. The reviewer executed selected pure Python source functions only. All four current canonical file bytes remain unchanged. No writer.main, update_pair, Main source write, Go, SQL, CLI/API or model call occurred.

26 checks cover actual Source scope and independent non-author review decision, exact ordered seven targets, exact Owner/worker shapes, rejected extra keys, bad bound digest/size, author self-approval, formal bool and dispatcher mutations; existing 934 rows, 11 new rows 937..947, literal original exit qualifications, registered total 945, exact worker/Owner addition, complete semantic inverse, and equality to the author preview apart from timestamp. Raw original IO files and registration links were retained and verified. 945 retains NULL outer/Python/native; all product Native exits remain NULL. The valid cut and inverse do not qualify the live overwrite.

There were no new original failures in this review. The successful P1 counterexample is a finding, not a failed original invocation. Formal accepted delta 0; Main adoption false. Actual CP367/OW171 registration and Main adoption remain pending a corrected Source package and fresh review.
