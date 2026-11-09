from pathlib import Path
import ast, hashlib, json, datetime
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
LAUNCH=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/root-g2-execute29-launch-r313'
REPLAY=ROOT/'execution/v2.4/receipts/W05/W05-99/provider_g2_independent_replay_codex/3ed3a3da52c3471d9ddc524897100842'
PREP=ROOT/'execution/v2.4/receipts/W05/W05-99/provider_g2_finite_replay_preparation_codex/3ed3a3da52c3471d9ddc524897100842'
RUNNER=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/complete-public-graph-and-g2-r310/g2_replay.v4.py'
READS=[]
def metadata(p,b):
    return {'path':p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):
    b=p.read_bytes(); READS.append(metadata(p,b)); return b
def save(name,obj):
    b=obj if isinstance(obj,bytes) else (json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with (OUT/name).open('xb') as f:f.write(b)
    return metadata(OUT/name,b)
def localref(p):return metadata(p,p.read_bytes())
sealraw=read(LAUNCH/'seal.py'); runnerraw=read(RUNNER); launchraw=read(LAUNCH/'launch.py')
for name,b in [('seal.original.py',sealraw),('runner.original.py',runnerraw),('launch.original.py',launchraw)]:
    ast.parse(b);save(name,b)
specraw=read(PREP/'execution_spec.json');spec=json.loads(specraw);save('spec.original.json',specraw)
grantraw=read(LAUNCH/'authorization.execute.json');grant=json.loads(grantraw);save('grant.original.json',grantraw)
preparedraw=read(REPLAY/'prepared.json');prepared=json.loads(preparedraw)
beforeraw=read(REPLAY/'execute/inputs.before-first.json');before=json.loads(beforeraw)
lookup={x['path'].casefold():x for x in before['observed']}
subset_missing=[x['path'] for x in prepared['inputs'] if lookup.get(x['path'].casefold())!=x]
facts={'spec_roster_count':len(spec['roster']),'spec_MODEL_expected_sum':sum(x['MODEL_calls'] for x in spec['roster']),'prepared_input_count':len(prepared['inputs']),'beforefirst_observed_count':len(before['observed']),'beforefirst_errors':before['errors'],'prepared_exact_subset_mismatches':subset_missing,'unique_beforefirst_paths':len(lookup)==len(before['observed']),'actual_prepared_sha_matches_grant':hashlib.sha256(preparedraw).hexdigest()==grant['prepared_sha256'],'actual_spec_sha_matches_grant':hashlib.sha256(specraw).hexdigest()==grant['spec_sha256'],'underlying_41958_files_rehashed':False,'sealer_AST_parsed_not_executed':True}
cases=[]
for row in spec['roster'][:6]:
    folder=REPLAY/'execute'/('%02d-'%row['index']+row['leaf'].replace('/','_'))
    rr=read(folder/'result.json');result=json.loads(rr);save('case-%02d-result.json'%row['index'],rr)
    ir=read(Path(result['process']['path']));inv=json.loads(ir);save('case-%02d-invocation.json'%row['index'],ir)
    ar=read(folder/'snapshot-audit.json');snap=json.loads(ar);save('case-%02d-snapshot-audit.json'%row['index'],ar)
    vectors=[]
    for name in ['all-inputs.before.json','all-inputs.after-native.json','all-inputs.after-fixtures.json']:
        b=read(folder/name);v=json.loads(b)
        vectors.append({'ref':metadata(folder/name,b),'keys':list(v),'observed_count':len(v['observed']),'errors':v['errors'],'equals_beforefirst':v['observed']==before['observed']})
    cleanup=inv['result']['job_cleanup']
    cases.append({'index':row['index'],'selector_matches':result['selector']==row['selector'],'actual_native_exit':inv['actual_exit'],'helper_error':inv['result']['error'],'timed_out':inv['result']['timed_out'],'cleanup':cleanup,'result_process_ref_matches':metadata(Path(result['process']['path']),ir)['sha256']==result['process']['sha256'],'MODEL_reported':result['MODEL'],'snapshot_audit_count':len(snap),'vectors':vectors})
facts['cases00_to05']=cases
facts['snapshots00_to05_total']=sum(x['snapshot_audit_count'] for x in cases)
facts['typed_snapshot_producer_structure']={'runner_lines':[287,310],'fields':['snapshot','method','source_original_file_retained','integrity','schema','tables','implicit_rowid_checked'],'schema_columns':['type','name','tbl_name','rootpage','sql'],'tables':'columns plus rows_multiset of {type,value}; blobs hex','observed_nonempty_snapshot_json_in_this_review':False,'SQLite_open_or_reaudit':False}
findings=[
 {'id':'S01','severity':'BLOCKER','title':'Failure collection aborts on the condition it must preserve','sealer_lines':[60,76,89,106,139],'cause':'Before failure_origin is saved, asserts require current exe/refs intact, beforefirst errors empty, all native0 helper error/timeout/cleanup successful and every result closure valid. A real input drift, native0 cleanup error or launcher error/NULL exit therefore causes a second unsealed exception.','change':'Separate best-effort original failure capture from success qualification. Keep actual outer/controller/native nullable values and helper fields; collect validation_errors and raw refs. Gate PASS on all checks, but always seal original failure and any sealer failure in a distinct immutable result. Do not coerce unsupported exit/NULL to 1 or 0.'},
 {'id':'S02','severity':'BLOCKER','title':'Failed attempted case incorrectly represented as later NOT_RUN; MODEL total can omit its calls','sealer_lines':[130,149,163,174],'runner_lines':[335,363,408],'cause':'runner.results is appended only after all post-fixture gates. failure.not_run is roster minus qualified results, so it includes an already attempted native case. MODEL sum in sealer uses qualified results only and misses HTTP calls in that attempted case.','change':'Derive separate QUALIFIED, ATTEMPTED_FAILED_OR_UNQUALIFIED, NEVER_STARTED partitions from exact roster, existing case/process records and argv. Preserve original not_run verbatim as runner_unqualified_roster, not later_NOT_RUN. Publish qualified_MODEL separately; failed-case observed records plus coverage/unknown establish total, otherwise actual_total=NULL with known lower bound. external_paid_calls_authorized=0 is distinct from observed0; no inferred actual_cost=0.'},
 {'id':'S03','severity':'REQUIRED','title':'Bind sealing inputs and success summary to frozen spec and exact case/process mapping','sealer_lines':[62,68,83,109,126,142],'cause':'Spec is loaded by hardcoded path but its bytes are not compared with grant.spec_sha256/prepared.spec. Success checks only final status strings and global counts; it does not compare final result.results/MODEL/snapshots with collected case records or bind each invocation argv/process folder uniquely to the roster.','change':'Verify spec actual bytes against grant and prepared pins, source/output/work/roster grant equality and runner SHA. Enforce unique ordered path identities in vectors and case-to-process bijection including exe/selector argv. Compare complete final aggregate to collected results and counts. Verify outer stdout/stderr pinned refs and keep wrapper_error separate.'}
]
facts_ref=save('actual-read-audit.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'facts':facts,'input_refs':READS,'readonly_tools_prior':['4520c9','301d69','deebfc','2a7c8f'],'new_product_executions':0,'new_failure_origins':[]})
prior=ROOT/'execution/v2.4/receipts/W05/W05-99/root_registration_r315_readonly_review_codex/9f2550ee1b144f9d91d48da291dff594'
failure_refs=[]
for name in ['failure_origin.json','failure_origin.eebbe6.json','failure_origin.77e582.json']:
    p=prior/name;b=read(p);v=json.loads(b)
    failure_refs.append({'absolute_path':str(p),'ref':metadata(p,b),'original_tool_ref':v['original_tool_ref'],'actual_outer_exit':v['actual_outer_exit'],'actual_native_exit':v['actual_native_exit'],'raw_hint':v.get('raw_limitation'),'original_raw_file':v.get('raw_file'),'count_once':True,'registration_cut':'future316, excluded315'})
review=save('review.json',{'schema':'researchos.g2-root-sealer-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES','reviewed_sealer_ref':metadata(LAUNCH/'seal.py',sealraw),'actual_sealer_executed':False,'actual_product_executed':False,'actual_read_audit_ref':facts_ref,'findings':findings,'positive_findings':['Success path requires29qualified native processes/4MODEL/13snapshots and three complete per-case vectors.','Actual case00..05 shapes match parser expectations; each three observed vectors matches frozen before-first.','Prepared41958 entries are an exact subset of41963 execution-vector entries in records; no underlying resource rehash performed.','VACUUM image/original bytes/implicit rowid limits and source/Main/formal false are stated.'],'bounds':['G2 still running; no complete29 conclusion.','No SQL, Go, Node, SDK, model, process polling or mutable output changes.','Nonempty typed snapshot JSON not yet independently observed in selected00..05; producer shape only.','No cost statement or public/paid qualification.'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'new_failure_origins':[]})
manifest=save('manifest.json',{'entries':[localref(p) for p in sorted(OUT.iterdir()) if p.is_file()],'self_excluded':True})
handoff=save('handoff.json',{'decision':'REQUEST_CHANGES','review_ref':review,'manifest_ref':manifest,'actual_sealer_executed':False,'cp315_three_pending_failure_origins':failure_refs,'new_failure_origins':[],'formal_increment':0})
print(json.dumps({'review':review,'manifest':manifest,'handoff':handoff},ensure_ascii=True))
