# CP597 Native first-writer schema boundary

This is a read-only construction recommendation against Main `001f7e5a4d95152c8f83874a60d9fbd3bbace538`, not implementation, migration approval or W14 acceptance. No database, probe or model was run. Root subsequently reserved the name `0025_client_native_writer_origins.sql`; this reviewer did not allocate it.

## Chosen small scope: prepared addon, not startup adoption

Use **one immutable table**, backed by the backend author's current-Host immutable witness map. Keep the current numbered migration inventory and all hard24 guards unchanged. Put the prepared payload at `internal/domain/contracts/0025_client_native_writer_origins.sql`, outside `migrations/sqlite` and its normal startup glob. Embed it for explicit installation in fresh isolated fixtures only. Missing or drifted schema returns `UNSUPPORTED` for the Native pilot; no startup DDL, backfill or automatic legacy upgrade.

This still permits the complete fresh-fixture vertical: typed Native producer -> bounded current-Host witness -> actual same-Tx credential/request verification -> truly fresh `session.create` -> epoch1 writer-origin row plus sealed reply association in the **same HTTP transaction**. It does not make the source operational against a user database. Controlled24->25 adoption is a later Root scope.

Why not merely add numbered25 now: `backup_migration.go:61` and `backup_host_configuration.go:82` reject >24. Even after raising them, `migrationAuthorityPresent` distinguishes populated authority, not a physically new file: an existing empty24 database could silently advance. Safely adopting25 therefore needs an explicit prepared/approved upgrade or trusted fresh-target construction, not just changed constants. `store.go:66-74` already gates migration before DDL, and `:109-116` only installs the existing sessions addon.

## Exact schema-author paths

The backend author owns Native profile/Host witness/API/CLI/Desktop consumers and `client_command_identity.go`. Avoid overlapping those files.

| Path | Bounded responsibility |
|---|---|
| `internal/domain/contracts/0025_client_native_writer_origins.sql` | Prepared DDL, one table/indexes plus the narrowly scoped Native-marker immutability triggers on idempotency. Not in the live migration glob. |
| `internal/domain/client_native_writer_origin_schema.go` | Embed/fingerprint; private closed canonical DTO; scalar/body/hash checks; no authority producer. |
| `internal/domain/client_native_writer_origin_store.go` | Same-Tx insert/read and historical relationship validation against immutable command identity, original raw header, sealed typed response and session. No commit/open/schema-install/fallback. |
| `internal/domain/backup_client_native_writer_origins.go` | Complete stable logical inventory, historical typed validation, and prepared-addon production-backup unsupported guard. Never consult a live witness map to validate historical backup data. |
| `internal/domain/backup.go` | One small default integrity entry hook to reject prepared Native state in ordinary backup/restore until explicit adoption. No change to existing table inventory/manifest semantics for databases without the addon. |
| `internal/domain/client_native_writer_origin_store_test.go` | New fresh-SQLite positive/negative integrity fixtures. |
| `internal/domain/backup_client_native_writer_origins_test.go` | Fresh snapshot/restore historical validation, missing-marker/row/schema and cold-witness negatives. |

Do not modify any of `0001..0024`, current migration ceilings, `next_v24_sessions.sql`, old fixed23->24 plans, the previous four coding-delivery-binding files, registry41, StepState or existing ownership records in this scope.

## One table: proposed exact logical fields

The backend and schema authors should freeze one shared private DTO before implementation. Suggested fields are:

- `origin_schema` fixed `researchos.client-native-writer-origin.v1`; `schema_version` integer1.
- `attestation_ref` server-random primary key; `witness_hash` digest of the immutable trusted witness projection. A digest is a relation check, not authentication.
- `principal`, `command_id`, `request_hash` (the **existing semantic command identity hash**), `request_wire_hash` (SHA256 of the **actual original HTTP bytes**), `response_hash` (the actual sealed typed response).
- `project`, `session_id`, `writer_epoch` fixed integer1, `writer_client_id` (explicitly a label).
- `host_instance_ref`, `host_generation_ref`, `connection_instance_ref` (server-random per Native approval, **not a stable client identity**), `os_subject_ref`, `credential_hash` (real resolved credential digest, never raw token).
- `attested_at`, `attestation_expires_at`, `created_at` as strict UTC strings; `origin_body` canonical closed JSON and `origin_hash` equal to the existing Go Hash chain over that body.

