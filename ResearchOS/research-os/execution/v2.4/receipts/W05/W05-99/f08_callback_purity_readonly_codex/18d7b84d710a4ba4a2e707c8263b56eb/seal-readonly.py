from pathlib import Path
import hashlib
import json

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99'
START = BASE / 'cancel_finalization_v5_startup_caller_revision_codex/4639ce79ec914062ad92c278533a128f'
DOC = START / 'snapshots/author-fd227/snapshot/v5'
PRIOR = BASE / 'f08_innocuous_gap_readonly_codex/3dda0d3a44bc475685a1de15cff15c06'
CATALOGS = [
    BASE / 'cancel_finalization_udf_producer_supplement_codex/9d5612d4e27d43e09250867e88edcc9e',
    BASE / 'cancel_finalization_closed_contract_revision_v5_codex/669a7381fd594e88b8570b67a507596a',
    START,
]
SOURCES = ['internal/domain/backup_host_configuration.go', 'internal/domain/client_protocol_schema.go',
    'internal/domain/contracts.go', 'internal/domain/client_command_identity.go',
    'internal/domain/client_protocol.go', 'internal/canonical/jcs.go', 'go.mod', 'go.sum', 'AGENTS.md',
    '.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/sqlite.go',
    '.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/conn.go',
    '.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/driver.go']
paths = [ROOT / x for x in SOURCES]
paths += [p / n for p in CATALOGS for n in ['manifest.json', 'handoff.json']]
paths += [START / 'reserved_absent_paths.json', START / 'complete_scope21.json']
paths += [DOC / n for n in ['closed-contract.md', 'source-contract.md', 'evaluator-v5.md']]
paths += [PRIOR / n for n in ['handoff.json', 'manifest.json', 'findings.json', 'minimum-patch-proposal.json', 'historical-errors.original.json']]

