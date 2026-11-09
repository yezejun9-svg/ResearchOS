from pathlib import Path
import json,hashlib,re,datetime
M=Path('D:/作品集/ResearchOS/research-os'); B=M/'execution/v2.4/receipts/W05/W05-99'
I=B/'cancel_finalization_v5_startup_caller_revision_codex/4639ce79ec914062ad92c278533a128f'
N=B/'review_f08_v5_startup_caller_codex/f2a1d3715c774ffd8dba7ba434a8209d'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def ref(p,loc=None):
 d={'path':str(p),'sha256':h(p),'bytes':p.stat().st_size}
 if loc is not None:d['locator']=loc
 return d
def save(name,o):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(N/name)
assert h(I/'proposal.json')=='3f374c2e90a859f60495b06f3b0b4565068e50882e9fdad81649558c4dd62fe5'
assert h(I/'complete_scope21.json')=='4c6145ef1f136d1cbd6977fbeb33f93919fff5347e49a71ac5c302f005712216'
manifest=read(I/'manifest.json');mismatches=[]
for r in manifest['files']:
 p=I/r['path']
 if not p.is_file() or h(p)!=r['sha256'] or p.stat().st_size!=r['bytes']:mismatches.append(r)
assert not mismatches
scope=read(I/'complete_scope21.json');old=read(I/'snapshots/author-fd227/scope_revision.json')
assert old['scope']==scope['original20_unchanged']
assert [{k:v for k,v in x.items() if k!='ordinal'} for x in scope['complete21'][:20]]==old['scope']
assert scope['complete21'][20]['path']=='internal/domain/store.go'
sql=I/'snapshots/author-fd227/candidate.sql.txt';assert h(sql)=='e3d58e53a76d00cfecb5cf139320f09055c0996c88616e288a49cfdd2ca07736'
text=sql.read_text(encoding='utf-8');counts={k:len(re.findall(r'CREATE\s+'+k+r'\b',text,re.I)) for k in ['TABLE','VIEW','TRIGGER']}
assert counts=={'TABLE':9,'VIEW':3,'TRIGGER':90}
inputs=read(N/'inputs.before.json');source=[]
for rel in ['internal/domain/store.go','internal/domain/client_session_fence.go','internal/store/sqlite.go','internal/domain/backup_migration.go','internal/domain/backup_upgrade.go']:
 p=M/rel;source.append(ref(p));dst=N/(rel.replace('/','__')+'.readonly.txt');dst.write_bytes(p.read_bytes())
