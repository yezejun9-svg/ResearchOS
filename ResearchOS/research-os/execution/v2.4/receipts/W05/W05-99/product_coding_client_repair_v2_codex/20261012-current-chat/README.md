# Coding client repair v2 candidate

Commit `b20c816ec346c1dad1534b18b02abbb4f47c4628` fixes the reviewed desktop coding authorization races in seven authorized source/test paths. The original source bundle remains frozen. `c-build-binding.json` binds its eight registered files to the C build-only worktree, the shared Git object store, the 6,439 build inputs, the native binary, the descriptor, and the captured tests. The full build logs and descriptor are copied under `raw/`.

The source-bound build finished with zero input drift. Local tests passed: 25/25 desktop boundary assertions, compiled Go validator tests, and Chromium normal, STATUS recovery, and refresh-retry scenarios. Each browser run recorded zero actual model calls. The first compiled Go test invocation failed because PowerShell split the unquoted `-test.v` flag; its raw stderr and invocation are retained. The quoted retry passed.

These are source-bound local and synthetic UI results. The candidate has not been integrated into Main, installed into a managed Core, qualified against a live provider, independently reviewed, or formally accepted. Formal and parent acceptance deltas remain zero.
