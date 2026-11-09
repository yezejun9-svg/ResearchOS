"""Metadata seal only: hashes/text/JSON, no target imports or execution."""
from pathlib import Path
import ast, difflib, hashlib, json, re
HERE=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
    b=p.read_bytes();return {'path':p.as_posix(),'sha256':sha(b),'bytes':len(b)}
def doc(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,value):
    p=HERE/name;b=value if isinstance(value,bytes) else value.encode('utf-8')
    with p.open('xb') as f:f.write(b)
    return ref(p)
def dump(name,value):return write(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')

baseTests=(HERE/'snapshots/048-client_cancel_finalization_test.go.proposed.txt').read_text(encoding='utf-8')
testText=(HERE/'client_cancel_finalization_test.go.proposed.txt').read_text(encoding='utf-8')+'\n'+(HERE/'materialization-controls_test.go.proposed.txt').read_text(encoding='utf-8')
testsRef=write('client_cancel_finalization_test.v2.go.proposed.txt',testText)
write('client_cancel_finalization_test.v2.delta.patch',''.join(difflib.unified_diff(baseTests.splitlines(True),testText.splitlines(True),fromfile='previous-6ed/client_cancel_finalization_test.go.proposed.txt',tofile='proposed/internal/domain/client_cancel_finalization_test.go')))
source=(HERE/'client_cancel_finalization.go.proposed.txt').read_text(encoding='utf-8')
sourceRef=ref(HERE/'client_cancel_finalization.go.proposed.txt')
patch=''.join(difflib.unified_diff([],source.splitlines(True),fromfile='/dev/null',tofile='b/internal/domain/client_cancel_finalization.go'))
patch+=''.join(difflib.unified_diff([],testText.splitlines(True),fromfile='/dev/null',tofile='b/internal/domain/client_cancel_finalization_test.go'))
patchRef=write('domain-new-files.proposed.patch',patch)

oldMF=doc(HERE/'snapshots/046-manifest.json')
dependencyRefs=[]
for name in ['modernc-sqlite-innocuous.patch','dependency-patch-contract.json','dependency-callgraph.json','function_innocuous_test.go.proposed.txt']:
    matches=[x for x in oldMF['files'] if Path(x['path']).name==name]
    assert len(matches)==1,(name,'actual prior manifest member required')
    original=matches[0];p=Path(original['path']);b=p.read_bytes();assert sha(b)==original['sha256'] and len(b)==original['bytes']
    copyRef=write('inherited-'+name,b)
    dependencyRefs.append({'original':original,'copy':copyRef})
dump('inherited-dependency-refs.json',dependencyRefs)

roster=doc(HERE/'future-pure-selectors.json')
roster['new_top_selectors'].append('TestF08ProofMaterializationExactParent')
roster['new_expanded_leaf_selectors']+=['TestF08ProofMaterializationExactParent/'+x for x in ['exact_parent_member','wrong_index','wrong_original_task','missing_parent']]
roster['new_expanded_leaf_selectors'].sort();roster['new_expanded_leaf_count']=len(roster['new_expanded_leaf_selectors']);roster['source_ref']=testsRef
roster['limits']='33 new component leaves, 8 new top selectors; prior12 top proposals retained. All NOT_RUN. No top-level result is counted as a leaf.'
rosterRef=dump('future-pure-selectors.v2.json',roster)

rows=[]
def mode(n,action,input_category,implemented,open_items,functions):
    rows.append({'mode':n,'action_literals':action,'input':'strict {action,row,old,sources}; actual tuple '+input_category,'success_output':'canonical JSON TEXT' if n==8 else 'int64(1)','source_implemented':implemented,'open':open_items,'functions':functions,'execution':'NOT_COMPILED_NOT_RUN','mode_complete':False})
mode(0,['admitted.insert'],'admitted','NO_RUN original request/global identity/current Session/target/all-member closure',['native and genuine legacy admission; full runtime binding/origin ancestry'],['admitted','groupRequest','noRun','queueAdmission','referenceClosure'])
mode(1,['final.insert'],'final','NO_EXECUTION with no Session or genuine empty original/new fence; final Task/Event/snapshot binding/pins',['nonempty queue/native effects and observations/SDK receipts; historical replay'],['finalGroup','emptyQueueFinal','eventClaim','f08Pending'])
mode(2,['origin.insert'],'origins','Initial qualification origin recomputation versus actual dispatch, immutable birth/plan/marker/profile',['ordinary admission; complete profile predicates; later/historical origins'],['originInsert','deriveInitialOrigin','originalBirth','bootstrapAdmission'])
mode(3,[],'UNBOUND','explicit fixed refusal; no guessed action',['actual mode3 backup/upgrade caller and authenticated source23 inventory contract'],[])
mode(4,['dispatch.update'],'dispatches OLD/NEW','actual OLD equality; monotone launch/identity/unknown/observed fields',['physical SQL deferred observation obligation and whole native proof independent replay'],['dispatchUpdate','dispatchManifest','f08BoundIdentity'])
mode(5,['journal.insert','journal.update','commit.insert'],'idempotency or commits','full original private header/Q/identity/schema; raw sole-journal ACK/COMPLETED closure for implemented final subset',['native final subset and historical validation; actual SQL deferred transaction integration'],['journalEnvelope','journal','completedJournal','finalResponse'])
mode(6,['control.insert','control.update'],'controls OLD/NEW','new original membership; actual state/bytes preservation; legacy REQUESTED->RECONCILING without backfill; subset final staging',['native final closure; actual producer ordering integration'],['control','finalGroup'])
mode(7,['admitted_member.insert','final_member.insert','pin.insert'],'actual child/pin tuples','exact parent doc member index/task/hash/pin and actual version; complete materializations at closure',['SQL AFTER trigger execution, indirect writes/collisions and all guard controls'],['materialization','completeMaterializations'])
mode(8,['origin.derive'],'dispatches','canonical initial qualification origin; later immediate-version/route/carry components fail closed at known gaps',['ordinary qualification/full prior epochs/native/budget/dependencies; real operation field not retained'],['deriveInitialOrigin','laterParts','effectHistories','f08EffectPrefix'])
matrixRef=dump('mode-coverage.json',{'schema':'researchos.f08-proposed-evaluator-coverage.v1','source_ref':sourceRef,'rows':rows,'complete_modes_0_through_8':False,'no_new_sql_action_or_tuple':True,'source_authority_boundary':'SQL fixed source view + original preserved authenticated Go producer + immutable triggers; a supplied unit-test bundle has no standalone authority','helper_only':['effectHistories','f08EffectRows','f08EffectPrefix','laterParts (no later origin success)']})

future=[
('TestF08ActualNoRunAtomicFinalJournal','real Decode/Execute CANCEL original Goal/Task/Session; original header, real Task event, actual final snapshot; closed raw DB and exact journal bytes'),
('TestF08ActualMultiTaskOriginalMembership','Goal with original multi-Task set and different noSession/realSession/fence branches; no later invented membership'),
('TestF08ActualQueueOriginalReceiptChain','preSDK CANCEL_FENCE and delivered command.cleared/consumed chains; exact generation/sequence/previous relation; one missing receipt refuses'),
('TestF08ActualInitialQualificationOrigin','real immutable Run birth not necessarily epoch1, TASK/RUN events/outbox/plan/marker/profile/permission; wrong exact anchor refused'),
('TestF08ActualOrdinaryOriginDependencyVector','original accepted dependency receipts/artifact use proofs with ordered vector; no current head substitution'),
('TestF08ActualLaterCheckpointResume','current Run R already written and immediate R-1, route/native_resume false/carry actualuse; no future RUN_CHANGED requirement'),
('TestF08ActualLaterResourceSwitch','actual replacement runtime and grant.admission operation, old/new exactrefs; never copy old runtime into new manifest'),
('TestF08ActualPriorUnknownReconciled','earlier UNKNOWN closed only by genuine later same effect sequence and cost; later epoch never clears unresolved exposure'),
('TestF08ActualNativeNeverLaunched','original selected PREPARED plus full prior epochs, no selected execution/upload/SDK contradictions except proven carry'),
('TestF08ActualStartedCleanupBeforeCompletion','authentic observation/artifact/owned native process+SDK clear/drop/abort/idle/fullcost; every removed gate refuses'),
('TestF08ActualHistoricalAppendAndBackup','retained original immutable proof and legal later effects/versions; closed backup/restore without current-head substitution'),
('TestF08PhysicalConnectionInnocuousOptIn','patched driver per-function flag only, trusted_schema OFF physical pooled connections and full SQL view/trigger callbacks'),
('TestF08Schema24UpgradeAndRollback','frozen original40 acceptance controls remain; source23 cohort/full inventory/staged upgrade/oldwriter/rollback/backup'),
]
dump('future-integration-gates.json',{'all_status':'NOT_IMPLEMENTED_OR_NOT_RUN','authorized_execution':False,'not_counted_as_component_pass':True,'cases':[{'selector':a,'required_causal_evidence':b,'status':'NOT_RUN'} for a,b in future],'frozen_original_controls':'Original contract/source_scope controls inherited by reference; this list does not replace or reduce them.'})

inputs=doc(HERE/'snapshot-map.json')+doc(HERE/'additional-inputs.before.json')+doc(HERE/'final-additional-inputs.before.json')
inputs+=dependencyRefs
after=[];drift=[]
for pair in inputs:
    before=pair['original'];now=ref(Path(before['path']));after.append(now)
    if now!=before:drift.append({'before':before,'after':now})
inputsRef=dump('public-inputs.after.json',{'input_count':len(inputs),'unique_paths':len({x['path'] for x in after}),'drift':drift,'files':after,'timing_note':'8 final-additional sources were first read before their recorded snapshot; no false pre-first-read proof'})

# Text-level symbol inventory only. No Go parser/formatter/compiler is invoked.
names=re.findall(r'(?m)^func\s+(?:\([^\n]*?\)\s*)?(\w+)\(',source)
duplicates=sorted({x for x in names if names.count(x)>1})
ast.parse((HERE/'assemble.py').read_text(encoding='utf-8'));ast.parse(Path(__file__).read_text(encoding='utf-8'))
diagnostics=dump('tool-diagnostics.json',{'kind':'KNOWN_FIELDS_FROM_VISIBLE_TOOL_RESULTS_NOT_RAW_NATIVE_STREAMS','target_calls':0,'metadata_assembly':{'initial_ast_chunk':'3b4530','actual_outer_exit':0,'actual_native_exit':None,'assembler_chunk':'61c972','actual_outer_assembler_exit':0,'actual_native_python_exit':0,'native_basis':'PowerShell explicitly exit $LASTEXITCODE'},'read_hash_chunk':'d2addf','read_hash_outer_exit':0,'read_hash_native_exit':None,'apply_patch_native_exit':None,'notes':['No product/Go/SQLite/SDK/model/HTTP execution','text private symbol closure is not compilation','parent owns all failure accounting; no reset or rewrite']})
auditRef=dump('static-source-audit.json',{'kind':'TEXT_ONLY_NOT_GO_AST_NOT_COMPILE','source_ref':sourceRef,'lines':len(source.splitlines()),'function_names_count':len(names),'duplicate_function_names':duplicates,'private_symbol_check_ref':ref(HERE/'static-text-check.json'),'source_fragments_complete_text':True,'full_evaluator_complete':False,'metadata_python_ast_parsed':True,'input_after_ref':inputsRef,'drift_count':len(drift),'old6ed_source_unmodified':ref(HERE/'snapshots/047-client_cancel_finalization.go.proposed.txt'),'root_or_worktree_source_writes':0})
origins=[ref(p) for p in sorted(HERE.glob('failure-origin.*.json'))]
handoff={'schema':'researchos.f08-evaluator-implementation-preparation-handoff.v1','actor':'codex:/root/sources_parent_impl','status':'PROPOSED_SOURCE_IMPLEMENTED_SUBSETS_FULL_EVALUATOR_OPEN_STOPPED','source_writer':'STOPPED','source_ref':sourceRef,'test_ref':testsRef,'new_file_patch_ref':patchRef,'mode_matrix_ref':matrixRef,'roster_ref':rosterRef,'status_document_ref':ref(HERE/'IMPLEMENTATION-STATUS.md'),'operation_patch_ref':ref(HERE/'runtime_admission.operation.proposed.patch'),'operation_scope_ref':ref(HERE/'operation-producer-scope.json'),'audit_ref':auditRef,'input_after_ref':inputsRef,'tool_diagnostics_ref':diagnostics,'origin_refs':origins,'registered_failure_count_changed':False,'source_ready':False,'complete_three_callbacks':False,'sql24_installation_permitted':False,'compiled':False,'go_sql_product_native_model_http_calls':0,'canonical_index_cache_worktree_writes':0,'new_component_top_count':8,'new_component_leaf_count':33,'actual_component_executions':0,'independent_review_required':['new single source and actual base diff','full pure transitive graph and no callback external effects','all OPEN branches and new operation producer change before any source lease','driver explicit opt-in/fork/pin and compiler/runtime tests separately authorized'],'limits':['This is source text preparation, not product acceptance.','No modes0..8 blanket success is claimed. Native/ordinary/history remain incomplete implementation work.','Historic metadata errors and original nativeNULL are preserved.']}
handoffRef=dump('handoff.json',handoff)
manifest=dump('manifest.json',{'schema':'researchos.readonly-manifest.v1','files':[ref(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='manifest.json'],'self_excluded':True})
print(json.dumps({'handoff':handoffRef,'manifest':manifest,'source':sourceRef,'tests':testsRef,'input_count':len(inputs),'drift_count':len(drift),'duplicates':duplicates},ensure_ascii=False))
