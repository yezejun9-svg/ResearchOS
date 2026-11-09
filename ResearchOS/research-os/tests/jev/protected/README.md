# W11 protected-body canary implementation

This slice introduces `protectedstore.Provider`, a trusted host dependency, and
`Service.RegisterProtectedArtifact` / `ReadProtectedArtifact`. The normal content
endpoint dispatches `VERIFIER_ONLY` objects through the configured provider. A
restricted Owner/Verifier grant is required and is checked again after provider
IO, together with current lineage, artifact version and content integrity.
Registration stores an opaque ticket, descriptor and event metadata in SQLite;
the private body never enters `uploaded_content`. No HTTP registration endpoint
or environment-variable provider auto-enablement is added.

The only shipped provider is **CANARY_ONLY**, Windows native, and FIXTURE-only.
It creates a new directory with an atomic, protected current-user DACL; it checks
actual handle ownership, exact ACL, regular files, hardlink count, reparse points,
size and hashes. It refuses existing directories and never alters their ACLs.
The root handle's final path is checked because Windows POSIX rename can succeed
despite share-delete restrictions. These checks are exercised with synthetic
data, including an actual junction, ACL change and native AppContainer child.

**This is not independent verifier isolation.** The unrestricted developer's
current OS identity can read the canary files, and the frozen suite explicitly
asserts that limitation. The child AppContainer has zero capabilities and is
denied canary read/write; this establishes only that restricted child boundary.
Default sandbox TEMP capture is used solely for synthetic probe Booleans, never
formal private output. Hostile concurrent same-user mutation and administrator
access are not qualified by this provider. LIVE always fails closed.

Ordinary list/event/search/context consumers do not receive private bodies or
opaque tickets. Public sealing rejects protected ancestry. Protected context
materialization and backup remain refused rather than copying private bytes to
ordinary output directories. `SafeSummary` accepts only aggregate counts and
fixed enums; it grants no publication/declassification authority. The separate
frozen evaluator preparation is documented in DEPLOYMENT.md; its actual service
installation and formal run require independent live verification.

## Frozen canary execution

Set `RESEARCHOS_GO` to the pinned Go 1.27.1 executable and run:

```powershell
python tests/jev/protected/run.py
```

The runner records the pre-run source revision/manifest, Windows/Go versions,
exact command, raw logs and all **41** frozen assertions in `expected.json` under
`execution/receipts/W11/protected/<run_id>`. Missing/duplicate/malformed assertions,
source drift, test errors and incorrect scope fields fail the runner. It makes no
network or model calls and propagates no Jev/Typesafe environment credentials.
The result is owner `EXECUTION_REPORTED`, pending independent code/evidence review.

Formal W11-G04 and A08 remain **BLOCKED** until a real independent Verifier OS
identity/service, private storage/log/temp boundary, bounded audited summary
publication and independent live validation exist. No formal holdout is created,
read or inferred from this suite. No qualification or BOUNDED_AUTO is granted.

Native API references: [CreateFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilea),
[ACCESS_ALLOWED_ACE](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-access_allowed_ace),
[reparse point operations](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points-and-file-operations).
