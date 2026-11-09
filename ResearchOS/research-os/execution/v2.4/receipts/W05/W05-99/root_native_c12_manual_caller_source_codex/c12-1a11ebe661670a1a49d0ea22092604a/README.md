# C12 explicit Root caller Source

Source-only package, pending non-author review and actual Root config/checkpoint freeze. It creates no config, approval, signature, publication, SQL inspection, process, or model call during preparation. The old S10/API10/NH1/CTL4 and all canonical files remain unchanged.

The new callers use only the fixed C12 config path `integration_codex/native-cleanup-controller-source-root-1791517434000/controller.public.config.json`. Every invocation requires trailing `--config-sha256 BARE_LOWERCASE_HEX --config-bytes POSITIVE_INTEGER`, supplied from the actual frozen config. There is no default pin, directory scan, latest-file selection, or config construction. The same exact pin is forwarded to the serve child. CaseID is `t12cl149d6f49321`; the Root program directory must be `.local/native-cleanup-compile-env-1791516889000/programs`; CTL4 Source must match its reviewed SHA and byte length.

Root subsequently supplied the actual C12 config; a read-only SHA/length check confirmed `38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256`,1106152 bytes. For this exact config, append `--config-sha256 38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256 --config-bytes 1106152`. This observation does not authorize launching or approving a phase. The caller sources continue to require explicit arguments and reject mismatching config bytes.

Root must create these three new, empty, independent directories before invoking callers. This Source author did not create them:

- `B/integration_codex/native-cleanup-positive-serve-root-1791517434000`
- `B/integration_codex/native-cleanup-positive-root-api-1791517434000`
- `B/integration_codex/native-cleanup-manual-requests-root-1791517434000`

Here B is `D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99`. Output paths must be outside ControllerDirectory, harness OutputDirectory, program directory, BuildRoot and TEMP; scripts enforce this. Freeze the caller sources, NH1 Source/review, CTL4 Source/review and actual C12 config as Root execution references before starting. Do not rewrite the already-frozen config to add this later caller package: wrappers retain their existing explicit self-source pin in the guard inventory. No canonical read guard is held by this author.

## Manual sequence

1. Root independently reviews and freezes CP/config and caller pins, verifies fresh outputs/signed destinations, and explicitly launches `serve_one_positive_c12.actual_owned.py` with the actual config pin. The outer owned Job runs at most1800 seconds and the child gets identical config arguments. This caller does not approve any phase.
2. Root explicitly invokes `root_public_api_c12.actual.py snapshot` with the same trailing config arguments after the release ready artifact exists. Poll/snapshot/stop remain separate Root API actions. The request preparer never calls them or waits for readiness.
3. Root prepares one `helper-request / sign / release` specification using actual snapshot/payload/public-key metadata refs. Run the preparer once, inspect its output, then explicitly invoke its returned NH1 helper argv. NH1 creates one concrete approval; it does not sign.
4. Root prepares one `api-arguments / sign / release` specification using that existing approval ref and the same snapshot. The resulting argv JSON is inert. Root reads and explicitly invokes its argv. This invokes the unchanged actual signer through the API. An absent/failing sign receipt cannot prepare publication.
5. Root prepares `helper-request / publish / release` with the actual successful SigningReceipt and SignedDocument. Use the SAME snapshot and payload used by the sign approval: the signing receipt binds that exact prior approval. Explicitly run NH1, then separately prepare and invoke `api-arguments / publish / release` with its existing approval.
6. Only after the actual grant phase exists, repeat sign then publish with `Phase=grant`, its current snapshot/payload and exact prior ReleaseDocument. The original four-minute issue/expiry interval is checked without modification; elapsed validity fails. No retry refresh or future approval is generated.
7. At the actual retained fixture pause, Root explicitly captures its snapshot. Prepare/invoke `api-arguments / inspect / fixture-retained` with that snapshot. Inspect reads the entire live fixture through the original guarded API implementation. Root reviews its result.
8. Root prepares `helper-request / release-fixture / fixture-retained` with that existing inspection receipt and explicit `ExpectedFixtureState=migrated` or `unchanged-failed`. Explicitly invoke NH1, then prepare/invoke the existing-approval `api-arguments / release-fixture / fixture-retained` (maps to API action `release`). Exact fixture release and native identity revalidation remain the original API's responsibility.