save('public_source.before.json',source)
actual=M/'internal/domain/store.go'
assert h(actual)=='fa22f121b7f99f11094c1c68cbd961f146d3aee0ce73a356b5fce84216799a2c'
save('scope_comparison.json',{'original20_structurally_exact':True,'additional_path':'internal/domain/store.go','complete_count':21,'sqltext_ref':ref(sql),'sqltext_unchanged':True,'ddl_text_counts':counts,'category_count':34,'columns':281,'inline_before_gates':14,'manifest_entries_verified':len(manifest['files']),'manifest_mismatches':mismatches,'prior_review_ref':ref(I/'snapshots/review/review.v2.json'),'prior_whole_contract_ref':ref(I/'snapshots/review/whole_contract_review.v2.json'),'prior_static_audit_ref':ref(I/'snapshots/review/static_sql_audit.json'),'status':'STATIC_BYTE_AND_SCOPE_COMPARISON_NOT_ENGINE_EXECUTION'})
conditions=[
 {'id':'S01','topic':'Exact two New insertion spans','required':'Existing installed24 pre-DDL helper immediately after successful Begin/defer Rollback before numbered loop. Full34 helper after installClientSessionFence(false) succeeds and before original Commit. Same caller Tx only; errors return no Service and Rollback. NewCurrentMu policy unchanged.','evidence':ref(actual,{'line_start':52,'line_end':120})},
 {'id':'S02','topic':'Version branch is actual inventory','required':'Enumerate real schema_migrations version+stored typeof contiguity in same Tx. Old own22/23 returns without F08 queries. Already24 missing objects is corruption, never inferred legacy. Future/gapped/invalid inventory refused. Existing pre-Begin checkMigrationInventory+CheckMigrationSafety stay independent.','evidence':ref(actual,{'line_start':64,'line_end':101})},
 {'id':'S03','topic':'Prevent silent protector recreation','required':'Pre24 branch does not interfere with legitimate old additive/fence install. Already24 checks expected complete protector metadata before IF NOT EXISTS can heal missing old/F08 triggers/table/view. No DDL repair in validator.','evidence':ref(M/'internal/domain/client_session_fence.go',{'line_start':25,'line_end':74})},
 {'id':'S04','topic':'Freeze actual installed fingerprint before source freeze','required':'Qualify pinned-engine fresh24 and matching public23→24 installations. Record exact sqlite_schema tuples including SQL NULL handling and all relevant table/index/trigger/view constraints. If legitimate install histories produce different stored SQL text, freeze only explicitly reviewed exact release variants with producer evidence, not whitespace/name/count relaxation or untrusted current-DB generated expectations. No scope rejection merely because future literal is currently NOT_RUN.','evidence':ref(I/'startup-contract.md')},
 {'id':'S05','topic':'Fixed sqlite_% exclusion meaning','required':'Document exact engine-internal exclusion roster; schema-internal autoindexes must not let PK/UNIQUE constraints escape table-SQL comparison. The draft mentions autoindex sql=NULL as well as sqlite_% exclusion: implement one explicit reproducible policy and independently compare legitimate indexes/constraints. This is a precision condition, not an additional caller gap.','evidence':ref(I/'startup-contract.md')},
 {'id':'S06','topic':'Main source and temp shadowing','required':'Actual readers qualify main schema and inspect protected-name temp shadows. Do not rewrite original frozen34 tuple SELECT block. Validate schema before trusting f08 views. Fixed schema-version before/after collection and every Scan/rows.Err must propagate. Missing view/table/category is not empty source.','evidence':ref(sql,{'line_start':316,'line_end':360})},
 {'id':'S07','topic':'Full34 storage and semantics','required':'After additive/fence, consume actual type violation view and guarded complete source snapshot. Preserve all281 nullable/type rules, actual idempotency TEXT/BLOB positives, integer affinity facts, domain_refs bag and original target version proofs. Existing fourteen first-statement NEW/OLD gates unchanged; no catch-as-empty or type-cast loss hiding violations.','evidence':ref(I/'snapshots/review/static_sql_audit.json')},
 {'id':'S08','topic':'Mode9 remains error only','required':'Mode9 fixed arity/input produces unconditional F08_STORAGE_CLASS error; valid reads do not invoke it deliberately as success. No new callback/mode/ready bit or DB reads inside pure callbacks. Prior three pure callbacks remain complete evaluator authority.','evidence':ref(sql,{'line_start':351,'line_end':360})},
 {'id':'S09','topic':'Physical connection settings','required':'Read actual same physical Tx FK=1 and record recursive_triggers/trusted_schema; recursive0 and1 remain valid branches. Do not silently enable trusted_schema, change DSN/defaults or add store.Open registration hook. Missing/unsafe UDF actual failure is refusal, not evaluator success. Default-driver every physical reopen/direct-memory/new pool must independently prove registration/guards in future V11.','evidence':ref(M/'internal/store/sqlite.go',{'line_start':15,'line_end':70})},
 {'id':'S10','topic':'History-aware inventory','required':'Use shared history validator for original identity/private header/control/groups/pins/origins/legacy/final_commit. Do not rerun admission proof against later current heads; final original versions and restore-current fences differ. All prior UNKNOWN/effects/reserves/cost histories retained and lawful later confirmation permitted. No startup witness/birth/observation/qualification/reservation-release created.','evidence':ref(I/'startup-contract.md')},
 {'id':'S11','topic':'Public upgrade distinct from startup','required':'Exact matching23 public backup→isolated target migration→additive/fence→same full gate→publication while original source writer lock held. Keep private upgradeLocal leading plan branch only, unchanged exported verifier. Do not call domain.New to mutate user source. Earlier WAL/header writes are not covered by transaction DDL rollback and must be separately reported.','evidence':ref(I/'complete_scope21.json',{'json_pointer':'/additional_responsibilities_within_original20'})},
 {'id':'S12','topic':'Mandatory execution and protection limits','required':'Original12+R1six+R2fourteen+Neight=40 groups plus twelve startup subcontrols all remain NOT_RUN. No 21-path scope label promotes source/runtime acceptance. Actual rollback/protector-removal/different connection/oldwriter/current handler38 composed controls are required before source acceptance; no outside-SQL tamperproof claim.','evidence':ref(I/'startup_subcontrols.json')}
]
save('mandatory_implementation_conditions.json',conditions)
flows=[
 {'id':'FRESH24','producer':'actual domain.New against target24 release after store.Bootstrap','order':['preexisting migration inventory+safety','Begin/defer Rollback','prehelper actual inventory≤23 no F08 query','numbered 2..24 with SQL24 numbered-only type preflight/DDL/cohort','next_v24_sessions additive','installClientSessionFence(false)','posthelper full fingerprint+all34 types+history','original Commit'],'future_evidence':['N05-S01','N05-S02'],'result':'DESIGN_CALLER_CLOSED_EXECUTION_NOT_RUN'},
 {'id':'REPEAT24','producer':'domain.New already24','order':['prechecks','same Tx prehelper exact original metadata','unchanged additive/fence','posthelper all34 and original history','Commit'],'future_evidence':['N05-S03','N05-S04','N05-S05','N05-S07'],'result':'missing/replaced protector rejected before repair; no source-backed result yet'},
 {'id':'OLD_OWN22_23','producer':'matching old release inputs/old programs','order':['existing own inventory+safety','new source validator if reached branches actual<=23 no F08 read','old numbered/additive/fence path unchanged'],'future_evidence':['N05-S06','N06'],'result':'preserve actual matching old program behavior; no new24 helper test executable substituted for old binary'},
 {'id':'POPULATED23_WITH24','producer':'ordinary domain.New with current target24 files','order':['existing CheckMigrationSafety rejects missing migration with data'],'future_evidence':['N05-S06','V12'],'result':'MIGRATION_PREBACKUP_REQUIRED; no live inplace bypass'},
 {'id':'PUBLIC23_TO24','producer':'private upgradeLocal selected new exact Cancel plan','order':['source validation+public source23 backup+exclusive writer lock','isolated matching target migration/additive/fence','shared post gate and original upgrade verifier','publication with lock','future target New gets repeat24 gate'],'future_evidence':['V12-S01','V12-S02'],'result':'different producer timing; new caller cannot replace protected public staged-upgrade checks'}]
