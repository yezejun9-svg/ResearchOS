"""SYNTHETIC targeted state guard, with unrelated provenance checks mocked.
No real prepare/apply/recover/registered call. This is not a full PASS fixture.
"""
from pathlib import Path
import importlib.util,sys,json
from unittest.mock import patch
OUT=Path(__file__).resolve().parent;MAIN=OUT.parents[6]
SRC=MAIN/'.local/worktrees/codex-w0599-command-queue/execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/w04-transition-candidate-3d1d3c4e-2f7c-493d-b19d-40bd7147543e/register.py'
spec=importlib.util.spec_from_file_location('isolated_state_guard',SRC);r=importlib.util.module_from_spec(spec);sys.modules[spec.name]=r;exec(compile(SRC.read_bytes(),str(SRC),'exec'),r.__dict__)
root=OUT/'SYNTHETIC_REGISTERED_STATE';root.mkdir()
def put(name,value):
 p=root/name;r.save(p,value);return r.reference(root,p)
oldrow={'id':'W04-99','status':'ACCEPTED','evidence':[],'accepted_at':'2026-01-01T00:00:00+00:00'}
original=r.encoded({'steps':[oldrow]})
put(r.STATE,{'steps':[{**oldrow,'accepted_at':'2026-02-01T00:00:00+00:00'}]})
roots={k:put('synthetic/'+k+'.json',{'SYNTHETIC':True}) for k in r.SCHEMAS}
archive=put('synthetic/archive.json',{'schema':'researchos.w04.historical-acceptance-archive.v1','scope':'HISTORICAL_ONLY_NOT_CURRENT_ROOT','owner':oldrow,'roots':roots,'nonroots':[],'original_evidence':[]})
old={'owner':oldrow,'roots':roots,'nonroots':[]}
assignment={'executor_id':'synthetic:executor','reviewer_id':'synthetic:reviewer'}
run=put('synthetic/run.json',{'started_at':'2026-02-01T00:00:00+00:00'})
msg=put('synthetic/message.json',{'SYNTHETIC':True});registry=put(r.REGISTRY,{'revision':40})
new={'index':{'cases':{cid:{'run_receipt':run} for cid in r.CASES}},'issuance':{'message_ref':msg},'context':{'registry_snapshot_ref':registry}}
helper=root/'synthetic/register.py';r.exclusive(helper,SRC.read_bytes());r.exclusive(helper.with_name('test_register.py'),SRC.with_name('test_register.py').read_bytes())
template=r.template_for(old,roots,archive,assignment,'2026-02-01T00:00:00+00:00')
plan={'schema':'researchos.w04.explicit-applicability-transition-plan.v1','resolver':r.RESOLVER,'invariants':r.INVARIANTS,'scope_ref':{'sha256':r.SCOPE_SHA},'amendment_ref':r.AMENDMENT,'old_row':oldrow,'old_row_sha256':r.object_sha(oldrow),'old_roots':roots,'old_nonroots':[],'archive_ref':archive,'new_roots':roots,'stable_row':template,'stable_row_sha256':r.object_sha(template),'helper_ref':r.reference(root,helper),'tests_ref':r.reference(root,helper.with_name('test_register.py')),'source_review_ref':{},'source_review_message_ref':{},'collection_completion_ref':{},'external_compiled_input_hashes':{},'applicability_differences':[],'case_actual_message_ref':msg,'registry_snapshot_ref':registry,'input_hashes':{r.STATE:r.sha(original)},'registry_sha256':registry['sha256']}
with patch.object(r,'__file__',str(helper)),patch.object(r,'source_approval'),patch.object(r,'collection_completion'):
 try:r.verify_plan_current(r.Audit(root),plan,old,new,assignment,[])
 except r.Refusal as exc:
  if exc.code!='HASH_MISMATCH' or r.STATE not in str(exc):raise
  actual={'code':exc.code,'error':str(exc)}
 else:raise RuntimeError('expected actual postcommit old-state mismatch absent')
result={'classification':'SYNTHETIC_NOT_PRODUCT_TARGETED_GUARD','candidate_sha256':r.sha(SRC.read_bytes()),'actual':actual,'input':'Signed plan input_hashes legitimately includes preapply canonical state; current bytes are own committed state.','call_path':'verify_registered→verify_plan_current→audit.bytes(plan.input_hashes[STATE])','unrelated_checks_mocked':['source_approval','collection_completion'],'real_canonical_access':False,'proves':'Unconditional old-state input replay rejects completed state when STATE is enrolled; does not claim other provenance passed.'}
with (OUT/'registered_state_repro.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False))
