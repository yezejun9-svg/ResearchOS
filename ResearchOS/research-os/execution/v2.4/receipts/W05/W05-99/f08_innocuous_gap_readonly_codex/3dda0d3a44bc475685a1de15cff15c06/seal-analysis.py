import ast
import hashlib
import json
import pathlib
from datetime import datetime, timezone

ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT=pathlib.Path(__file__).resolve().parent
DEP=ROOT/'.local/gopath/pkg/mod/modernc.org/sqlite@v1.60.1'
F08=ROOT/'execution/v2.4/receipts/W05/W05-99/cancel_finalization_v5_startup_caller_revision_codex/4639ce79ec914062ad92c278533a128f'
UDF=ROOT/'execution/v2.4/receipts/W05/W05-99/cancel_finalization_udf_producer_supplement_codex/9d5612d4e27d43e09250867e88edcc9e'
REVIEW=ROOT/'execution/v2.4/receipts/W05/W05-99/review_f08_v5_startup_caller_codex/f2a1d3715c774ffd8dba7ba434a8209d'
READS=[]
def ref(p,b=None):
    if b is None:b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):
    b=p.read_bytes(); READS.append(ref(p,b)); return b
def write(n,d):
    b=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with (OUT/n).open('xb') as f:f.write(b)
    return ref(OUT/n,b)
def loc(p,a,b):return {'ref':ref(p),'locator':{'line_start':a,'line_end':b}}

