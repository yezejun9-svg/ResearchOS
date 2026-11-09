# C51 diagnostic event crosswalk

The `interim_tool_observation` ordinals 1–34 and 37 describe distinct tool invocations without separately redirected recipe/raw/native-exit files. They are not the same invocations as numbered commands 018–049. The old interim ledger preserves their observed outcomes; it does not turn them into persisted native exits.

Interim 35 is the same eight-command batch as numbered 034–041. Its one failure is numbered 039; seven other native exits are 0. Interim 36 is the same eight-command batch as numbered 042–049, all native exit 0. Count each command once.

Interim 27 is the first isolated 085b baseline attempt, which failed to compile because the sparse worktree omitted `evaluation`. Interim 28 is the following baseline invocation after adding `evaluation`; it failed at `client_command_identities`. Numbered 032 is a **later repeat** of the same baseline test in the same clean detached 085b worktree, captured with recipe, raw output and native exit 1. They are separate invocations with the same causal fixture defect. Numbered 032 is the durable baseline proof; count the fixture defect once as one cause, without erasing the distinct attempts.

Interim 29 is the first candidate SQL22 fixture construction failure (missing real Task binding). Interim 30 is its successful corrected test before an explicit fixture precondition was added. Numbered 033 is a **later captured rerun** after that assertion was added, native exit 0. They are separate invocations.

Interim 37 is the first unredirected blocked-driver transaction lifetime test, native exit observed as 0. Numbered 050 is a later captured domain suite that includes the same named test after the final C51 source edit; it is a different invocation. Boot six source changed during 050–052, recorded in the before/after hashes.

Numbered 034–041 are diagnostics because `TEMP`, `TMP`, and `GOTMPDIR` were not explicitly directed into the authorized fixture root. Numbered 042–049 are later own-environment invocations and correspond exactly to interim 36. The successful later run does not delete numbered 039 or the environment deviation.
