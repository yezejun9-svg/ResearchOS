# Windows x64 R1 fixture bundle

This ZIP is a reproducible **development fixture**. It does not install an SCM service, enable normal LIVE runtime execution, qualify a provider, activate a populated database, or satisfy clean Windows A15.

Build from a frozen source commit on a Windows x64 build host with the exact locally provisioned Go 1.27.1, Node 24.9.0, npm 11.6.0, and Python 3.14.3 recorded in `execution/toolchains/locked.json`. The builder rejects dirty, missing, and untracked files across the package and Go/web build input trees, checks the source against HEAD before and after building, verifies tool hashes, uses `GOTOOLCHAIN=local`, runs `npm ci --offline`, and never invokes the repository's full-test CI script. Unrelated execution evidence can remain untracked. Its external JSON output records the archive SHA-256. Use two separate invocations and compare both archive hashes and every manifest file hash before distributing a candidate.

```powershell
$py = '<verified Python 3.14.3 path>'
& $py ops/release/build.py --output 'C:\release-output\researchos-r1-a.zip'
& $py ops/release/build.py --output 'C:\release-output\researchos-r1-b.zip'
Get-FileHash -Algorithm SHA256 'C:\release-output\researchos-r1-*.zip'
```

Extract one ZIP into a new directory. Keep that directory read-only during operation. The manifest lists every packaged file except itself; verify it and compare the archive hash with a separately approved distribution receipt. The manifest and hashes establish integrity, not independent source trust or a signature. The package contains no development tool paths. Its `licenses/` entries contain locally present license texts; `sbom.license_gaps` remains an explicit release gap where a text was unavailable. The bundled `execution/commands.json` is the real construction registry; `release.reproduce` and other `UNBOUND` entries remain nonzero. Construction checks require an exact source checkout, pinned tools, and their own evidence roots. The bundled scripts do not turn those checks into installed-product acceptance.

Use a new **absolute** data path outside the extracted package and a free loopback port other than 32736 or 79136. The example runs without credentials and creates only a fresh fixture database. `-Fresh` rejects existing data. It never points at the protected broker, an existing ResearchOS product database, or a production provider.

```powershell
$release = 'C:\release-output\researchos-r1-extracted'
$data = 'C:\release-output\researchos-r1-fixture-data'
& "$release\scripts\verify.ps1" -ReleaseRoot $release
& "$release\scripts\start.ps1" -DataDir $data -Listen '127.0.0.1:19878' -Fresh
Invoke-WebRequest 'http://127.0.0.1:19878/healthz' -UseBasicParsing
& "$release\scripts\stop.ps1" -DataDir $data
```

The fixture stop script validates the recorded PID, process creation time, executable, and OS command-line instance/data/release binding before stopping the owned process. A missing or mismatched process leaves the identity file and data untouched. It preserves that directory, logs, and database. It is not the production drain/checkpoint/SCM protocol. To disable this fixture, stop it and leave data in place. To remove the package, delete only the extracted release directory after stopping it; retain data and receipts separately.

The existing exact `schema13-to14-remote-access-v1` upgrade remains unchanged. The separate `schema13-to20-research-runtime-v1` plan pins all twenty frozen migrations and has bounded fixture evidence for preservation and recovery. Actual populated-database activation remains blocked; the fresh fixture launcher does not perform either upgrade.

The package also includes `bin/release_host.exe`, the existing same-user fixture supervisor. Its persistent actual-control host, private READY checks, exclusive data-root lease and encrypted cutover snapshot mechanisms have bounded evidence. The scripts above still use the direct fixture start/stop path. Actual-control business proof and complete different-build cutover/rollback remain closed; the supervisor binary does not grant that qualification.

Clean Windows installation, independent service identities and ACLs, actual update/rollback, W19 overnight evidence, and the full 42-case acceptance index remain incomplete. A successful current-user fixture run is evidence only for the packaged fixture start/stop path.
