# Native attempt 01: PRODUCT_PATH_TYPE — read-only diagnosis

**Conclusion:** The most likely failing inventory row is `runtime/electron/resources/default_app.asar`. The exact row was not logged by the native attempt, so this is a high-confidence inference, not an observed Electron `lstatSync` value. The attempt remains unresolved; no source, build, product process, or original data was changed in this diagnosis.

## Evidence

- `product_host_native_20261028/attempt-01/UNRESOLVED.json` records Electron PID 37624 loading the product app, then `PRODUCT_PATH_TYPE` at `product-layout.js:31`, called from `relativeFile:42` and `loadProductLayout:93`. The Playwright 45-second timeout is the outer error. The app load error is the direct failure. No first witness or provider connection was recorded.
- In commit `448af57c208a3f29199d10e0fa9d9c7311776fad`, `apps/desktop/main/main.js:30` calls `loadProductLayout(REPO)`. `apps/desktop/main/lib/product-layout.js:58` defaults `fsImpl` to `node:fs`; `exactPath:20-36` requires `lstatSync(...).isFile()` and exact native real path; `loadProductLayout:88-97` checks every inventory file's type, bytes and SHA-256.
- The build04 marker contains exactly one `.asar` inventory row: `runtime/electron/resources/default_app.asar`, 109371 bytes, SHA-256 `ecd526468d13b0d4d9d9f430e0834f25dbcdcfd910b6e38f59e6c66192bd41c4`. A read-only pinned Node 24.9.0 physical scan of all 133 rows found zero type or real-path mismatches. The archive is a physical regular file and its bytes match the marker. Raw result: `physical-node.json`; recipe: `physical-node-recipe.json`.
- The bundled Electron is 37.10.3. Its [version-matched ASAR guide](https://github.com/electron/electron/blob/v37.10.3/docs/tutorial/asar-archives.md) documents that Electron patches Node `fs` to expose archives as virtual directories and recommends its built-in `original-fs` when reading the archive as a file for checksum verification. This matches the source's physical-file contract and observed error. The [Electron process API](https://www.electronjs.org/docs/latest/api/process) also exposes `process.noAsar`, but that is process-wide.

## Smallest source change to scope

At `apps/desktop/main/main.js:30`, pass Electron's `require('original-fs')` as the second argument to `loadProductLayout(REPO, physicalFs)`. The helper already accepts `fsImpl`, so `apps/desktop/main/lib/product-layout.js` needs no change. Keep its type, symlink/junction, native real-path, length and SHA checks. Use `original-fs` for the complete physical inventory pass so `.asar` bytes and metadata are read from the on-disk archive. Check in the target Electron runtime that `originalFs.realpathSync.native` exists, since `exactPath` calls it. This is a recommendation for a future Root-registered scope, not an implemented patch.

## Focused regression and mock impact

- Add a targeted case to `tests/ui/desktop/product-host.test.mjs`: a regular `.asar` file is inventoried and accepted with physical `fs`; changed bytes, a directory in its place, and a redirected path still fail their existing type/hash/path checks. A test double can model Electron's virtual `.asar` directory to show why the default `node:fs` route fails.
- The independent VM4 source harness is `product_host_independent_20261028/main-lifecycle-mock.cjs`. Its `imports` table at line 47 and `require(name)` branch at line 66 currently have no `original-fs`; adding the main.js import would otherwise cause `UNMOCKED_IMPORT:original-fs`. Adapt that harness to return a physical-fs mock for `original-fs`, and assert the loader receives it. This harness lives in the review receipt, not the production source scope.
- A fresh full layout build must bind the changed main.js source commit and all inventory/dependency hashes. Existing product-host Node and VM probes can then be evaluated at the new source identity.

## Proposed dedicated native filesystem probe — separate Root authority required

Use a fresh isolated probe app directory and profile with the **build04 Electron executable**. The probe app's main script only reads the build04 marker/archive and invokes the existing `loadProductLayout` twice: first with Electron's patched `node:fs`, then with `require('original-fs')`. Capture both `lstatSync` type results, loader result/refusal, archive SHA, executable identity and raw exit. Expected: patched `fs` reports the virtual directory and loader refuses `PRODUCT_PATH_TYPE`; `original-fs` reports a regular file and loader accepts the unchanged build04 marker. Call `app.exit` without opening a BrowserWindow or loading the product app; the probe must not start Core, UI or business code. Use a fresh `LOCALAPPDATA/APPDATA/USERPROFILE/TEMP` root and no original data. **Do not execute until Root registers this exact probe.**

The direct Electron `lstatSync` result, compatibility of `original-fs.realpathSync.native`, and successful loader outcome remain unverified until that probe runs.
