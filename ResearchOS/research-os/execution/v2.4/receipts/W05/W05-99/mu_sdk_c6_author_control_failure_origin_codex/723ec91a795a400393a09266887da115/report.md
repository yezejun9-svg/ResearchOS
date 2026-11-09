# C6 author control failure 706

Read-only export of the exact current-chat commandExecution projection for the first failed pure control, with its original Source-add and subsequent Source-fix fileChange projections. The command failed with Python/commandExecution exit 1 because the fake fixture constructed ResidentSourceOwner directly. The correction used get_resident_source_owner; the current C6 package separately pins seven passing controls.

The stored commandExecution contains complete command, cwd, one commandAction, aggregatedOutput, status, exitCode and durationMs. It does not contain split stdout/stderr or raw console bytes. No unobserved bytes have been recreated. This evidence supplement does not modify C6/O4 Sources or claim native/provider/canonical execution.