SQL constraints:

1. `PRIMARY KEY(attestation_ref)`; `UNIQUE(principal,command_id)`; `UNIQUE(project,session_id,writer_epoch)`.
2. `FOREIGN KEY(principal,command_id,request_hash)` references the existing immutable `client_command_identities` triple, preferably deferred as in SQL23; session FK references `client_sessions(id)`. Do not FK historical facts to a currently active/unexpired credential.
3. NOT NULL and explicit JSON-type/presence/equality checks: SQLite CHECK(NULL) must not pass. Full hash shape, exact epoch1, closed canonical DTO in Go; no floats for larger provenance counters.
4. Unconditional no-update/no-delete guards. BEFORE INSERT conflict guard rejects **all** identity collisions before REPLACE/IGNORE/UPSERT can silently bypass immutability, regardless of recursive_triggers.
5. Exact schema fingerprint includes the table, columns, FKs, explicit/implicit index details, table triggers and the specifically named idempotency-marker triggers. Full database DDL hash alone is insufficient.

No `current_ref`, mutable used-bit, new writer journal or second response authority is needed. A row records a committed first-writer origin; current authorization always additionally requires the backend's real current witness/credential gates.

## Missing-row detection: versioned sealed-header association

The existing private header is a closed three-field object (`client_command_identity.go:215-229`): schema, encoding, exact original raw envelope base64. Do not append fields to it ad hoc.

The backend should define an explicit new private header version, scoped **only to fresh COMPLETED session.create in this Native pilot**. It retains the exact original raw bytes and adds a closed `NativeCreateOrigin` association with version, attestation ref and witness hash (optionally origin hash). Public request, public response and the immutable semantic command identity remain unchanged. The association is not a new journal and does not authenticate a row.

Order inside one transaction:

1. Ordinary real authentication/RBAC and exact original request/identity lookup.
2. Sealed replay returns the original response without new witness consumption, origin or grant. Malformed/conflicting/orphan replay remains an error.
3. For a fresh pilot command, domain builds the verifier query from the opaque same-Tx credential facts and its **own** original raw bytes/parsed scope. Only the trusted current-Host map can qualify it; request fields cannot construct a witness.
4. Execute the existing fresh create and validate its real final response/session. Require genuine new session, method session.create, original request session=null, epoch1, writer label equal to the actual request, current project and canonical immutable command identity.
5. Insert the immutable origin row, then seal the association into that response's existing idempotency headers with a guarded old-v1-to-new-version CAS. Commit both together with the normal identity/session/outbox effects. No new origin for REJECTED/failed commands or sealed ordinary replay.

Narrow DDL marker guards should prevent direct insertion of the Native-version header, require the matching origin before a v1->Native seal, and prevent removal/change/deletion/replacement of an already sealed Native association. Old header versions and unrelated operations retain their behavior. Header decoding, origin reading, attach classification and inventory validation require both directions: marker->origin and origin->marker->actual typed response/session. A marker with absent schema/row, or a row with missing/mismatched marker, is an integrity error, never legacy.

The old raw bytes are already available: `writeClientCommandEnvelope` stores `env.originalRaw` as base64; `validateClientIdentityRequest` cross-checks parsed, retained and canonical fields. Recompute wire SHA from those exact bytes during historical validation. Do not confuse it with `Envelope.ContentHash()`.

## Witness and credential boundary

The witness map is bounded, immutable, private to the current Host and populated only after its typed Native peer gate. Bind it to the exact owning service/data-store composition as well as boot generation, principal, real credential digest, method/project/client/command and wire hash. A clone or restored service cannot reuse a live old Host's map merely because the stable InstanceID or credential text matches.

If the Native profile carries only a declared wire digest (to fit the8192-byte frame), label that truth accurately: the producer seals the Native caller's authorization for a digest/scope; it has not inspected the entire HTTP body. The consumer must compute the actual original HTTP byte SHA and compare **every** sealed scope field. The existing original-header bytes make that comparison durable. Do not claim the full public unbounded create payload fits in an8KiB Native frame.