save('caller_flow_review.json',flows)
path_review=[]
for x in scope['complete21']:
 path_review.append({'path':x['path'],'bounds':x['bounds'],'verdict':'EXACT_NEW_CALLER_SUFFICIENT_WITH_S01_S12' if x['ordinal']==21 else 'PRIOR_REVIEW_BOUND_UNCHANGED','not_source_acceptance':True})
save('whole21_path_review.json',path_review)
matrix=read(I/'future-matrix.original40.json')
ids=[x['id'] for x in matrix['retains_all_original12_groups']['groups']]+[x['id'] for x in matrix['additional_cases']]+[x['id'] for x in matrix['reviewer_added_controls']]
assert len(ids)==40 and len(set(ids))==40
subs=read(I/'startup_subcontrols.json');assert len(subs['cases'])==12
save('future_controls_review.json',{'status':'ALL_NOT_RUN','original40_ids':ids,'subcontrols':subs['cases'],'subcontrols_do_not_add_or_replace_original_groups':True,'source_implementation_ready':False,'engine_behavior_verified':False})
notes=[{'id':'LOCATOR-01','severity':'NONBLOCKING_LOCATOR_CORRECTION','fact':'store.New.proposed-diff text says New53/Begin74/defer78. Exact same captured current file has funcNew52/Begin72/defer76; fence114–116 and Commit117 remain correct. Function/statement anchors unambiguous; use actual source hash+function anchors. No source or native failure.','evidence':ref(actual,{'line_start':52,'line_end':78})},
 {'id':'HISTORY-BOUNDARY','severity':'EXPLICIT_LIMIT','fact':'Whole20 earlier TYPE/R1/R2/DDL review is retained by exact byte hashes, not rerun SQL or product tests. New source acceptance will require all21 and actual current handler composition; this review does not sign the reviewer-authored handler38.'}]