ast.parse(pathlib.Path(__file__).read_text(encoding='utf-8'))
paths=[ROOT/'AGENTS.md',ROOT/'go.mod',ROOT/'go.sum',ROOT/'internal/store/sqlite.go',
       ROOT/'execution/v2.4/checkpoint.json',DEP/'go.mod',DEP/'sqlite.go',DEP/'conn.go',DEP/'driver.go',
       DEP/'func_test.go',DEP/'lib/sqlite.go',DEP/'lib/sqlite_windows.go',
       DEP/'lib/sqlite_g_0000000000060000.go',F08/'handoff.json',F08/'proposal.json',
       F08/'complete_scope21.json',F08/'startup-contract.md',
       F08/'snapshots/author-fd227/candidate.sql.txt',
       F08/'snapshots/author-fd227/snapshot/v5/source-contract.md',
       F08/'snapshots/author-fd227/snapshot/v5/closed-contract.md',
       REVIEW/'mandatory_implementation_conditions.json',UDF/'handoff.json',UDF/'scope_supplement.json',
       UDF/'read-errors-and-prior-outer-exit.json',
       ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/f08-udf-copy-r290/copy_audit.json']
raws={str(p):read(p) for p in paths}
cp=json.loads(raws[str(ROOT/'execution/v2.4/checkpoint.json')])
compiler_path=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-public-resources-15ccd02e325b4d0e9384d66bb2a9d924/compiler-resources.json'
compiler=json.loads(read(compiler_path))
pins={str(pathlib.Path(x['path'])).casefold():x for x in compiler['files']}
for p in paths:
    if p.is_relative_to(DEP):
        r=ref(p,raws[str(p)]); pin=pins[str(p).casefold()]
        assert r['sha256']==pin['sha256'] and r['bytes']==pin['bytes']
assert ref(F08/'proposal.json')['sha256']=='3f374c2e90a859f60495b06f3b0b4565068e50882e9fdad81649558c4dd62fe5'
assert ref(F08/'snapshots/author-fd227/candidate.sql.txt')['sha256']=='e3d58e53a76d00cfecb5cf139320f09055c0996c88616e288a49cfdd2ca07736'
contracts=F08/'snapshots/author-fd227/snapshot/v5'
evidence=[
 {'id':'E01','fact':'Declared dependency modernc.org/sqlite v1.60.1; actual pinned cache and engine literal 3.53.4 independently hash-bound. No go mod verify/build executed.', 'refs':[loc(ROOT/'go.mod',1,12),loc(DEP/'lib/sqlite.go',4556,4556)]},
 {'id':'E02','fact':'Public FunctionImpl exposes NArgs/Deterministic/Scalar/MakeAggregate/VolatileArgs, no innocuous/eTextRep option.', 'refs':[loc(DEP/'sqlite.go',505,563)]},
 {'id':'E03','fact':'RegisterDeterministicScalarFunction delegates only Deterministic:true; registerFunction starts UTF8 and ORs DETERMINISTIC alone.', 'refs':[loc(DEP/'sqlite.go',794,845)]},
 {'id':'E04','fact':'Each default-driver Open installs stored UDFs; createFunctionInternal forwards eTextRep unchanged to SQLite. Connection hooks execute later and expose no supported private db/tls/registration-flags API.', 'refs':[loc(DEP/'driver.go',287,315),loc(DEP/'conn.go',1075,1119),loc(DEP/'sqlite.go',694,717)]},
 {'id':'E05','fact':'Engine supports INNOCUOUS, extracts it, flips same bit into internal UNSAFE when absent; Windows DDL expression guard rejects unsafe function with trusted_schema OFF.', 'refs':[loc(DEP/'lib/sqlite.go',3782,3782),loc(DEP/'lib/sqlite_windows.go',71151,71162),loc(DEP/'lib/sqlite_windows.go',74658,74663),loc(DEP/'lib/sqlite_g_0000000000060000.go',108277,108291)]},
 {'id':'E06','fact':'Latest F08 SQLTEXT proof UDF is inside f08_sources CASE and BEFORE triggers. Even valid CASE input does not certify OFF usability because schema expression safety is checked at preparation. Registration is still proposed; no current Main F08 implementation.', 'refs':[loc(F08/'snapshots/author-fd227/candidate.sql.txt',351,364),loc(contracts/'source-contract.md',79,87),loc(contracts/'closed-contract.md',90,106)]},
 {'id':'E07','fact':'Current approved design permits OFF fail-closed refusal and explicitly forbids silently enabling trusted_schema. A goal of successful OFF operation requires a reviewed contract/dependency amendment, not a claim that existing guard execution passed.', 'refs':[loc(contracts/'source-contract.md',85,87),{'ref':ref(REVIEW/'mandatory_implementation_conditions.json'),'locator':{'json_pointer':'/8'}}]},
]
evref=write('source-evidence.json',{'evidence':evidence})
snippets=[]
for row in evidence:
    for entry in row['refs']:
        l=entry['locator']
        if 'line_start' in l:
            p=pathlib.Path(entry['ref']['path']); lines=raws[str(p)].decode('utf-8').splitlines()
            snippets.append({'evidence_id':row['id'],**entry,'lines':[{'line':n,'text':lines[n-1]} for n in range(l['line_start'],min(l['line_end'],len(lines))+1)]})
write('line-excerpts.json',{'snippets':snippets})
errors=raws[str(UDF/'read-errors-and-prior-outer-exit.json')]
with (OUT/'historical-errors.original.json').open('xb') as f:f.write(errors)
historicalref=ref(OUT/'historical-errors.original.json',errors)
patch={
 'status':'CANDIDATE_ONLY_NO_IMPLEMENTATION_AUTHORITY',
 'minimal_code_change':[{'actual_source_path':str(DEP/'sqlite.go'),'functions':['FunctionImpl','(*Driver).registerFunction'],
   'change':'Add explicit opt-in Innocuous bool (zero=false); only if opted in OR sqlite3.SQLITE_INNOCUOUS into textrep. Keep existing convenience wrappers and all old defaults unchanged. Do not globally mark all deterministic UDFs innocuous.'},
  {'proposed_domain_path':'internal/domain/client_cancel_finalization.go','exists_current_main':False,
   'functions':['proposed package init / private registerClientCancelFunctions helper'],
   'change':'After auditing each frozen pure callback, register exactly the three approved names through RegisterFunction(FunctionImpl{Deterministic:true, Innocuous:true,...}) before ANY default-driver Open. Fixed arities 2/5/2, existing failure-before-main behavior. No clock/DB/FS/env/network/Host state or retained args.'}],
 'driver_test_location':{'actual_source_path':str(DEP/'func_test.go'),'existing_entry':'TestRegisteredFunctions at line296','proposal':'Append separate explicit innocuous-flag tests; protect all old cases.'},
 'domain_test_candidate':'internal/domain/client_cancel_finalization_test.go (future proposed F08 file, not existing or authorized)',
 'dependency_delivery_blocker':'Do not edit .local module cache. Root must authorize a reviewed pinned upstream/fork/vendor delivery with full immutable module file inventory and go.mod binding (go.sum only if resolution changes). A local controlled fork is possible but exact destination/lock files are NOT yet chosen or authorized; this is outside current21 scope.',
 'no_change_required_in':['generated SQLite engine','conn.go flag forwarding','internal/store/sqlite.go','DSN/trusted_schema defaults','old SQL1..23'],
 'unsupported_shortcuts':['PRAGMA trusted_schema=ON as workaround','SQLITE_DIRECTONLY (blocks required view/trigger use)',
  'reflection/unsafe/linkname private conn or tls access','dynamic late registration','blanket innocuous flag on all registered functions'],
 'scope_next_step':'Non-author review of dependency capability amendment + same F08 registration contract; Root grants exact source/lock/tests and isolated execution. Current21 design alone does not authorize dependency changes.',
 'api_answer':'Existing public Go driver API cannot express this bit. Low-level SQLite lib API can take it, but driver connection/TLS/Go callback trampolines are private; no supported safe application-level bridge was found.'}
patchref=write('minimum-patch-proposal.json',patch)
cases=[
 ('I01','TestSQLiteFunctionInnocuousFlags','Driver registry: plain/deterministic-only/explicit-innocuous records. Actual PRAGMA function_list flags: no accidental INNOCUOUS on old defaults; opted-in includes0x200000 plus existing0x800, UTF8 and arity unchanged.'),
 ('I02','TestSQLiteDeterministicOnlyUnsafeSchemaRefusal','Fresh own DB, trusted_schema=OFF: same deterministic-only pure function succeeds direct SELECT but actual view-read and trigger-write refuse unsafe function; state unchanged. Preserve original error/code, not generic expected-error pass.'),
 ('I03','TestSQLiteExplicitInnocuousViewAndTrigger','Same inputs/DB design, only innocuous opt-in changes: direct/view/trigger legal paths succeed with OFF still0; exact output and committed row verified.'),
 ('I04','TestF08RegisteredFunctionsExactAndPure','Actual proposed three names/arity2,5,2 installed at init, flags queried on pinned physical connection; valid and invalid frozen raw inputs tested without clock/DB/secret side effects.'),
 ('I05','TestF08TrustedSchemaOffProofView','Actual schema24 f08_sources valid storage returns full original34 source document under OFF; bad storage reaches exact mode9 F08_STORAGE_CLASS and preserves rows. Do not replace with a synthetic always-true callback.'),
 ('I06','TestF08TrustedSchemaOffProofTrigger','Actual admitted/final journal producer with complete valid original evidence succeeds; one raw/hash/identity mismatch refuses and whole caller transaction rolls back. OFF remains0 throughout.'),
 ('I07','TestF08OffRecursiveTriggersBoth','Repeat exact authorized F08 insertion/forged transition and REPLACE protection controls with recursive_triggers0 and1, FK1. No threshold or guard deletion.'),
 ('I08','TestF08UDFEveryPhysicalConnection','Default sqlite Open, second real physical connection held concurrently, closed/reopened connection and NewConnector all independently demonstrate exact flags/guard. Do not mistake DB handle reuse for a second physical connection.'),
 ('I09','TestF08MissingOrCustomDriverRefuses','Unregistered separately constructed driver/missing-UDF negative refuses before publication; ordinary old23 connection behavior remains unchanged, not silently populated by a connection hook.'),
 ('I10','TestF08RegistrationCollisionFailsBeforeMain','Isolated child process duplicate-name registration fails before business Open/main; actual exit/stderr/absence-of-business effects retained. No overwrite or retry.'),
 ('I11','TestF08OffStartupUpgradeBackupRestore','Future matching source23→24 public upgrade, fresh24 and second startup, public backup/restore validate original schemas/history under OFF with rollback/publication barriers intact. Requires full F08 implementation and separate execution authority.'),
 ('I12','TestF08OldDefaultAndFailureCompatibility','Existing default registration tests and actual old22/23 fixed programs retain behavior; mode9/invalid schema/errors stay refused. Driver API addition alone is not old-binary or migration evidence.')]
matrixref=write('future-finite-verification.json',{'status':'ALL_NOT_RUN','selector_groups':len(cases),
 'rows':[{'id':i,'proposed_selector':s,'required_causal_assertion':a,'status':'NOT_RUN'} for i,s,a in cases],
 'expanded_leaf_count':None,'requires_separate_root_finite_execution_grant':True,
 'required_evidence':['actual physical connection PRAGMA trusted_schema/FK/recursive settings and function_list flags',
 'fixed driver/fork+full compiler input+test executable hashes before/after',
 'actual callback error versus SQLite unsafe/missing-function error distinguished',
 'closed own DB snapshot and row deltas/rollback, raw stdoutstderr and actual exits',
 'no true callback qualification from a flags-only synthetic driver unit test']})
summary={
 'schema':'researchos.f08-innocuous-gap-readonly.v1','actor':'codex:/root/sources_parent_impl',
 'status':'READONLY_GAP_CONFIRMED_PATCH_PROPOSED_NOT_IMPLEMENTED',
 'conclusion':'Pinned Go wrapper cannot express SQLITE_INNOCUOUS, though the pinned SQLite engine supports it. F08 OFF success is unavailable through the currently proposed deterministic-only registration; existing refusal is fail-closed, not successful evaluator execution.',
 'checkpoint_observed':{'revision':cp['revision'],'head':cp['head'],'f08_state':cp['work_in_progress']['f08_type_boundary_state']},
 'current_main_F08_helper_exists':(ROOT/'internal/domain/client_cancel_finalization.go').exists(),
 'dependency_declared':'modernc.org/sqlite v1.60.1','pinned_engine_source_literal':'3.53.4',
 'actual_dependency_bytes_verified_against':ref(compiler_path),'no_module_checksum_verification_executed':True,
 'code_evidence_ref':evref,'minimum_patch_ref':patchref,'verification_ref':matrixref,
 'original_failure_receipt_ref':ref(UDF/'read-errors-and-prior-outer-exit.json'),
 'historical_bytes_copy_ref':historicalref,'historical_native_exit_not_reported':None,
 'historical_outer_values_preserved_without_native_inference':True,
 'this_task_SQLite_Go_product_SDK_model_calls':0,'this_task_source_canonical_writes':0,
 'new_failures':[],'source_acceptance':False,'formal_increment':0,
 'official_references':[{'url':'https://www.sqlite.org/c3ref/c_deterministic.html','sections':['SQLITE_INNOCUOUS','SQLITE_DETERMINISTIC','SQLITE_DIRECTONLY'],
 'paraphrase':'INNOCUOUS is distinct from deterministic and is required for schema use under trusted_schema OFF. Only audited side-effect-free callbacks should opt in.'},
 {'url':'https://www.sqlite.org/pragma.html#pragma_trusted_schema','purpose':'Official trusted_schema semantics; not an execution observation.'}],
 'browsed_HTTP_or_native_exit':None}
findref=write('findings.json',summary)
before_ref=write('inputs.before.json',{'files':READS})
after=[ref(pathlib.Path(r['path'])) for r in READS]
drift=[{'before':a,'after':b} for a,b in zip(READS,after) if a!=b]
after_ref=write('inputs.after.json',{'files':after,'drift':drift})
diagref=write('tool-diagnostics.json',{'actual_successful_outer_chunks':['961404','bee0b9','c27e5f','8e4afd','b0402a','5fef3f','06fa09','036ba0','cc61fe','1ce9b4','369cc1','da2500','6dec11','87cc0b','d93df0','7d322c','747a1a','95cc80','aa64c5'],
 'all_outer_exit':0,'native_fields_not_separately_observed':None,
 'Python_explicit_exit_bridge_chunks':['8e4afd','b0402a','06fa09','036ba0','1ce9b4','da2500','6dec11','87cc0b','747a1a','95cc80'],
 'Python_native_for_bridge_chunks':0,'separate_raw_stream_files':None,
 'original_tool_results':'Conversation chunks; large inventory output was truncated and is not claimed complete.',
 'new_nonzero_origins':[],'old_origins_never_retried_or_recounted':True,'counter_reset':False})
handoff=write('handoff.json',{'status':'READONLY_ANALYSIS_SEALED_STOPPED','actor':'codex:/root/sources_parent_impl',
 'findings_ref':findref,'source_evidence_ref':evref,'minimum_patch_ref':patchref,'matrix_ref':matrixref,
 'before_ref':before_ref,'after_ref':after_ref,'drift':drift,'tool_diagnostics_ref':diagref,
 'SQL_Go_native_product_execution':0,'source_canonical_index_writes':0,'source_acceptance':False,
 'formal_increment':0,'writer':'STOPPED','manifest_path':str(OUT/'manifest.json'),
 'at':datetime.now(timezone.utc).isoformat()})
entries=[ref(p) for p in sorted(OUT.iterdir(),key=lambda p:p.name) if p.is_file() and p.name!='manifest.json']
mf=write('manifest.json',{'schema':'researchos.readonly-analysis-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True,'handoff_included':True})
print(json.dumps({'handoff_ref':handoff,'manifest_ref':mf,'findings_ref':findref,'patch_ref':patchref,'drift':drift},ensure_ascii=False))
