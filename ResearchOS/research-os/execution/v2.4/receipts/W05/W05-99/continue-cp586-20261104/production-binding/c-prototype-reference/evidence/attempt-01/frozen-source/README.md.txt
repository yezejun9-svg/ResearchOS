# Coding delivery bindings — C-only schema prototype

This is a fresh SQLite data-integrity prototype, not a product schema migration, Owner authentication, approval validation, business acceptance, or a LIVE gate. No D database is opened. The original unresolved questions and SQLite prerequisite probe remain unchanged; DECISIONS.md records Root's subsequent resolution.

## Artifact boundary

`coding_delivery_bindings.sql` is a candidate DDL file without a product migration number. The fixture alone creates a minimal `domain_objects` table with `fixture_only=1` and fake Goal/Task rows. No production migration is executed. A production integration must independently bind real canonical subjects and schema/version/backup policy.

The primary key is `(project,task_id)`; Goal is unique within its project. `(approval_issuer_ref,approval_ref)` and `(lineage_issuer_ref,business_anchor)` are unique across this database and across principals/projects. The database only constrains the supplied values. It cannot know whether an issuer or business anchor is truthful, preserve a lineage in a different database, or infer that an external/native approval is reusable after SQL rollback or a missing row. The Host's original consumed/UNKNOWN journal remains mandatory and is not implemented.

The DTO is a closed, explicitly prototype-only version. Identifiers and ref/hash anchors are required strings. Requirement and input vectors are represented by opaque ref/hash pairs (`requirement_refs_ref/hash`, `input_refs_ref/hash`), not reconstructed public Artifact contents. `schema_version` is integer 1. Creation writer/session snapshots are positive canonical decimal strings up to MaxInt64, including values greater than 2^53. They are provenance snapshots, never current Run/lease evidence. Extra Run/epoch keys are rejected.

## SQL guarantee versus consumer check

SQL checks required fields, identity column/body equality, hash shape and distinct Task/Goal hashes, same-project fake Goal/Task relations, unique claims and immutable rows. Explicit non-NULL JSON type tests avoid CHECK(NULL). The insert guard rejects REPLACE/UPSERT/IGNORE conflicts even with recursive_triggers OFF; UPDATE and DELETE including no-op writes are rejected. JSON top-level duplicate/escaped/unknown names are refused. These are structural properties, not authentication.

SQL does not compute SHA-256. `FixtureConsumer` strictly decodes the closed DTO, rejects duplicate/nonfinite/invalid data, recomputes canonical bytes and digest through the pinned Go helper, compares every identity and the full fake ExpectedContext, and checks a pristine full schema/index/trigger/FK snapshot. Correct-looking fields and a matching fake context do not make Owner/root/Host genuine. Classification is always `INTEGRITY_FIXTURE_ONLY`, with authentication and business acceptance false.

`canonical/jcs.go` is a byte-identical copy of the Root-authorized ResearchOS implementation. Its original SHA and the actual domain.Hash chain excerpt are recorded in canonical-provenance.json. The helper uses `json.Marshal(value) -> canonical.JSON -> SHA256`. Python only transports JSON; it does not substitute its sort/encoding rules for Go canonicalization. Independent vectors cover Unicode/UTF-16 key ordering, HTML, duplicates and large int64 decimal strings. Compatibility is limited to these actual tests and the prototype DTO.

## Fresh verification

The controller pins Python/Go, keeps profile/cache/tmp in this C scope, disables network/telemetry and preserves command/stdout/stderr/first failure in distinct evidence attempts. Fixture databases are memory-only or brand-new C files; backups copy to fresh C databases. Restore checks the complete expected binding inventory and all schema elements before row/hash/fake-context validation. Corrupt digests with valid shape are intentionally accepted by SQL and refused by the consumer, making the boundary explicit.

Not connected: native approved plans or approval consumption, real Owner/root/Host/Workspace/profile/suite/lineage producers, normal goal.start creation/pending audit, trusted source inventory/witness/checker, canonical Host REPORT/ArtifactUse aggregation, Task/Goal acceptance, old database migration/production restore, or any ordinary LIVE Goal 503 exception. The earlier frozen pure-scalar package is unchanged.
