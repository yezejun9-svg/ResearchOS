import pathlib,json,hashlib
D=pathlib.Path(__file__).resolve().parent; R=D.parents[6]
def ref(p):
 b=p.read_bytes(); return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,v):
 with (D/n).open('x',encoding='utf-8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2); f.write('\n')
p=json.loads((D/'execution_plan.json').read_text(encoding='utf-8'))
p['previous_draft_ref']=ref(D/'execution_plan.json')
p['frozen_profile_proposal']['adapter_revision']='windows-appcontainer-v1'
p['frozen_profile_proposal']['timeout_seconds']=420
p['frozen_profile_proposal']['notes']='Same immutable P3/P4 profile. P3 permission forbids TOOL; a TOOL request fails qualification. Mu backend allows at most900s (runtime_dispatch.go:24-27); proposed420s covers <=4x90s provider deadlines plus bounded startup/tool processing. Previous draft incorrectly called300s the Mu limit; only non-Mu default is300s. This correction changes no source or execution.'
p['budget']['policy_requirements']+=' Goal-level cap is updated through updateGoalBudgetPolicy, not a nonexistent task budget policy. Before P4 start coordinator auto-scan is held until the actual newly returned Goal policy/Task context is current, or use already-approved project ancestor3.00 plus original max_calls4/per-call0.50; do not invalidate a READY ContextBundle by changing policy without legitimate revalidation. Exact admission must be reviewed before enabling scan.'
p['helper_design']['current_plan_only']='No standalone product ModelAdmission API found; no unverified .local helper symbol was invoked. Future helper interface and protected evidence projection are proposed scope, not implemented availability.'
put('execution_plan.final.json',p)
checks=[]
for v in json.loads((D/'source_before.json').read_text())['files']:
 a=ref(R/v['path']); checks.append({'path':v['path'],'before':v['sha256'],'after':a['sha256'],'equal':v['sha256']==a['sha256']})
put('source_final.json',{'checks':checks,'drift':[x for x in checks if not x['equal']]})
put('handoff.final.json',{'status':'PROPOSED_BLOCKED_BEFORE_LIVE','plan_ref':ref(D/'execution_plan.final.json'),'original_plan_ref':ref(D/'execution_plan.json'),'source_before_ref':ref(D/'source_before.json'),'source_final_ref':ref(D/'source_final.json'),'actual_reads_ref':ref(D/'actual_reads.json'),'public_files':len(checks),'source_drift':sum(not x['equal'] for x in checks),'network_or_model_calls':0,'vault_or_private_database_reads':0,'helper_compilation_or_host_start':0,'new_actual_T08_blocker':'signed-zero SDK Map SameValueZero index merging; separate authorized repair required','future_approval':'Independent plan reviewer and Root helper/execution scope; no formal acceptance claimed'})
put('manifest.final.json',{'files':[ref(f) for f in sorted(D.rglob('*')) if f.is_file()]})
print(json.dumps({'plan':ref(D/'execution_plan.final.json'),'handoff':ref(D/'handoff.final.json'),'manifest':ref(D/'manifest.final.json')},ensure_ascii=False))