save('findings.json',notes)
save('tool_diagnostics.json',{'known_outer_exit_zero':['bc4529','4cdd82','9eddd1','033760','515ba4'],'known_outer_nonzero':[],'native_failure_origin_delta':0,'truncations':['bc4529 discovery','9eddd1 combined read'],'followup':'focused033760/515ba4 and complete locally read static JSON/hash used; no truncated-output full-read assertion','executed':{'SQL':0,'Go':0,'Node':0,'tests':0,'HTTP':0,'models':0,'source_writes':0,'canonical_writes':0}})
after=[ref(Path(x['path'])) for x in inputs];changed=[x['path'] for x,y in zip(inputs,after) if x['sha256']!=y['sha256']];assert not changed
source_after=[ref(Path(x['path'])) for x in source];assert source==source_after
save('inputs.after.json',after);save('public_source.after.json',source_after)
save('hashguard.json',{'input_files':len(inputs),'input_drift':changed,'live_public_source_count':len(source),'live_source_drift':0,'manifest_verified':len(manifest['files']),'manifest_errors':mismatches,'scope_old20_equal':True,'SQLTEXT_equal':True,'no_compiler_closure_claim':True})
review={'schema':'researchos.f08.startup-caller-scope-review.v1','reviewer':'codex:/root/sources_parent_impl','author':'codex:/root/command_queue_impl','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'SOURCE_SCOPE_READY_WITH_MANDATORY_IMPLEMENTATION_CONDITIONS','scope_count':21,'source_categories':34,'review_type':'NONAUTHOR_READONLY_SCOPE_DESIGN_NOT_SOURCE_ACCEPTANCE','resolves_prior':'STARTUP-01 missing post-additive sameTx caller at prior6379 v2; now exact domain/store.go two spans and shared helper scope supplied','proposal_ref':ref(I/'proposal.json'),'scope_ref':ref(I/'complete_scope21.json'),'contract_ref':ref(I/'startup-contract.md'),'conditions_ref':ref(N/'mandatory_implementation_conditions.json'),'findings_ref':ref(N/'findings.json'),'whole21_ref':ref(N/'whole21_path_review.json'),'flow_ref':ref(N/'caller_flow_review.json'),'future_controls_ref':ref(N/'future_controls_review.json'),'hashguard_ref':ref(N/'hashguard.json'),'SQL24_edit_lease':False,'source_ready':False,'formal_acceptance_increment':0,'conclusion':'No remaining concrete caller-path omission found. Expected installed fingerprint generation and actual engine behavior are mandatory implementation verification, not evidence already obtained or a reason to reject an otherwise sufficient exact21 scope.'}
save('scope_review.json',review)
save('handoff.json',{'verdict':review['verdict'],'scope_review_ref':ref(N/'scope_review.json'),'conditions_ref':ref(N/'mandatory_implementation_conditions.json'),'source_ready':False,'execution_count':0,'new_native_failures':0,'next':'Root may decide/register exact21 lease after this conditional scope review; author must execute original40 and startup subcontrols before nonauthor source acceptance. No SQL/source writes currently authorised by this receipt.'})
files=[ref(p) for p in sorted(N.rglob('*')) if p.is_file() and p.name!='manifest.json']
save('manifest.json',{'files':files,'listed_count':len(files),'self_excluded':True})
print(json.dumps({k:ref(N/k) for k in ['scope_review.json','mandatory_implementation_conditions.json','handoff.json','manifest.json']},ensure_ascii=False))
