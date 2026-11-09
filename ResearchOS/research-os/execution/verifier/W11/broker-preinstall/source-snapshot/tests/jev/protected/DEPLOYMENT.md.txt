# Independent-identity canary service preparation

`adapters/protectedstore/cmd/canary-broker` is a **synthetic-only Windows service**.
This package is prepared for review; compilation, same-user native protocol tests
and a dry-run installation plan do not establish installed service isolation.
Actual installation/start/verification/uninstall require the separately approved
elevated step. The scripts do not request elevation or launch UAC themselves.

## Concrete machine changes

- Add only `ResearchOSVerifierCanary`, a manual-start own-process service using
  virtual account `NT SERVICE\ResearchOSVerifierCanary` (no password is stored).
- Add only `C:\ProgramData\ResearchOSVerifierCanary` on this machine. The executable
  and install manifest have Administrators ownership, with full access for
  Administrators/System and read/execute for the service and named developer SID.
  The developer cannot use file ownership to replace the binary or its DACL.
- `data` is writable by the service and administrators; `data\private` is created
  atomically by the service with exactly its own protected DACL. Four fixed
  synthetic input/label/detail/log files are the only payloads. Existing private
  state is reopened only after exact actual-handle owner/ACL validation.
- Restrict service control to Administrators/System. The developer SID receives
  only config/status query rights. Required privileges are limited to
  `SeChangeNotifyPrivilege`; no provider credential, network or formal data is used.

The service verifies that its actual token user equals its exact virtual account,
that it is running under SCM, and that its executable is at the fixed installed
path. It accepts only `summary-v1` on one local, remote-rejecting named pipe.
Pipe rights exclude `FILE_CREATE_PIPE_INSTANCE`; first-instance protection fails
closed if another server already owns the name. The client binds the pipe server
PID to the running SCM service with the expected account before and after reading.
The probe has a 3-second overall deadline; native overlapped I/O and Go's Windows
poller also enforce that deadline on request/read/ack, including a silent server.
Only `SafeSummary` fixed enums/counts leave the service; every request rechecks the
four private files, so tampering changes the response to BLOCKED. Invalid commands
receive no body. There are no arbitrary file, process, proxy or model interfaces.

The small canary server uses nonblocking message-pipe polling with 25 ms waits and
2-second request/ack limits. It is a bounded deployment probe, not the final
concurrent evaluator transport. There are no private console logs, temporary
captures, subprocesses or SQLite payloads in this service.

## Build, preview, and authorized deployment

Build with pinned Go 1.27.1:

```powershell
& $env:RESEARCHOS_GO build -trimpath -o .local/canary-broker.exe ./adapters/protectedstore/cmd/canary-broker
$hash = (Get-FileHash .local/canary-broker.exe -Algorithm SHA256).Hash
./tests/jev/protected/deployment.ps1 -Binary .local/canary-broker.exe -ExpectedSHA256 $hash
```

The default `Plan` action is read-only. It prints the exact service, account/SID,
binary hash, installation path and command line. Review and freeze that output.
For the final user-authorized elevated action, pass the same reviewed hash and
the developer `-ReaderSID` from the plan explicitly, then `-Action Install
-Confirm:$false`. No prior service/directory is overwritten. A partial failure
preserves its state for inspection and cannot be silently retried as a fresh install.

After returning to the ordinary **unelevated developer** context, run:

```powershell
./tests/jev/protected/verify-deployment.ps1 -ReceiptDirectory <new-receipt-directory>
```

The 16 fixed assertions check SCM account/state, PID-bound aggregate output,
actual ACCESS_DENIED for read/write opens of all four existing canaries, and
denied binary write/DACL write with Administrators ownership. Opening for write
does not modify bytes. The output contains Booleans, counts, hashes and identities,
never private contents. Separately restart the service as administrator and repeat
the unelevated probe to establish persistence. Keep both raw command receipts.

`-Action Uninstall` validates the manifest, binary hash and exact SCM command,
requests privileged service control 128 to erase only the four known canaries,
then deletes this service, its known files and empty fixed directories. There is
no recursive delete; unknown files or drift cause a refusal with data preserved.
The installer never stops, deletes or changes another service.

## Qualification still blocked

Even a successful installed canary verifies only this synthetic OS boundary.
Formal protected provider wiring, independent label provisioning, per-case
candidate confinement, raw official responses, private bounded captures,
declassification review and the full W11-G04/A08/C22 matrix remain unimplemented.
The service has no `Provider.Read` bridge back into the same-user control plane:
doing so would copy formal private bytes into the developer's identity. A future
trusted evaluator must stay inside the service identity and publish audited
aggregate summaries. No qualification or BOUNDED_AUTO authority is granted.

References: [CreateService virtual account](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-createservicea),
[pipe access rights](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights),
[pipe modes](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-setnamedpipehandlestate).
