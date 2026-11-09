# SourceReadGuard Source handoff

Status: **SOURCE_ONLY / PURE_CONTROLS_PASS / REAL_WINAPI_NOT_RUN**. This immutable candidate closes the gap between a source pin check and a later path-based consumer by holding a read handle. It does not run the Root controller, Resume, Job, Host, native provider or database.

## API and Root C4 integration

`SourceReadGuard()` only stores caps and an optional API factory; it does not load `kernel32`, open a file, start a thread or create a Job. Default limits are 128 MiB per unique file and 512 MiB across unique files. Root should pin these constructor limits. `acquire(references)` accepts a nonempty list of **exact** `{"path": absolute_local_drive_path, "sha256": plain_64_hex, "bytes": integer}` records. It rejects extra fields, conflicting normalized duplicate paths, out-of-cap files and UNC/device paths before opening anything. Equivalent normalized duplicate paths share one handle and one byte buffer.

Root C4 should first perform its independent literal source pin/import, construct the guard, and then call `acquire` over the entire reviewed tuple **before any Source consumer**. That tuple includes review controller, observer, hooks, worker, runner, Python/Root helpers and this guard module itself. The guard cannot bootstrap trust in its own import. Root then passes `guard.get_buffer(path)` (or `guard.buffers[ntpath.normcase(ntpath.normpath(path))]`) to each consumer, never reopening a source path to parse or hash after `acquire`. Keep the object and its handles alive across Resume, the held worker paths and the complete owned Job cleanup. In the outer `finally`, call `close()` and pin its JSON-safe observation. A `retained_handles_count > 0` or `closed=false` is a cleanup failure; do not report all handles closed. The same pattern applies to a separately owned Host binary/Node/bundle tuple, held until that whole Job cleanup.

```python
from source_read_guard import SourceReadGuard

guard = SourceReadGuard()
try:
    guard.acquire(exact_reviewed_references)
    worker_source = guard.get_buffer(worker_path)
    # Root consumes all other buffers, resumes the owned Job, then observes cleanup.
finally:
    close_observation = guard.close()
    # Root records close_observation; failed closes retain their handle in guard.
```

## Windows behavior and failure evidence

Only `acquire` creates `_Win32API`. For each unique local path it calls `CreateFileW(GENERIC_READ, FILE_SHARE_READ=1, OPEN_EXISTING)` with **no** `FILE_SHARE_WRITE` or `FILE_SHARE_DELETE`; compatible Python/Go child reads may continue until `close`. It checks `GetFinalPathNameByHandleW` against the normalized absolute authorized target, uses `GetFileSizeEx`, reads through that same held handle with `ReadFile`, rechecks size, and compares exact length and SHA-256. `buffers` stores only those verified bytes. A failure during acquisition is recorded, then every opened handle receives a close attempt. Failed `CloseHandle` calls remain represented by private handles and a nonzero retained count; the observation never serializes raw handle values, tokens or file contents. Calling `close()` again retries retained handles and preserves earlier errors.

The in-memory substitute controls cover constructor purity, normalized de-duplication, verified buffer delivery, a second-file failure closing both handles, conflicting duplicates, and failed-close retention/retry. They do **not** prove Windows sharing behavior. Pure control stdout is pinned as `pure-controls.json` and reports `real_winapi_calls=0`, `target_file_reads=0`, `provider_requests=0`.

## Exact Source pins

| File | SHA-256 | Bytes |
|---|---|---:|
| `source_read_guard.py` | `e61a1b078a40b7d8bda1116944c42e0ddd37644ad5689917a164b6c5d67d9c96` | 10646 |
| `pure_controls.py` | `babf7e193dc974965ab9ffb0675be6912139273e9a23e46bb18479a1ae25f5e6` | 4637 |
| `pure-controls.json` | `c79d59cd6ba4bfb9c6b88bf7e4c86f5cfa3e17a84223f29ca6511635c5c2cb4c` | 379 |

`manifest.json` pins this handoff and every local member except itself; Root receives its SHA-256 separately.

## OPEN before execution

- Root must independently review the module and its C4 callback wiring, then run an owned real Windows probe proving `CreateFileW` sharing, final-path normalization, child read compatibility, replacement denial and `CloseHandle` cleanup on the target files. Pure controls cannot certify these OS behaviors.
- The verified bytes remain trusted only while all relevant handles stay open. Root must prove the guard lifetime spans every Source consumer, Resume and Job cleanup; a process crash still requires OS/Job cleanup evidence. This module does not start a watchdog or native Job.
- Source files larger than configured caps fail closed. `acquire` accepts drive-root absolute paths only; any future UNC/device-path need needs a separately reviewed contract revision.
- This guard pins file bytes and holds file handles; it does not prove the larger Root authority, provider budget, task acceptance or model result.
