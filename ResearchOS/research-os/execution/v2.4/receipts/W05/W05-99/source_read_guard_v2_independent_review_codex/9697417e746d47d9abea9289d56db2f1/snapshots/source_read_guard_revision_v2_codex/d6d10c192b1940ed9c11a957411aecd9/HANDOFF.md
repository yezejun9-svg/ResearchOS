# SourceReadGuard v2 Source handoff

Status: **SOURCE_ONLY / PURE_CONTROLS_PASS / REAL_WINAPI_NOT_RUN**. This immutable revision replaces the v1 source candidate after independent review found that forward-slash UNC/device paths could reach CreateFileW. The v1 receipt is preserved at `D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/source_read_guard_codex/68ac03921c9c4efd821c178dd934e16e`; its manifest SHA-256 is `099113490f7f894f0bcdc23e3d92ce31de1e4d4cac4883ec0dbc31d24f8f0a7c` (1899 bytes).

## Fix and preflight boundary

`_canonical` first normalizes `/` to `\`, then accepts only an exact ASCII `[A-Za-z]:` drive and one rooted separator in the tail. It rejects UNC/extended/device drives, drive-relative paths, alternate data stream colons, control characters, dot segments, repeated separators, trailing dots/spaces and DOS device components before `_api_factory` or `CreateFileW`. Both `C:/...` and `C:\...` are accepted; Unicode and ordinary spaces in components remain valid. The held handle final path must pass the same canonical rule and equal the authorized target.

This is an input preflight, not proof that Windows will resolve a local-drive path to local media. Root's real Windows probe must check actual final-target and replacement behavior under held handles.

## Root C4 integration

Root independently checks the literal source pin before import. `SourceReadGuard()` performs no OS action. `acquire(references)` accepts a nonempty complete reviewed tuple of exact `{"path", "sha256", "bytes"}` records; duplicates with identical pins share a single held handle and buffer. Source consumers use `get_buffer(path)` and do not reopen paths. Keep the guard alive through Resume and the entire owned Job cleanup, then call `close()` in an outer `finally`. A nonzero retained handle count or `closed=false` is a cleanup failure. Failed close attempts remain observable and retryable without exposing handle values.

The default caps are 128 MiB per unique file and 512 MiB total. `CreateFileW` uses `GENERIC_READ`, `FILE_SHARE_READ` only, and `OPEN_EXISTING`. The guard verifies `GetFinalPathNameByHandleW`, `GetFileSizeEx`, held-handle `ReadFile`, exact bytes and SHA-256. Failures attempt to close every opened handle.

## Evidence and literal pins

The pure in-memory controls retained the seven v1 baseline cases and added forward/backslash UNC/device rejection before adapter construction, drive-relative/ADS/reserved-path rejection and both local-drive separator forms with Chinese and spaces. The captured result is `pure-controls.json`, status `PASS_IN_MEMORY_ONLY`, with zero real WinAPI calls, target reads and provider requests. It does not establish native sharing or Job behavior.

- `source_read_guard.py`: SHA-256 `e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85`, 11404 bytes.
- `pure_controls.py`: SHA-256 `495222ff76c2e80bf5ca12aa270b6f4664ce059756d94595e6112d1d9edf3ef7`, 6135 bytes.
- `pure-controls.json`: SHA-256 `2920e3a29c6bbfef3e1949f67f0f38c5e4a2ca2c5586f7b6ef527014e90b1205`, 573 bytes.
- `source-pins.json` pins these files and this handoff; `manifest.json` pins every local member except itself. Root receives the manifest hash out of band.

Root still needs independent v2 review and a real owned Windows test of sharing, final-path resolution, replacement denial and close/retry behavior. This branch does not invoke native OS APIs, Host, provider, Job, Main or canonical state.
