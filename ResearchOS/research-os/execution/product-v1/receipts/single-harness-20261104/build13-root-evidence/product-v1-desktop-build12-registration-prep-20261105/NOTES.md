# Build 12 registration preparation

This is a C-only preparation for Root review. It does not register a scope, create a worktree, or run the build.

- Registrar: `prepare_product_v1_desktop_build12.py` (SHA-256 in `MANIFEST.json`). It derives from the build11 registrar, targets fresh build12 paths, checks 67 integrated source pins, binds the qualification-build and native-prelaunch scopes, adds `/cmd/` and `/tests/desktop/` to sparse checkout, and pins the helper plus its receipts.
- Actual scope command: Python launches `build_desktop_serial12.py`, followed by the pinned `apps/desktop/build-development.py` and the registrar-generated original flags. The wrapper validates Main/source pins and the exact builder/tool inputs, sets `GOMAXPROCS=1`, then runs the app builder in-process. The wrapper and registrar are both scope inputs.
- Both candidates passed UTF-8 round-trip and Python compile checks. These checks compiled source text only; neither script was executed.
- The malformed first draft remains byte-for-byte preserved as `prepare_product_v1_desktop_build12.draft01-bad.py`; its SHA and syntax diagnostic are recorded in the manifest.

Root should review the files and confirm the current Main HEAD and bound-scope receipts before registering and invoking the build-only scope.
