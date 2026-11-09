from pathlib import Path
import ast
import difflib
import hashlib
import json
import re

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99'
START = BASE / 'cancel_finalization_v5_startup_caller_revision_codex/4639ce79ec914062ad92c278533a128f'
DOC = START / 'snapshots/author-fd227/snapshot/v5'
SQL = START / 'snapshots/author-fd227/candidate.sql.txt'
SUP = BASE / 'cancel_finalization_udf_producer_supplement_codex/9d5612d4e27d43e09250867e88edcc9e'
PRIOR = BASE / 'f08_callback_purity_readonly_codex/18d7b84d710a4ba4a2e707c8263b56eb'
DRIVER = ROOT / '.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1'

def ref(p, b=None):
    if b is None: b = p.read_bytes()
    return {'path': p.as_posix(), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def write(name, value):
    with (OUT / name).open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def write_text(name, text):
    with (OUT / name).open('x', encoding='utf8', newline='\n') as f: f.write(text)

inputs = [ROOT / p for p in [
    'AGENTS.md', 'go.mod', 'go.sum', 'internal/domain/backup_host_configuration.go',
    'internal/domain/client_command_identity.go', 'internal/domain/client_protocol.go',
    'internal/domain/client_protocol_schema.go', 'internal/domain/contracts.go', 'internal/canonical/jcs.go',
    'internal/domain/contracts/client.protocol.schema.json', 'internal/domain/contracts/client.protocol.domain.schema.json']]
inputs += [DRIVER / n for n in ['sqlite.go', 'conn.go', 'driver.go', 'func_test.go']]
inputs += [DOC / n for n in ['closed-contract.md', 'source-contract.md', 'evaluator-v5.md']]
inputs += [SQL, START / 'complete_scope21.json', START / 'reserved_absent_paths.json', START / 'manifest.json', START / 'handoff.json', SUP / 'scope_supplement.json']
inputs += [PRIOR / n for n in ['handoff.json', 'manifest.json', 'partial-callgraph.json', 'findings.json']]

# These are public dependency source inventory only. Reading these bytes is not
# execution, an exhaustive purity proof, or actual compiler-consumption evidence.
jsonschema_parent = ROOT / '.local/gopath/pkg/mod/github.com/santhosh-tekuri/jsonschema'
schema_roots = [p for p in jsonschema_parent.iterdir() if p.name == 'v6@v6.0.3' and p.is_dir()]
assert len(schema_roots) == 1
schema_go = sorted(p for p in schema_roots[0].iterdir() if p.is_file() and p.suffix == '.go' and not p.name.endswith('_test.go'))
inputs += schema_go
assert not (ROOT / 'internal/domain/client_cancel_finalization.go').exists()
assert not (ROOT / 'internal/domain/client_cancel_finalization_test.go').exists()
captured = {p: p.read_bytes() for p in inputs}
before = [ref(p, b) for p,b in captured.items()]
write('inputs.before.json', before)
(OUT / 'snapshots').mkdir(exist_ok=False)
snapshots = []
for i,(p,b) in enumerate(captured.items()):
    dest = OUT / 'snapshots' / (f'{i:03d}-' + p.name)
    with dest.open('xb') as f: f.write(b)
    snapshots.append({'source_ref':ref(p,b),'snapshot_ref':ref(dest,b)})
write('snapshot-map.json', snapshots)

driver_raw = captured[DRIVER / 'sqlite.go']
original = driver_raw.decode('utf8')
flag_anchor = '\tDeterministic bool\n'
assert original.count(flag_anchor) == 1
modified = original.replace(flag_anchor, flag_anchor + '\n\t// Innocuous explicitly attests that the function has no side effects and\n\t// cannot expose information beyond its arguments. Default false. It is\n\t// independent of Deterministic and permits audited schema use when\n\t// trusted_schema is OFF. Never enable this without a complete audit.\n\tInnocuous bool\n', 1)
anchor = '\tif impl.Deterministic {\n\t\ttextrep |= sqlite3.SQLITE_DETERMINISTIC\n\t}\n'
assert modified.count(anchor) == 1
modified = modified.replace(anchor, anchor + '\n\tif impl.Innocuous {\n\t\ttextrep |= sqlite3.SQLITE_INNOCUOUS\n\t}\n', 1)
patch = ''.join(difflib.unified_diff(original.splitlines(True), modified.splitlines(True), fromfile='a/sqlite.go', tofile='b/sqlite.go'))
write_text('modernc-sqlite-innocuous.patch', patch)
write('dependency-patch-contract.json', {'kind':'PROPOSED_PINNED_FORK_PATCH_NOT_CACHE_EDIT',
    'module':'modernc.org/sqlite', 'declared_version':'v1.60.1', 'actual_source_ref':ref(DRIVER/'sqlite.go',driver_raw),
    'fork_relative_path':'sqlite.go', 'patched_source_sha256':hashlib.sha256(modified.encode('utf8')).hexdigest(),
    'default_false':True, 'existing_wrappers_unchanged':True, 'conn_engine_unchanged':True,
    'flags_added_only_when_explicit_true':['SQLITE_INNOCUOUS'], 'go_mod_go_sum_future_binding':'MISSING_REQUIRES_ROOT_SEPARATE_SCOPE_AND_PIN',
    'compilation':'NOT_RUN_UNPATCHED_DRIVER_HAS_NO_INNOCUOUS_FIELD',
    'pure_registration_tests_ref':ref(OUT/'function_innocuous_test.go.proposed.txt')})

proposals = [('client_cancel_finalization.go.proposed.txt','internal/domain/client_cancel_finalization.go'),
    ('client_cancel_finalization_test.go.proposed.txt','internal/domain/client_cancel_finalization_test.go')]
domain_patch = ''
for name,path in proposals:
    body = (OUT/name).read_text(encoding='utf8')
    domain_patch += ''.join(difflib.unified_diff([],body.splitlines(True),fromfile='/dev/null',tofile='b/'+path))
write_text('domain-new-files.patch',domain_patch)

sql_lines = captured[SQL].decode('utf8').splitlines()
registry=[]
actions=[]
for number,line in enumerate(sql_lines,1):
    if 316 <= number <= 350:
        m=re.search(r"SELECT '([^']+)',json_array\((.*)\) FROM ([a-z_]+)",line)
        if m:
            registry.append({'category':m[1], 'table':m[3], 'positional_expression_exact':m[2],
                'source_ref':ref(SQL,captured[SQL]), 'line':number,
                'typing_gates':[{'line':i,'text':x} for i,x in enumerate(sql_lines,1) if ('FROM '+m[3]+' WHERE ') in x and 'typeof(' in x and i<316]})
    for m in re.finditer(r"researchos_f08_proof_v1\(([0-9]+),CAST\(json_object\('action','([^']+)'",line):
        actions.append({'mode':int(m[1]),'action':m[2],'line':number,'source_ref':ref(SQL,captured[SQL])})
assert len(registry)==34 and len(set(x['category'] for x in registry))==34
write('source-registry34.exact.json', {'source_ref':ref(SQL,captured[SQL]), 'categories':registry,
    'preservation':'Original SQL source bytes, positional expressions and typeof clauses are authoritative. This is text extraction, not SQLite parsing/evaluation.',
    'empty_categories':'Zero contributing rows is legal; cannot require one row per category.',
    'exception':'domain_refs is an unkeyed multiset; do not globally deduplicate equal rows.'})
write('mode-action-literals.exact.json', actions)

mode_details = [
 (0,'ADMITTED','Validate complete closed transport/root/member digests; reconstruct original private CANCEL envelope and identity; original pre-mutation target Goal/Run and full Task membership; exact versions/runtime/dispatch/origin/Session/fence/queue; R1 reference closure and exact pins.'),
 (1,'FINALIZED','Resolve and recompute immutable admitted group. Revalidate every final member, final versions/events, selected epoch ownership, all run-wide effects/reserves/costs, queue/SDK/native proof, prior epochs and permitted carry. Recompute raw response/snapshot/other-pending preservation and group/pins.'),
 (2,'ORIGIN_VERIFY','Independently derive full mode8 origin and compare all fields/hash. Insertion-time heads and historical captured anchors are distinct. Old23 exclusion is permanent by project+RunID.'),
 (3,'LEGACY_INVENTORY','Backup/upgrade-only original source23 authenticated snapshot inventory; complete Run-ID union and ordered version/dispatch tuples. Concrete caller action/row binding not present in SQL triggers; must be specified, not guessed.'),
 (4,'DISPATCH_TRANSITION','Complete original/NEW tuple keys/raw manifest/prepared_at immutability; permitted monotone state/identity/worker changes; exact current Run/Task/epoch and cancellation fence; deferred authentic observation obligation, not nonexistent future proof.'),
 (5,'JOURNAL_AND_COMMIT','Original request/header/identity/control and complete admitted/final materialization; distinct ACK insert/original COMPLETED/ACK promotion/commit paths. Call local request/response validation only with arguments reconstructed from verified real source rows. Preserve every non-body journal column/type and every unrelated pending command.'),
 (6,'CONTROL_TRANSITION','Actual original control identity/target/member set, original_response/final_response raw bytes and CONFIRMED semantics; no copied-row/session/current-head substitute or all-status exemption.'),
 (7,'MATERIALIZATION','Exact parent transport member index/task/body/root/admitted-member hashes and exact pins including nullable original content hash; reject extra/missing/duplicate materialization, preserve multiset references but unique pin set.'),
 (8,'ORIGIN_DERIVE','Complete R2 permanent birth and current epoch authority, INITIAL_CLAIM/CHECKPOINT_RESUME/RESOURCE_SWITCH, unique route/carry/dependency evidence, complete settled prior-epoch prefix, authentic original runtime/profile/qualification/lease. No future RUN_CHANGED and no manufactured epoch1.'),
]
write('mode-implementation-matrix.json', {
 'request_callback':{'state':'SOURCE_CANDIDATE_LOCAL_CHECKS_UNCOMPILED', 'authentication':'Not established by local function; immutable SQL principal binding belongs to mode evaluator'},
 'response_callback':{'state':'SOURCE_CANDIDATE_LOCAL_CHECKS_UNCOMPILED','not_proven':'Whether roots/control/snapshot/pending set are real source facts; summary input alone is not that proof.'},
 'digest_modes':{'modes':[-1,-2],'state':'SOURCE_CANDIDATE_UNCOMPILED','mutation_authority':False},
 'mode9':{'state':'SOURCE_CANDIDATE_UNCOMPILED','result':'Fixed error for every BLOB input'},
 'proof_modes':[{'mode':m,'name':n,'state':'NOT_IMPLEMENTED_FAIL_CLOSED_NOT_A_COMPLETED_CALLBACK','required_code':d,'actual_actions':[x for x in actions if x['mode']==m]} for m,n,d in mode_details],
 'integration_permitted':False, 'SQL24_permitted':False, 'source_ready':False})

write('next-evaluator-implementation.json', {
 'authoritative_contract_refs':[ref(DOC/n,captured[DOC/n]) for n in ['closed-contract.md','source-contract.md','evaluator-v5.md']]+[ref(SQL,captured[SQL]),ref(START/'complete_scope21.json',captured[START/'complete_scope21.json'])],
 'use_latest_v5_over_earlier_supplement':['proof_v1 replaces old witness_v1','No response1MiB/identity1MiB/witness64KiB cap','R1 keeps duplicate reference occurrences','R2 later epochs use already-written current Run/Task and do not require future RUN_CHANGED','mode9 is fixed error only'],
 'code_modules_still_needed':[
  {'proposed_private_functions':['f08DecodeSources34','f08IndexActualPrimaryKeys','f08ResolveVersion','f08ResolveCurrentHead'], 'depends':['source-registry34.exact.json','SQL typeof gates','domain schema full definitions'], 'obligation':'Decode uppercase even-length raw hex; exact tuple width/types/nullability; no PK duplicates except legal repeated domain_refs; current head equals exact stored immutable version; historical references never substitute a new head.'},
  {'proposed_private_functions':['f08DeriveReferenceOccurrences','f08ValidateReferenceClosure','f08CollectExactPins'], 'depends':['evaluator-v5.md R1','schema-defined relation traversal','original domain_refs producer'], 'obligation':'Body-derived occurrence multiset and exact explicit VersionRefs; ID-only historical target revisions retained from original captured rows; distinguish multiset rows, unique pins, unique task membership and ordered dependency arrays.'},
  {'proposed_private_functions':['f08DeriveBirth','f08DeriveEpochAuthority','f08DeriveOrigin','f08ValidateOriginHistory'], 'depends':['evaluator-v5.md R2','actual outbox events','run_dependencies','routes','checkpoint_carries','immutable runtime/profile/qualification refs'], 'obligation':'Permanent birth event and task-at-claim, no epoch1 assumption; later exact R-1/current R/route/carry and all prior epochs; reproduce actual old-source bytes without fabricating missing ancestry.'},
  {'proposed_private_functions':['f08ValidateEffectClosure','f08ValidateNativeObservation','f08ValidateArtifactBytes','f08ValidateQueueClosure'], 'depends':['original domain schemas','effects/reservation/cost relation producers','dispatch and observation proof producers','SDK receipt and queue state contracts'], 'obligation':'Full current Run-wide keys/sequence/state and original request/reserve/cost facts including zero-money UNKNOWN; authentic native observation/cleanup/upload/use bytes, same-generation SDK chain; no prefix/status/label-only acceptance.'},
  {'proposed_private_functions':['f08EvaluateAdmitted','f08EvaluateFinal','f08EvaluateDispatchTransition','f08EvaluateControlTransition','f08EvaluateJournal','f08EvaluateMaterialization','f08ValidateLegacyInventory'], 'depends':['all previous pure modules','mode-implementation-matrix.json','exact frozen SQL action/row boundaries'], 'obligation':'Only after complete source-derived proof may callback return1 or canonical derived origin. Recompute every supplied digest; preserve unrelated pending commands, all non-body journal columns, immutable identities, old23 inventory and later Run ownership.'}],
 'reusable_implemented_functions':['f08BuildCallbacks','f08Boundary','f08Strict','f08Object','f08String','f08Integer','f08HashString','f08RawHash','f08Encode','f08ValueHash','f08Request','f08ResponseBody','f08Response'],
 'not_reusable_as_proof':['f08ProofFrame: structural scaffold only','standalone response_proof/root-hash supplied by arbitrary caller','old shared backupConfigurationSchema cache','DB-aware client command identity lookup/reserve helpers'],
 'definition_gap':['Mode3 is named in source-contract57 but no SQL action literal binds it; next backup/upgrade caller interface must supply and review a concrete exact row/action/source23 archive binding. Current candidate accepts no guessed alias.'],
 'production_state':'No callbacks installed; no migration or business code written; Main/worktrees/module cache unchanged.'})

def lexical_check(s):
    # Delimiter/comment/string sanity only. This is explicitly NOT a Go parser.
    stack=[]; i=0
    while i<len(s):
        if s.startswith('//',i):
            j=s.find('\n',i); i=len(s) if j<0 else j+1; continue
        if s.startswith('/*',i):
            j=s.find('*/',i+2); assert j>=0; i=j+2; continue
        if s[i] in ['"',"'",'`']:
            quote=s[i]; i+=1
            while i<len(s):
                if quote!='`' and s[i]=='\\': i+=2; continue
                if s[i]==quote: i+=1; break
                i+=1
            else: raise AssertionError('unclosed literal')
            continue
        if s[i] in '([{': stack.append(s[i])
        elif s[i] in ')]}': assert stack and stack.pop()=={')':'(',']':'[','}':'{'}[s[i]]
        i+=1
    assert not stack

texts={n:(OUT/n).read_text(encoding='utf8') for n in ['client_cancel_finalization.go.proposed.txt','client_cancel_finalization_test.go.proposed.txt','function_innocuous_test.go.proposed.txt']}
text_checks=[]
for name,s in texts.items():
    lexical_check(s)
    funcs=[{'name':m[1], 'line':s[:m.start()].count('\n')+1} for m in re.finditer(r'^func\s+(?:\([^\n]*\)\s+)?([A-Za-z_][A-Za-z_0-9]*)\(',s,re.M)]
    text_checks.append({'ref':ref(OUT/name),'delimiter_check':'BALANCED_TEXT_ONLY','functions':funcs})
ast.parse(Path(__file__).read_text(encoding='utf8'))
write('static-text-audit.json', {'python_metadata_ast':'PARSED_ONLY', 'go_ast':'NOT_RUN', 'gofmt':'NOT_RUN','compile':'NOT_RUN','tests':'NOT_RUN','files':text_checks,
    'production_source_absence_checked':True,'driver_flag_patch_text_anchors':2,
    'purity_scope':'Callback closures ignore FunctionContext and use per-init private schema; actual schema/compiler transitives need independent review. No DB/Host/cache lookup in proposed function bodies.'})
write('dependency-callgraph.json', {
 'kind':'SOURCE_SYMBOL_GRAPH_NOT_COMPILED_CALLGRAPH',
 'candidate_function_locators':text_checks[0]['functions'],
 'candidate_ref':ref(OUT/'client_cancel_finalization.go.proposed.txt'),
 'edges':[
  ['init','f08BuildCallbacks','sqlite.RegisterFunction'],
  ['f08BuildCallbacks','bytes.Clone','f08RawHash','LoadSchemaWithExternals','f08Boundary'],
  ['request closure','f08Blob','f08Request'],
  ['response closure','f08Blob','f08Response'],
  ['proof closure','f08Blob','f08Strict','f08RawHash','f08ProofFrame'],
  ['f08Strict','canonical.JSON','json.Decoder.UseNumber','sameNumbers','utf8.Valid','errors.Is'],
  ['f08Request','f08Strict','f08Object','f08String','f08Integer','base64.Strict.DecodeString','base64.EncodeToString','SchemaDoc.ValidateDefInput','DecodeEnvelope','Envelope.ContentHash'],
  ['f08Response','f08Request','f08ResponseBody','f08HashString','f08ValueHash','f08Integer'],
  ['f08ResponseBody','f08Strict','SchemaDoc.ValidateDef','DecodeResponse','ValidateResultAgainstMethod','f08Integer'],
  ['f08Integer','big.Rat.SetString','big.Rat.IsInt','big.Int.IsInt64','big.Int.Int64'],
  ['f08RawHash','sha256.Sum256','hex.EncodeToString'],
  ['LoadSchemaWithExternals','Decode','localOnly.Load','jsonschema.NewCompiler','Compiler.AssertFormat','Compiler.AddResource','Compiler.Compile','neutralizePatterns'],
  ['SchemaDoc.validate','Bytes','firstWriteOnly','firstBadRelativePath','defChecks','jsonschema.Schema.Validate'],
  ['DecodeEnvelope session.control branch','canonical.JSON','methodsV2 read','writeMethods read','Envelope.validatePayload'],
  ['Envelope.ContentHash','mustMarshal','compactJSON','canonicalHash','canonicalBytes'],
  ['DecodeResponse session.control branch','methodsV2 read','json.Unmarshal'],
 ],
 'public_existing_domain_source_refs':[ref(ROOT/p,captured[ROOT/p]) for p in ['internal/domain/client_protocol.go','internal/domain/client_protocol_schema.go','internal/domain/contracts.go','internal/canonical/jcs.go']],
 'schema_library_source_refs':[ref(p,captured[p]) for p in schema_go],
 'init_only_writes':['modernc default driver registration registry','new private compiled SchemaDoc/maps'],
 'callback_visible_global_reads':['Existing methodsV2/writeMethods static package maps inside DecodeEnvelope/DecodeResponse; no writes in candidate; independent review must confirm no reachable mutation in final linked program'],
 'conditional_branch_bound':'Exact method session.control is checked before existing method-specific decoders. No host.configure or DB-aware identity helper is called by candidate.',
 'not_claimed':['No actual Go compiler call graph','No exhaustive stdlib/library transitive purity certification','No complete proof evaluator','No resource-exhaustion safety proof; unbounded legal response/proof parser cost remains to measure under actual grant']})
selectors=[]
for x in text_checks:
    selectors += [{'name':f['name'],'line':f['line'],'source_ref':x['ref'],'state':'NOT_RUN','execution_authorized':False} for f in x['functions'] if f['name'].startswith('Test')]
assert len(selectors)==13
write('future-selector-roster.json', {'top_level_selectors':selectors,'top_level_count':13,'expected_expanded_leaf_count_design_only':58,
 'expanded_leaf_count_not_measured':True,'compile_prerequisites':['separately approved driver fork/pin','reviewed candidate source patch scope','full pinned compiler/schema/dependency/exe closure and independent actual grant'],
 'pure_component_caps_proposed':{'top_level_invocations':13,'per_selector_seconds':120,'HTTP':0,'SDK':0,'MODEL':0,'SQL':0},
 'not_covered':['Actual physical connections and trusted_schema=OFF SQL execution','complete proof modes0..8','fresh24/upgrade/rollback/backup/restore','all private schema-library transitive purity and resource exhaustion']})

after=[ref(p,p.read_bytes()) for p in inputs]
assert before==after
write('inputs.after.json',after)
write('tool-diagnostics.json',{'metadata_read_tool_chunks':[{'id':x,'actual_outer_exit':0,'actual_native_python_exit':0} for x in ['1966c5','f7f33c','fd4ef2','66d777','b2dd84','6aeeeb','819e59','f9b999','758bc4','e52794']],
 'new_failure_origins':[],'native_product_SQL_Go_Node_HTTP_MODEL_calls':0,'counter_changes':0,
 'output_truncation':'Some console reads truncated display; complete original document bytes are snapshotted. No truncation is treated as a complete read/verification of all transitive code.',
 'seal_exit':'Reported separately by actual caller tool; no future exit self-asserted.'})
write('handoff.json',{'schema':'researchos.f08-callback-source-preparation.v1','actor':'codex:/root/sources_parent_impl',
 'status':'PARTIAL_CONCRETE_CANDIDATE_NOT_FOR_INTEGRATION','writer':'STOPPED_AFTER_SEAL','source_ready':False,'product_accepted':False,'authorization_for_execution':False,
 'candidate_ref':ref(OUT/'client_cancel_finalization.go.proposed.txt'), 'test_candidate_ref':ref(OUT/'client_cancel_finalization_test.go.proposed.txt'),
 'dependency_patch_ref':ref(OUT/'modernc-sqlite-innocuous.patch'),'domain_patch_ref':ref(OUT/'domain-new-files.patch'),
 'mode_matrix_ref':ref(OUT/'mode-implementation-matrix.json'),'next_implementation_ref':ref(OUT/'next-evaluator-implementation.json'),
 'registry_ref':ref(OUT/'source-registry34.exact.json'),'selector_roster_ref':ref(OUT/'future-selector-roster.json'),
 'input_count':len(inputs),'input_drift':[],'compilation':'NOT_RUN_UNPATCHED_DRIVER_INCOMPATIBLE','tests':'NOT_RUN','actual_case_count':0,
 'mandatory_before_opt_in':['Non-author complete source/transitive purity review','Complete mode0..8 authority evaluator; all-error refusal is NOT completion','Exact pinned driver fork and Root source leases','New controlled compiler/SQL/unit execution grants'],
 'unchanged':['Main','all worktrees','module cache','canonical/index','sealed historical receipts','failure counters']})
write('manifest.json',{'schema':'researchos.readonly-manifest.v1','files':[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file()],'self_excluded':True})
print(json.dumps({'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'candidate':ref(OUT/'client_cancel_finalization.go.proposed.txt'),'input_count':len(inputs),'drift':0,'tests':0},ensure_ascii=False))
