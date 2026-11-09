# Root resolution for this C-only prototype

This supersedes the unresolved choices recorded in OPEN_SEMANTICS.md without rewriting that earlier record.

- A given `business_anchor` is independent of Owner root, project, new Goal/Task/approval identities and timestamps. `UNIQUE(lineage_issuer_ref,business_anchor)` applies across projects and principals in this database. Owner root is a separate required authority snapshot. The prototype does not derive a trusted anchor or protect against another database; a future Host must recover the original trusted lineage and fail closed when it cannot.
- Approval identity is `(approval_issuer_ref,approval_ref)`, unique across this database. A missing/rolled-back row does not authorize another use of a consumed or UNKNOWN native approval. Native approval consumption is not implemented here.
- Keep `PRIMARY KEY(project,task_id)` and `UNIQUE(project,goal_id)`. Insert conflict guards supplement indexes and immutable UPDATE/DELETE triggers, including REPLACE/UPSERT/IGNORE and recursive_triggers OFF.
- The closed DTO is explicitly a prototype, not a published product schema. Identifiers/ref/hash values are strings; schema_version is integer 1. Creation writer/session snapshots use canonical positive int64 decimal strings. They are not Run/dispatch/lease proofs. No Run id or runtime epoch is invented.
- Copy the original `internal/canonical/jcs.go` bytes from ResearchOS to C and record SHA256. Its Go JSON canonicalizer plus `json.Marshal` and SHA256 are the authority for the prototype's hash chain; Python only transports JSON. Interoperability is claimed only for the vectors and DTO actually tested.
- All databases are new C fixtures. `domain_objects` in fixtures is a deliberately minimal fake canonical-subject table, not a production migration or an authority store. FK/relational consistency and an ExpectedContext match are not Owner authentication or business acceptance.

No D migration number, old-database operation, scheduler, native approved plan, current authority root lookup, actual refs/suite/checker/REPORT aggregation or ordinary LIVE Goal 503 exception is implemented.
