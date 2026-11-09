# Root inert archive-request builder calling contract

Fixed request directory Q12: D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-cleanup-manual-requests-root-1791517434000. The sole output filename is grant-public-pin-archive.request.json. Q12 must already exist; that file must not exist.

Fixed future archive directory: D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-grant-public-archive-root-c12-1791517434000. It must not exist. The builder checks its separation from controlled resources and does not create it.

After independent Source review, Root fills actual existing snapshot values in this one-line PowerShell shape (placeholders are never fabricated resources):

```powershell
& 'C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe' -I -S -B -X utf8 'EXACT_REVIEWED_BUILDER_SOURCE_PATH' 'EXISTING_GRANT_SNAPSHOT_PATH' 'sha256:EXACT_SNAPSHOT_SHA' 'EXACT_SNAPSHOT_BYTES' '--select-full-current-grant-public-pins'
$builderExit=$LASTEXITCODE
Write-Output "SOURCE_PYTHON_EXIT=$builderExit"
exit $builderExit
```

Success marker ROOT_ARCHIVE_REQUEST_WRITTEN prints only request ref3. Result JSON has exactly Schema, HelperSource, Config, Snapshot, Payload, OutputDirectory, Entries; Schema is researchos.native-grant-public-pin-archive-request.v1. Entries contain exact original role/path/sha256/bytes. HelperSource is the bounded revision pinned in this packet. The fixed config is 38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256 / 1106152, using a sha256: prefix. Full flag selects 57 inventory + backup/rehearsal + manifest ciphertext only, with migration-sql as the verified target-0024 alias, not a second entry.

The request writer does not call/import/execute the archive helper. Root reviews the resulting concrete request, then invokes the separately reviewed helper with request ref3 as a distinct action while TEMP inputs remain available and before fixture release. No current request or archive was generated in Source controls. This is evidence preparation, not approval, signing, a TTL change or migration acceptance.

