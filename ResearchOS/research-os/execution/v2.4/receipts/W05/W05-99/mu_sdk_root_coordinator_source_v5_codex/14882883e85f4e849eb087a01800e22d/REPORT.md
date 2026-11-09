# Root coordinator v5 Source candidate

Decision: IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW. This Source packet grants no execution, runtime qualification, or formal acceptance.

R01: invocation comparison now requires the exact argument count, flag order and non-path values. Only binary, seed, receipt and cwd paths use absolute Windows Path equality; parent path components and relative paths are rejected. Finalize follows the actual existing caller order: -phase finalize-prepare -seed PATH -draft-goal-id ID -receipt PATH. Actual runtime and finalize receipts pass unmodified.

R02: every one of the four original Job closures is pinned and checked. The two continuation entries must equal their separately pinned closure records. All four must bind original before-resume identity, assigned_before_resume=true, resumed=false, original lifecycle parent PID, actual invocation process PID/creation time, native Job cleanup, typed finite fresh observation window, original primary exit code, and both producer/watchdog duplicate closure. Normal Host requires the explicit successful planned teardown with code 0xE0000508 and no timeout; the other three native exits must be zero.

The historical lifecycle owner PID belongs to the original closed preparation parent, never the future MODEL_TRIAL parent. MODEL_TRIAL SourceReadGuard holds the caller Source and all four closure/invocation/before-resume refs. NO_PROVIDER verifies the same original public chains without launching candidate native work.

Templates add normal_host_closure_ref, cli_goal_closure_ref and staged_caller_source_ref; both modes carry the preparation closure refs. Actual record placeholders remain unfilled. The existing 24 fixed roles, current helper Source/compile evidence, one 300-second admission/qualification/ordinary sequence, no-retry rule, once path, ArtifactRef hash and retained-parent behavior remain in place.

One constructor completed successfully. Two pure control groups pass using unmodified actual public receipt chains plus 9 argv negatives and 22 layered cleanup negatives. Only AST-extracted free functions ran; the coordinator class/module was not imported or executed, and no actual SQL, native process, WinAPI or provider call was made. Unrelated methods, including the entire trial execution and retention pipeline, are AST-identical to C4; full-byte inverse reconstruction is verified.

The independent C4 review and actual component review are input evidence. Prior Source packets and Main/canonical files were not changed. Prior failures were not recounted; this version has zero new tool failures.

