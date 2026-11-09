# Explicit Root call contract
No implicit resource discovery, latest selection, future path synthesis, recursive refs, signing or publishing is provided. Source review must precede actual use.

Use the HDF helper_ref as HelperSource. Root writes a new UTF-8 request in its own receipt namespace and supplies its exact path, prefixed SHA256 and integer byte length:
```json
{
  "Schema": "researchos.native-grant-public-pin-archive-request.v1",
  "HelperSource": {"path":"EXACT_HDF_HELPER_PATH","sha256":"sha256:EXACT","bytes":0},
  "Config": {"path":"EXISTING_C12_CONFIG_PATH","sha256":"sha256:38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256","bytes":1106152},
  "Snapshot": {"path":"EXISTING_CURRENT_GRANT_SNAPSHOT_PATH","sha256":"sha256:EXACT","bytes":0},
  "Payload": {"path":"EXISTING_CURRENT_02_GRANT_PAYLOAD_PATH","sha256":"sha256:EXACT","bytes":0},
  "OutputDirectory": "FRESH_ROOT_RECEIPT_DIRECTORY",
  "Entries": [
    {"role":"EXPLICIT_EXISTING_ALLOWED_GRANT_ROLE","path":"EXACT_ORIGINAL_PATH","sha256":"sha256:EXACT","bytes":0}
  ]
}
```
Placeholders are shapes, never runnable authority or an instruction to fabricate paths. Select each intended entry explicitly from that same payload; validate exact metadata against current snapshot. To get FULL_TEMP_PIN_CLOSURE select 57 inventory entries, backup, rehearsal, and every manifest-listed cipher payload. Do not select migration-sql separately: the selected target 0024 entry closes its one declared alias. Four JSON paths and next_v24_sessions.sql are mandatory; 27/28 was the earlier erroneous count, corrected to 28/29.

PowerShell shape (Root fills concrete reviewed values):
```powershell
& 'C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe' -I -S -B -X utf8 'EXACT_HDF_HELPER_PATH' 'EXACT_REQUEST_PATH' 'sha256:EXACT_REQUEST_SHA' 'EXACT_REQUEST_BYTES'
$sourcePythonExit = $LASTEXITCODE
Write-Output "SOURCE_PYTHON_EXIT=$sourcePythonExit"
exit $sourcePythonExit
```
Success marker: GRANT_PUBLIC_ARCHIVE_OK followed only by the exact manifest ref3. The manifest contains originalRef -> archivedRef path/SHA/bytes mappings, selected count, missing roles, explicit alias mapping, guard-close facts and nonacceptance flags. Cipher files remain opaque .enc bytes; metadata is role/name plus original/archive path pins. No decoded ciphertext or nested private field content is emitted.

The real helper must run on Windows because the already-reviewed SourceReadGuard requires held Win32 file handles. Its successful close is necessary before manifest publication. Grant TTL is neither checked as authority nor refreshed: archival is evidence preservation and may occur after consumption/expiry while this case remains retained. No signature validity or permission is inferred from copying.

Failure produces no success manifest. Preserve any partial files as failure evidence and use a new request and fresh output directory for a separately authorized retry. Never edit original payload refs to archived paths. Future reviewers rehash the archived copies and consult the mapping, retaining the original snapshot/payload pins as provenance. The original TEMP paths can become unavailable after fixture release; archived pins are replacement evidence locations, not rewritten grant authorization.

Current source-only test evidence: 41 controls PASS; archive run(), real Win32 guard, native case, API, SQL, private key and model were not executed by this author. HDF/MF sealing does not self-approve the independent review or native/resource acceptance.