def reference(p, raw):
    return {'path': p.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def emit(name, value):
    with (OUT / name).open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

captured = {p: p.read_bytes() for p in paths}
before = [reference(p, raw) for p, raw in captured.items()]
emit('inputs.before.json', before)
(OUT / 'snapshots').mkdir(exist_ok=False)
snapshots = []
for i, (p, raw) in enumerate(captured.items()):
    target = OUT / 'snapshots' / (f'{i:02d}-' + p.name)
    with target.open('xb') as f:
        f.write(raw)
    snapshots.append({'original': reference(p, raw), 'snapshot': reference(target, raw)})
emit('snapshot-map.json', snapshots)

def evidence(relative, first, last):
    p = ROOT / relative
    return {'source_ref': reference(p, captured[p]), 'locator': {'first_line': first, 'last_line': last}}

catalog = []
for p in CATALOGS:
    obj = json.loads(captured[p / 'manifest.json'])
    rows = obj['files']
    names = [str(x['path']).replace('\\', '/') for x in rows]
    catalog.append({'manifest_ref': reference(p / 'manifest.json', captured[p / 'manifest.json']),
        'listed_files': len(rows), 'go_member_count': sum(x.endswith('.go') for x in names),
        'callback_source_members': [x for x in names if x.endswith('/client_cancel_finalization.go') or x == 'client_cancel_finalization.go']})
assert all(not x['callback_source_members'] for x in catalog)
reserved = json.loads(captured[START / 'reserved_absent_paths.json'])
assert any(x['path'] == 'internal/domain/client_cancel_finalization.go' and x['status'] == 'ABSENT_NEW_RESERVED_SOURCE_NO_FILE_CREATED' for x in reserved)
assert not (ROOT / 'internal/domain/client_cancel_finalization.go').exists()
emit('catalog-audit.json', {'catalogs': catalog, 'reserved_absent_records': reserved,
    'main_callback_source_exists': False,
    'limit': 'Bounded catalog and current named-path check; no claim that every filesystem location or unsealed worktree was searched.'})

contract_ref = reference(DOC / 'closed-contract.md', captured[DOC / 'closed-contract.md'])
callbacks = []
for name, signature, lines, promise in [
    ('researchos_f08_cancel_request_v1', '(BLOB header, BLOB identity)', [94, 95], 'Strict private header and identity, original envelope <=1048576 bytes, fixed header bound, canonical base64 and full CANCEL envelope, exact Q/R tuple.'),
    ('researchos_f08_cancel_response_v1', '(BLOB header, BLOB binding, BLOB-or-NULL old, BLOB new, INTEGER mode)', [97, 102], 'Modes 0/1/2 and full original response schemas, byte digests, identity and snapshot proof. No invented response-size cap.'),
    ('researchos_f08_proof_v1', '(INTEGER mode, BLOB input)', [104, 111], 'Digest modes -1/-2 have no authority; proof modes 0..8 verify passed facts; later mode9 unconditionally refuses storage-class violation.'),
]:
    callbacks.append({'name': name, 'planned_signature': signature,
        'decision': 'REQUEST_MISSING_CALLBACK_SOURCE', 'innocuous_opt_in_permitted': False,
        'body_ref': None, 'init_registration_ref': None, 'actual_transitive_graph': None,
        'determinism_proven': False, 'side_effect_freedom_proven': False,
        'environment_database_time_random_access': 'UNKNOWN_NO_CALLBACK_BODY',
        'argument_validation_exception_size_behavior': 'NOT_IMPLEMENTED_OR_NOT_PRESENT_IN_REVIEWED_CATALOG',
        'contract_promise_not_execution': promise,
        'contract_evidence': {'ref': contract_ref, 'locator': {'first_line': lines[0], 'last_line': lines[1]}}})
emit('callback-purity-matrix.json', callbacks)

graph = [
 {'node': 'loadBackupConfigurationSchema', 'evidence': evidence('internal/domain/backup_host_configuration.go', 31, 42),
  'actual_direct_calls': ['Digest', 'LoadSchemaWithExternals'], 'finding': 'Fixed source hash guards are useful. backupConfigurationSchema is a separate shared sync.Once/doc/error cache; cannot be silently reused as the promised private F08 initialization.'},
 {'node': 'LoadSchemaWithExternals / SchemaDoc.validate', 'evidence': evidence('internal/domain/client_protocol_schema.go', 28, 217),
  'actual_direct_calls': ['Decode', 'jsonschema.NewCompiler', 'UseLoader(localOnly{})', 'AssertFormat', 'neutralizePatterns', 'Bytes', 'Schema.Validate'],
  'finding': 'Schema construction mutates new maps; SchemaDoc has mutable maps and exported fields. Private cloned initialization is required by contract. Whole schema-library call graph and custom format/pattern state are not proven by this bounded audit.'},
 {'node': 'localOnly.Load / Decode / Bytes / Hash / Digest', 'evidence': evidence('internal/domain/contracts.go', 30, 103),
  'actual_direct_calls': ['canonical.JSON', 'json.NewDecoder', 'sameNumbers', 'json.Marshal', 'sha256.Sum256', 'hex.EncodeToString'],
  'finding': 'localOnly returns error rather than loading a URL. Decode keeps numeric checks. Bytes and Hash can panic on unsupported values/invalid canonical JSON; callbacks need explicit typed decoding and safe error propagation. No DB/environment/time/random access observed in these particular bodies; file-level imports alone are not a call graph.'},
 {'node': 'canonical.JSON', 'evidence': evidence('internal/canonical/jcs.go', 1, 21),
  'actual_direct_calls': ['json.Unmarshal', 'jsontext.Value.Canonicalize'],
  'finding': 'Clones input and validates canonical JSON. Deterministic byte transformation at this source boundary; not a proof of the missing F08 evaluator.'},
 {'node': 'readClientCommandEnvelope / decodeClientIdentityEnvelope', 'evidence': evidence('internal/domain/client_command_identity.go', 37, 95),
  'additional_evidence': evidence('internal/domain/client_command_identity.go', 213, 275),
  'actual_direct_calls': ['canonical.JSON', 'json.Unmarshal', 'SchemaDoc.ValidateDefInput', 'base64.StdEncoding.Strict().DecodeString', 'validateClientIdentityRequest'],
  'finding': 'Header and raw envelope have existing bounds. Empty/legacy headers can return known=false without error; a F08 callback must explicitly require known=true. Original request ContentHash must not be replaced with raw-byte SHA.'},
 {'node': 'validateClientDerivedSession and reservation/lookup helpers', 'evidence': evidence('internal/domain/client_command_identity.go', 278, 310),
  'actual_direct_calls': ['QueryRowContext', 'clientSessionCreationPrincipal'],
  'finding': 'These higher-level helpers read DB state and are NOT permitted inside pure callbacks. Callback source facts must arrive in arguments from the transaction producer. This does not accuse the nonexistent callback of calling them.'},
 {'node': 'Envelope.ContentHash / canonicalHash', 'evidence': evidence('internal/domain/client_protocol.go', 367, 451),
  'actual_direct_calls': ['mustMarshal', 'compactJSON', 'json.Unmarshal', 'canonicalBytes', 'sha256.Sum256'],
  'finding': 'Local deterministic processing including sorted object keys; preserve existing canonical protocol hash semantics and exact tuple checks.'},
 {'node': 'DecodeResponse / ValidateResultAgainstMethod', 'evidence': evidence('internal/domain/client_protocol.go', 481, 626),
  'finding': 'DecodeResponse alone admits legacy status vocabulary; method validator returns early on non-COMPLETED/nil doc/result. Full frozen CommandResponse schema validation is separately mandatory for ACK and refusals. Method-only success does not prove a valid response.'},
]
emit('partial-callgraph.json', {'roots_present': False, 'kind': 'EXISTING_HELPER_BODIES_ONLY_NOT_F08_TRANSITIVE_CLOSURE', 'nodes': graph,
    'missing': ['actual init and three callback bodies', 'all actual evaluators and recursive validators called by those bodies', 'reachable schema-library callbacks and global state', 'actual exception mapping, retained argument policy, recursion/resource behavior']})

emit('minimal-patch-and-prerequisites.json', {
 'status': 'PROPOSAL_ONLY_NO_SOURCE_LEASE',
 'driver': {'version': 'modernc.org/sqlite v1.60.1 (actual frozen local bytes)',
   'evidence': evidence('.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/sqlite.go', 510, 564),
   'registration_evidence': evidence('.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1/sqlite.go', 815, 850),
   'minimal_change': 'In a separately reviewed pinned dependency fork, add explicit FunctionImpl.Innocuous bool default false; only when true OR SQLITE_INNOCUOUS into eTextRep in Driver.registerFunction. Keep existing deterministic wrappers, conn forwarding and engine unchanged. Never edit module cache in place.',
   'capability_is_not_permission': True},
 'domain': {'future_path': 'internal/domain/client_cancel_finalization.go',
   'minimal_change_after_bodies_reviewed': 'Register only these three audited scalar functions during package init before any default-driver Open, using explicit deterministic and innocuous flags. Private cloned fixed-hash schemas initialized once before registration; no callback DB/FS/env/network/clock/random or mutable validation flags; no retained SQL arguments/FunctionContext.',
   'opt_in_blocked_now': True},
 'non_substitutes': ['DETERMINISTIC is not INNOCUOUS', 'DIRECTONLY prohibits required trigger/view use', 'trusted_schema=ON is not a fix', 'no broad marking of all deterministic functions', 'no callback SQL hook/reentry or unsafe handle patch'],
 'review_before_execution': ['Complete candidate body/init/source blobs and all transitive functions', 'Prove read-only immutable private schema and no captured mutable host/global facts', 'Explicit SQL driver.Value type checks, allowed NULL position, integer modes, BLOB exact bytes including NUL; known=true private header', 'No undocumented size cap for response/proof; preserve existing header/envelope bounds and document bounded evaluation/resource failure behavior', 'Panic/error paths cannot expose input secrets or become success/NULL; return fixed typed errors where appropriate'],
 'official_basis': 'https://www.sqlite.org/c3ref/c_deterministic.html',
 'prior_dependency_audit_ref': reference(PRIOR / 'handoff.json', captured[PRIOR / 'handoff.json'])})

tests = [
 ('F08PureRegistrationFlagsDefaultOff', 'Existing wrappers remain unflagged; explicit opt-in is the only INNOCUOUS registration.'),
 ('F08PureThreeFunctionsEachPhysicalConnection', 'All three exact names/arity/flags on each real connection; default init before Open, custom driver noninheritance explicit.'),
 ('F08PureTrustedSchemaOffTriggerAndView', 'Valid production trigger/view inputs execute actual guards with OFF; unrelated unflagged function still rejected; no ON fallback.'),
 ('F08PureInputTypeAndNullMatrix', 'TEXT/BLOB/INTEGER/REAL/NULL/arity and embedded-NUL controls; only documented old-response NULL and actual SQLite source storage exceptions.'),
 ('F08PureHeaderBoundsAndStrictDecoding', 'Existing raw/header/base64 boundaries, empty legacy known=false, duplicate keys, Unicode, numbers and full schemas; no new response cap.'),
 ('F08PureExactOriginalRequestResponseIdentity', 'Single-change original request/hash/identity/response/body multiset and order negative controls; no digest-only authority.'),
 ('F08PureAllModesAndMode9Refusal', 'Every contract mode including -1/-2 no authority, 0..8 semantics, fixed 9 error; unknown mode errors never NULL or success.'),
 ('F08PureRepeatedInputsAndConcurrentConnections', 'Identical input outputs/errors independent of call order, other SQL, connections, time/env; source review is still required beyond finite tests.'),
 ('F08PureNoRetainedArgumentsOrCallbackIO', 'Audit actual full graph and lifetime; no DB callbacks, filesystem/env/clock/random/logging/network, no mutable ready/cache state.'),
 ('F08PureInvalidNestedValuesNoPanicLeak', 'Deep/large/malformed/schema/panic-adjacent inputs produce documented refusal without input-secret error leakage; do not introduce unapproved contract caps.'),
 ('F08PureTamperedPrivateSchemaInitRefusal', 'Missing or changed private embedded bytes refuse initialization; no fallback schema/loader or post-init map mutation.'),
 ('F08PureStartupUpgradeBackupRestoreBindings', 'Future admitted source scope must separately execute fresh24 first/second startup and original22/23 upgrade/rollback/restore paths with actual physical connection flags. No present product acceptance.'),
]
emit('future-validation-cases.json', [{'selector_proposal': n, 'required_assertion': a, 'state': 'NOT_RUN', 'authorization': False} for n, a in tests])
emit('findings.json', {'decision': 'REQUEST_MISSING_CALLBACK_SOURCE', 'three_callback_opt_in_permitted': False,
 'source_accepted': False, 'product_accepted': False,
 'findings': [
  {'id': 'P01', 'severity': 'BLOCKING_REVIEW_INPUT', 'message': 'Three reviewed catalogs lack the candidate callback source; latest scope reserves it absent. No actual init or complete transitive graph can be audited.'},
  {'id': 'P02', 'severity': 'IMPLEMENTATION_CONDITION', 'message': 'Existing helpers expose shared schema cache, legacy header fallthrough, DB-aware identity helpers and panic-capable hashing; selectively reusing them requires actual call graph proof and strict wrappers.'},
  {'id': 'P03', 'severity': 'DEPENDENCY_CAPABILITY_GAP', 'message': 'Pinned FunctionImpl/registerFunction cannot express INNOCUOUS. A default-off dependency capability patch is distinct from permission to enable it for missing callback implementations.'}],
 'not_inferred': ['No finding claims actual missing callbacks are impure.', 'No static helper review is a SQL test.', 'No finite repeatability test can establish absence of all external side effects.'],
 'historical_failure_policy': 'Prior original payload copied byte-for-byte. Native NULL preserved. No counter writes or repeated old failing inputs.'})

after = [reference(p, p.read_bytes()) for p in paths]
assert before == after
emit('inputs.after.json', after)
emit('tool-diagnostics.json', {'metadata_only': True,
 'current_turn_prior_tools': [{'chunk_id': x, 'actual_outer_exit': 0, 'actual_native_exit': (0 if x != '85bea8' else None)} for x in ['85bea8', 'e416be', 'eb9339', 'bf06b4']],
 'earlier_contiguous_readonly_tools': ['43d9e2', '8f162a', '1c567d', 'da1385', 'c97cdc', '8e3eee', '840b74', 'e304ba', '9ceadd'],
 'earlier_tools': 'Actual outer0 reported; native not independently reconstituted here. See original tool conversation.',
 'new_failure_origins': [], 'go_sql_product_sdk_http_model_calls': 0, 'counter_writes': 0,
 'final_sealer_actual_exit': 'Reported by caller tool only after this script completes; this file does not self-assert future completion.'})
handoff = {'schema': 'researchos.f08-callback-purity-readonly-handoff.v1', 'actor': 'codex:/root/sources_parent_impl',
 'decision': 'REQUEST_MISSING_CALLBACK_SOURCE', 'writer': 'STOPPED_AFTER_SEAL',
 'input_count': len(before), 'input_drift': [], 'callbacks_audited_from_actual_bodies': 0, 'planned_callbacks': 3,
 'actual_tests': 0, 'source_writes': 0, 'canonical_writes': 0, 'source_acceptance': False,
 'findings_ref': reference(OUT / 'findings.json', (OUT / 'findings.json').read_bytes()),
 'matrix_ref': reference(OUT / 'callback-purity-matrix.json', (OUT / 'callback-purity-matrix.json').read_bytes()),
 'partial_graph_ref': reference(OUT / 'partial-callgraph.json', (OUT / 'partial-callgraph.json').read_bytes()),
 'minimal_patch_ref': reference(OUT / 'minimal-patch-and-prerequisites.json', (OUT / 'minimal-patch-and-prerequisites.json').read_bytes()),
 'future_cases_ref': reference(OUT / 'future-validation-cases.json', (OUT / 'future-validation-cases.json').read_bytes()),
 'historical_errors_ref': reference(PRIOR / 'historical-errors.original.json', captured[PRIOR / 'historical-errors.original.json'])}
emit('handoff.json', handoff)
files = [reference(p, p.read_bytes()) for p in sorted(OUT.rglob('*')) if p.is_file()]
emit('manifest.json', {'schema': 'researchos.readonly-manifest.v1', 'files': files, 'self_excluded': True})
print(json.dumps({'handoff': reference(OUT / 'handoff.json', (OUT / 'handoff.json').read_bytes()),
    'manifest': reference(OUT / 'manifest.json', (OUT / 'manifest.json').read_bytes()), 'inputs': len(before), 'drift': 0}, ensure_ascii=False))
