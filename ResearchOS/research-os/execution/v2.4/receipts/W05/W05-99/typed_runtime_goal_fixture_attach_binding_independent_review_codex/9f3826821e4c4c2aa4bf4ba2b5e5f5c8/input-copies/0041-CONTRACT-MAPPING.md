# ATT3: ATTACH-RESTORE-002 timestamp ordering Source

Status: SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_BUILD_AND_TEST.
No formal acceptance, native positive result, or production readiness is claimed.

## Exact scope and preservation

ATT2 remains immutable. The sole production replacement is its restore helper section in client_protocol.go. The previous two test files are copied byte for byte (five attach contract tests plus restore rejection/ordinary-active tests, including ten modes times two clients). Main, T6, Root canonical files, shared migrations, old Sources, and the other author's legacy test branch are untouched. Exact inverse edits restore every ATT2 byte. The preceding Execute/dispatch/handleWrite gates and following session journal implementation are unchanged.

## Time semantics

clientAttachRestoreTime parses RFC3339Nano, rejects unparseable or zero/unknown time, and converts the instant to UTC. Date/time ordering uses time.Time.After/Before/Equal only.

1. Barriers: SELECT every restored_at for the exact project/run, parse every returned value, and choose the latest instant. No SQL max(TEXT) or text timestamp order remains. The current schema has a project/run primary key, but the read path does not depend on text MAX semantics. An unknown timestamp refuses the restore claim.
2. Observations: SELECT all records for the same project/run/current Run lease_epoch without ordering by observed_at. Every timestamp must parse, including records that otherwise appear older. clientAttachObservationOrder selects the actual latest instant; any invalid or partial record at that exact instant makes the latest result invalid, independent of row order. Thus .11Z partial cannot be hidden by .1Z settled, and equivalent offsets/fractional spellings cannot discard a conflicting same-instant fact.
3. Observation identity, receipt hash, spec task/run/epoch, strict-after barrier, Run double-settled flags and observation double-settled flags retain their prior checks. Only after the actual latest instant is valid can the earliest valid fresh instant establish precedence for a generation.
4. Related CLIENT_HANDOFF events keep exact outbox project/session/run and event sequence/command/protocol/current-owner/current-epoch/previous-epoch bindings. effective_at and writer expires_at use the shared UTC parser; expiry must be later than effective time. Malformed JSON/payload/time or impossible expiry ordering refuses the claim. The helper scans all selected related events before accepting a recovered generation; a matching event cannot hide a later-read damaged timestamp. There is no TEXT time sort or early matching-event return.
5. No matching recovered generation with valid fresh evidence still uses the existing HandoffEpoch/CAS/journal transaction. A valid recovered generation follows the existing same-owner lease policy. With no restore barrier, ordinary active-owner renewal is unchanged. The helper contains SELECT statements only and never changes queue/control/barrier/resume flags.

## New Source tests

- TestClientAttachRestoreTimestampOrdering directly exercises the production timestamp parser and observation accumulator with .1Z/.11Z, zero fractional digits versus one nanosecond, offset normalization, both input orders, and conflicting equal instants. It creates no runtime observation.
- TestClientAttachRestoreRelatedTimestampParsing exercises invalid/unknown/missing-zone/impossible-date/zero timestamps and barrier < observation < handoff < expiry using variable fractional precision. The same parser is used at all four production reads.
- TestClientAttachRestoreRejectsMisorderedOrUnknownObservationTime reaches handlerCommand -> Execute -> dispatch -> handleWrite -> clientAttachRestoreState using artificial negative fixtures: fractional later partial, same-instant partial, malformed observation time, and malformed barrier. Both original-owner future lease and another-client acquisition must return SESSION_BUSY without changing Session/Run/barrier or emitting CLIENT_HANDOFF, with stable exact-command replay.

The paired older settled-shaped observation is exclusively part of an invalid negative fixture containing a later partial or unorderable observation (or malformed barrier). It is not a genuine native observation, authority record, real restore positive, or acceptance artifact. No fabricated CLIENT_HANDOFF/history is inserted. No fixture SQL or Go test is executed by this author.

Pure Python comparison evidence is limited to timestamp vectors and a translated accumulator; it is not execution of Go, SQLite, the handler, or the native observation producer. Lexical delimiter scans are not Go parsing.

## Resource gap and Root acceptance

True fresh restore positive remains BLOCKED/PENDING_ROOT_RESOURCE. Root must provide authorized real coordinator/native observations for current Run epoch after the actual latest restore barrier, with durable actual stop/queue evidence. Then an isolated candidate must verify one-generation transfer, exact replay, recovered lease-only renewal, a newer valid same-epoch observation, newer partial refusal, and a later barrier/current-epoch change. Related malformed handoff time is covered by parser Source tests and static all-row control flow here; no real handoff corruption experiment has been run.

Root owns independent Source review, isolated Go compilation/testing, separate legacy-test composition, and any subsequently authorized native resource. Existing active asynchronous takeover and historical cached ACK reconciliation remain open. Native T7 closure and Root CP360 are Root-owned facts, not evidence generated by this Source author.

The two prior Source rejections and all prior mechanical ordinals remain preserved through pinned packages. This ATT3 author pass introduced no new mechanical failure. Nothing is self-approved.

