# Observer v2: actual launch binding

Status: `SOURCE_PREPARATION_ONLY_WITH_OPEN`. This revision fixes observer portions
of `CTRL-R06` and the extra-environment counterexample in `CTRL-R04`. It does not
claim the complete controller chain is ready. Root's canonical transaction
ownership (`CTRL-R02`) and independent Job deadline enforcement (`CTRL-R05`)
remain OPEN, alongside actual callback/Host/phase-seed prerequisites.

The previous v1 package is retained unchanged. The new runtime entry point is
still `observe_assigned_before_resume(context, *, process_handle, thread_handle,
job_handle, pid, creation_filetime)`. In addition to the v1 context, Root's next
controller revision must provide `phase_worker_source` and `python_binary`, both
exact public `{path, sha256, bytes}` pins.

The independent review schema is now
`researchos.mu-sdk-controller-observer-independent-source-review.v2`. It requires
`phase_worker_source_ref` and `python_binary_ref` as well as the four existing
source refs. A v1 review is rejected even if labeled `READY_SOURCE_ONLY`. Missing
pins, source-author/Root/program self-review and `REQUEST_CHANGES` also fail.
The package's template has null actor/decision and is not an approval.

The actual live `run_owned` frame must have this exact argv:

```text
<pinned Python> -I -S -X utf8 <pinned phase worker> <phase_dir>/input.execute.json
```

Its cwd must exactly equal the canonical repository path. The phase input must
still be absent during admission; Root writes it only after the observer returns.
The only allowed public environment keys are `SystemRoot`, `WINDIR`, `PATH`,
`USERPROFILE`, `LOCALAPPDATA`, `APPDATA`, `TEMP` and `TMP`. `SystemRoot` and `WINDIR`
must be `C:/Windows`. `ComSpec`, `PATHEXT`, Python injection variables and every
other extra key are rejected. After removing only the two known CLI config keys,
the frozen v8 basis environment must exactly equal the full actual worker
environment. No environment key is silently dropped from this binding.

Each worker/Python validation reads one raw buffer and checks that buffer's hash
and size. The worker is syntax-compiled directly from its checked buffer without
execution. The observer revalidates authority and file pins on both sides of OS
observation; each validation uses its own checked buffer. This does not claim
that a path remains immutable after the callback returns. Root's next controller
must separately close the actual execution/load interval and have that reviewed.

All 46 source controls passed. They use extracted AST functions, synthetic
frame/locals and byte buffers, and compile the frozen base only. The tests include
the three previously accepted argv/cwd/extra-env counterexamples, exact valid
launch, Python/worker byte/hash/size mismatches, read-once buffering, extra flags,
wrong input, source-review schema and reviewer identity. They execute neither a
candidate module body nor the runtime observer/WinAPI and write no runtime
receipts. Program identity remains transparent: author is w05, executor is Root,
and the observer is an automated program. Formal acceptance, runtime/source
qualification, completed cleanup and model authorization remain unissued.