Map absence/cold restart/expired witness is unqualified, not a request to rebuild or backfill proof from the database. HTTP rollback does not mutate the witness; SQL rollback removes the attempted origin/session/identity together. Retrying the exact original command is not a new Native/model budget. Missing rows, new command IDs, new Host generations, restores and unrelated databases cannot refund an old external Native UNKNOWN or consumed model scope; those retain their original authoritative reconciliation journal.

The per-connection random ref proves no durable client instance across later Native calls. This scope therefore establishes **first-writer historical provenance**, not secure same-writer credential rebind or cross-boot recovery. Any retained same-label ordinary renewal must be described as ordinary compatibility, not new Native proof.

## Backup/restore boundary

`backup.go:380` snapshots the full SQLite file and `:162` hashes all DDL, but inventory at `:239` has a fixed nine-table set; the public typed restore loop at `:654` only covers domain_versions. Physical copy is not typed private-state qualification.

For this prepared addon:

- Ordinary backup/restore with neither addon nor marker is unchanged.
- Presence of the addon or a recognized Native header marker must trigger explicit prepared-native UNSUPPORTED in the default product backup/restore path until adoption. A marker with a missing table is an integrity failure, not absence.
- Fresh-fixture snapshot tests may manually copy the complete fresh DB and invoke the dedicated schema/typed/inventory validators. The logical root is stable ordering over the complete origin set, canonical bodies/hashes, witness associations, immutable command triples, exact original request bytes and sealed responses. Historical expiration/revocation does not invalidate historical data.
- Restoring historical rows never restores the in-memory witness map. Do not require that map to validate historical storage, and do not treat successful historical validation as current authorization. No automatic re-sealing to a new generation.
- A live Host map must not be reused with a restored/changed DB. Root restore activation must create a new Host/service incarnation or explicitly close the new Native path; no hot DB swap under old witness authority.

Later controlled24->25 adoption needs Root-reserved live SQL, explicit prepared/approved upgrade path, exact source inventory/safety ceilings, dedicated typed schema/inventory support and pre/post-restore verification. Preserve the fixed23->24 plan and its hashes. If a development24 addon already exists, later adoption must validate its exact bytes/rows rather than blindly reexecute or overwrite it.

## Must remain blocked

- No current verified witness, wrong credential/principal/service/store/generation/scope/wire bytes, expired/cold map, invented client label or request-provided verification booleans.
- Legacy sessions with only old receipts/labels: no automatic Native backfill. Goal.start remains legacy in this pilot.
- Marker/row/schema/original-header/response mismatch or missing consumption association.
- Native-provenanced sessions' foreign-client attach for **all** lease states, including expired/null, must reject before the old transfer path. Current Main still has an expired/null foreign-writer handoff branch (`client_protocol.go:1197-1254`); it is not globally closed today. Legacy behavior is not silently rewritten by this proposal.
- True same-writer Native rebind, cross-boot writer continuity, crosswriter ACK/CAS/full settlement, active-Run pause and actual handoff remain unqualified. A same client_id string is not a stable client proof.

## Required fresh-fixture cases

Positive controls must use real current contracts, exact command identity/raw headers and an actual sealed create response. Cover producer->map->sameTx origin+marker success and full rollback on row/marker/CAS fault; fresh witness exact retry; final ordinary sealed replay with zero new consume; canonical historical snapshot/restore with an empty live map and no authorization.

Refuse forged/mismatched raw/semantic hashes, credential/principal/project/client/method/command/session, wrong boot/service/store, malformed or duplicate DTO keys, NULL/type aliases, REPLACE/IGNORE/UPSERT/no-op mutation, missing/altered indexes/triggers/FKs, valid-shape bad hash, marker-only/origin-only states, orphan or non-COMPLETED response, same command across project/method, duplicate attestation/epoch1 claims, absent schema, cold restore proof replay and every foreign attach lease state. Verify old24 normal startup and no-addon backup are byte/state preserving, and no old binding table is installed. Source tests only; no old DB, native backend, model or probe.
