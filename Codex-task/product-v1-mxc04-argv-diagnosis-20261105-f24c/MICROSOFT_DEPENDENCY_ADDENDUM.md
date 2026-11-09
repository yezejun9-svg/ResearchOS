# MXC04 static dependency addendum (2026-11-05)

Conclusion: the recorded command failed with a complete native-looking command-syntax diagnostic. The forward-slash CMD executable spelling remains a plausible cause; the public source does not establish the exact Windows CMD parser condition that produced it. Neither MXC absence nor MXC readiness is established. Keep FAILED_COMMAND_SYNTAX_CAUSE_UNCONFIRMED / resource readiness UNKNOWN; no automatic retry, no model permission.

This supplements the earlier REPORT.md after Root explicitly authorized reading the fixed Microsoft dependency. Earlier statements that the SDK had not yet been inspected are historical; the findings below supersede that source-coverage limitation. The original report, frozen preparations, consumed scope, receipts, product Task and failure counts remain unchanged.

## Observed receipt, not reconstructed execution

Run: product-v1-owned-verification-20261104/runs/mxc_availability_20261105_e91c.
Native child exited 1, stdout empty, stderr 18 bytes, no spawn error, no timeout, no drift or observation error. The complete stderr bytes are C3 FC C1 EE D3 EF B7 A8 B2 BB D5 FD C8 B7 A1 A3 0D 0A; CP936 decoding is the Chinese command-syntax error followed by CRLF. The stream is complete, not truncated or re-encoded by the wrapper. Outer f13 reports 7 total Job processes, zero active processes and proved stop without forced termination. Process count alone identifies neither the emitting image nor enforcement success.

Receipt SHA256 pins:
- mxc/RESULT.json: d3f25b1ace55b453e675a54f3669cc4a9d9777cc6d8c0106df34ae1640cd6931
- mxc/stderr.prefix.bin: 7830609d54ab060eb4d9b243eda3a59e38b0940058ed397f4cd26d89631cd86d
- mxc/launch-plan.json: 29537b0933fd1960d33b7517cfc7f98225a52ac341a4e165559c83f82d82d9c1
- outer RESULT.json: 6903454745a9ee821497e9a2f172fd00a736a07165316800a0129a28ff8442fd

## Fixed public source chain

The source reference is OpenAI rust-v0.166.0 and its pinned Microsoft/mxc revision b21120168d70befe12356411423266bfef168446. It matches the installed release number but is not a reproducible-build attestation for the installed binary SHA 9d563ee4e0441ff9d59d612013e0460ddf8e5709735c2d9f6b98b7ef8ca4eb42.

1. OpenAI pins this exact Microsoft dependency in [Cargo.toml](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/Cargo.toml#L429). Its [MXC policy builder](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/mxc-sandbox/src/policy.rs#L253) renders the target argv using WindowsCreateProcess context into ExecutionRequest.script_code.

2. Microsoft's fixed [cmdline.rs](https://github.com/microsoft/mxc/blob/b21120168d70befe12356411423266bfef168446/src/mxc-sdk/src/core/mxc_common/cmdline.rs#L71) joins tokens with one space. The CreateProcess quoting predicate at lines 117-121 covers empty tokens, selected whitespace and double quotes. It does not canonicalize paths, convert slash direction, special-case cmd.exe or quote this argv's executable. Therefore static evaluation of these exact fixed ASCII tokens gives:

```text
C:/Windows/System32/cmd.exe /d /c echo MXC_OK
```

This is a source-derived prediction, not a captured live CreateProcess argument. No serializer code or test was executed in this investigation. Both the slash and the absence of quotes survive this serializer; changing context to WindowsCommandProcessor would not change these particular tokens either, because none contains its additional metacharacters.

3. The fixed [BaseContainerRunner](https://github.com/microsoft/mxc/blob/b21120168d70befe12356411423266bfef168446/src/mxc-sdk/src/backends/process_container/common/base_container_runner.rs#L515) converts script_code to UTF-16. At lines 734-763 it creates the security environment and returns a structured failure on error. At [lines 829-842](https://github.com/microsoft/mxc/blob/b21120168d70befe12356411423266bfef168446/src/mxc-sdk/src/backends/process_container/common/base_container_runner.rs#L829), it directly calls CreateProcessW with NULL application name, the command string and the security-environment startup attributes. There is no additional cmd /c prefix on this path and no COMSPEC-based shell selection in this visible command construction. Thus the previous nested-shell/COMSPEC-selection hypothesis is not supported by this call chain. This does not claim COMSPEC has no possible use anywhere in Windows or CMD.

4. [OpenAI native.rs](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/mxc-sandbox/src/native.rs#L15) calls this runner with inherited stdio, forwards launch errors, suppresses the SDK diagnostic buffer, then returns the child's wait result. As a result the receipt contains no published SDK launch audit that would independently identify the reached API stage or child image.

## What Microsoft documents, and what remains unknown

[CreateProcessW documentation](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw) says that with NULL application name, the first whitespace-delimited command-line token determines the module. The remaining command line is available to the child. Executable lookup and the child's own command parsing are distinct stages.

[Microsoft CRT portability guidance](https://learn.microsoft.com/en-us/cpp/c-runtime-library/unix?view=msvc-170) distinguishes Win32 path APIs accepting either slash direction from CMD command-prompt syntax lacking general forward-slash support. That makes using a Win32-valid forward-slash path insufficient evidence of CMD parser equivalence. Its documented scope is commands entered at the prompt; it does NOT specify precisely how this installed CMD parses a forward slash in its own argv0. Do not turn that documentation into proof of this failure's cause.

[CMD documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd) documents /d disabling AutoRun and /c executing the supplied command and exiting. The requested command tail contains only the echo command and a literal ASCII marker. It contains no filesystem path whose slash style could affect echo's data argument. The slash concern is the executable token before /d /c, not an echo builtin file-path argument.

The retrieved public Microsoft SDK source does not implement Windows CMD's private parser or provide the exact predicate for the observed localized error. CP936 bytes and the plain localized text are consistent with inherited output from a native command interpreter; they are not an emitter attestation. We cannot assert from them that the sandbox API succeeded, that forward slash was treated as a specific switch, that /d was honored, or that the marker command actually ran. The absence of an explicit MXC-unavailable error is not availability proof. Seven Job processes are likewise insufficient.

## Bounded next decision, no execution authorization

The strongest static finding is the direct, unnormalized command-string handoff. No definite serializer quoting defect has been established for these five simple tokens. No configuration, permissions, installation or elevation change is indicated by the syntax error.

If Root obtains a distinct authorization for one additional local diagnostic, the smallest proposed delta is only the target argv executable token C:/Windows/System32/cmd.exe -> C:\Windows\System32\cmd.exe, same pinned binary, leaving the command tail, COMSPEC, other environment, MXC selection, permission profile, fresh owned cwd requirement and original f13 budgets unchanged. This isolates argv spelling better than changing CMD and COMSPEC simultaneously. It would require a newly reviewed immutable candidate and explicitly authorized scope; this document creates neither. Do not reuse or reset the consumed MXC04 scope, or run an uncontained CMD control as a workaround. A successful result would support that spelling mattered under these exact conditions; it would still prove only startup availability, not the product's split-read policy enforcement or model eligibility.

This investigation performed public source/document reads and receipt reads only, plus this C addendum. It ran no Codex, native echo, model, admin, setup or runtime probe; it changed no product source, permission policy, saved config, old receipt or frozen preparation. The original real Task remains consumed; no inference/model retry is authorized by this analysis.