There is no combined approve/sign/publish command. The preparer never invokes NH1/API. Files are written exclusively and no prior phase output is overwritten. The whole flow must fit the current native lifecycle; passing Source checks does not extend it.

## Invocation shapes

Use the fixed Python executable from the actual HarnessConfig, with `-I -S -B -X utf8`. Argument arrays below are descriptive; substitute only actual frozen refs, never invented digests:

```
python -I -S -B -X utf8 serve_one_positive_c12.actual_owned.py --config-sha256 CONFIG_BARE_HEX --config-bytes CONFIG_BYTES
python -I -S -B -X utf8 root_public_api_c12.actual.py snapshot --config-sha256 CONFIG_BARE_HEX --config-bytes CONFIG_BYTES
python -I -S -B -X utf8 prepare_one_root_request.py SPEC_PATH sha256:SPEC_HEX SPEC_BYTES
```

The preparer emits one prepared artifact reference. Helper mode also prints NH1 argv; API mode writes an argv array to an inert file. Root invokes arrays directly without rebuilding shell strings. Actual API/NH1 nonzero exit remains a failure, never an approval or success observation.

## Preparation specification contract

Each specification is JSON with exact fields. Common fields are `Schema=researchos.c12-one-root-request-preparation.v1`, `Mode`, `Action`, `Phase`, `Config`, `Snapshot`. A reference has exactly `path`, `sha256`, `bytes`, canonical absolute path and integer byte length. It must already exist and match the provided digest.

| Mode/action | Additional required fields |
|---|---|
| helper-request sign/release | PublicKeyMetadata, SID, IssuerPublicKey, RootSigningPublicKey, Payload |
| helper-request sign/grant | Above plus ReleaseDocument |
| helper-request publish | Corresponding sign fields plus SigningReceipt and SignedDocument |
| helper-request release-fixture | PublicKeyMetadata, SID, IssuerPublicKey, RootSigningPublicKey, InspectionReceipt, ExpectedFixtureState |
| api-arguments sign/publish/release-fixture | Approval |
| api-arguments inspect | None |

Every reference uses the `sha256:` prefix except `InspectionReceipt` in the preparation specification, which must use the actual Root API's ordinary bare-hex `inspection_ref`. The preparer validates those bytes and explicitly promotes ONLY that top-level file reference to NH1's public pin. It never converts `inspection.database_ref`: that nested metadata stays bare hex and is not opened. Public key metadata's private-resource references are never followed. Config argv uses bare hex; config refs in JSON use exactly one prefix.

Output names are fixed per phase/action under the independent manual requests directory. Helper requests point to a fresh `approval.<phase>.<action>.json`, but no approval is created by the preparer. API arguments require that actual approval to exist. Extra fields, duplicate JSON members, mixed phases, future/nonexistent references, wrong digest formats and already-consumed phases are rejected.

## Time boundary and Source correction

The actual S10 source had a1440-second outer timeout (24 minutes). The earlier30-minute summary was inaccurate. This candidate changes exactly that outer value to1800 with explicit Root authorization; old S10 is untouched. CTL4 remains1560-second inner Job and1570-second serve loop, Go timeout25 minutes. Main20 minutes, independent retained cleanup4 minutes and migration grant4 minutes are inherited harness/helper prerequisites, not edited here. No other timeout was changed in S10/API10. Source evidence of these constants is not evidence of a successful native run.

Source sealing origin905 was a Windows GBK decoding failure in the first sealer: outer1, explicit SourcePython1, product-nativeNULL. Its original script and complete tool IO are retained. The corrected sealer uses explicit UTF-8 reads and isolated Python flags. The retry passed Source controls; no caller, NH1 main, API, SQL or native executable was run by this author. The earlier preliminary seal is not the final handoff; final HDF/MF include this failure evidence.
