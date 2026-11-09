import sys
sys.dont_write_bytecode=True
import json,hashlib,datetime
from pathlib import Path
O=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os')
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(n,obj):
 with (O/n).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
final=read(O/'final-review.json');assert final['remaining_canonical_findings']==0
guards=[]
for p in O.rglob('*.json'):
 if p.name in ('canonical-short-sourceguard.close.json','sourceguard.close.json','correction.sourceguard.close.json') and 'originals' not in p.parts:
  g=read(p);assert g['closed'] and g['retained_handles_count']==0 and not g['errors'];guards.append(pin(p))
expected=read(O/'attempt2/canonical.closing-pins.json');observed=[pin(v['path']) for v in expected];assert expected==observed
save('canonical.final-short-pins.json',observed)
failure_refs=[pin(O/f'failure-origin.{n}.json') for n in (880,883,884)]
hdf={'schema':'researchos.independent-checkpoint-review-handoff.v1','decision':final['status'],'checkpoint_revision':362,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'current_target_actual_review','author_of_CP362':False,'canonical_refs':observed,'report_ref':pin(O/'report.md'),'final_review_ref':pin(O/'final-review.json'),'base_attempt_ref':pin(O/'attempt2/report.json'),'count_correction_ref':pin(O/'count-correction.report.json'),'input_refs_ref':pin(O/'attempt2/input-refs.json'),'sourceguard_close_refs':guards,'all_guards_closed':True,'old845_raw_record_bytes_and_semantics_preserved':True,'new_original_ordinals':list(range(848,876)),'registered_failures':873,'highest_observed_ordinal_at_cutoff':875,'next_failure_ordinal_at_cutoff':876,'new_review_failure_origins':failure_refs,'new_review_failures_registered_in_CP362':False,'remaining_canonical_findings':0,'T8_boundary_leaf_parent_terminal':[28,2,30],'T8_native868_failed_not_accepted':True,'T9_target_suite_failed_actual_limited_accepted':True,'T9_child_native_pid_exit':None,'BR4_pure17_at_cutoff':'NOT_RUN','formal_progress':'0/42','historical_parents':'6/22','original_paid_business':'OPEN_ONCE_CONSUMED_EXPIRED_PROVIDER_NULL','counter_reset':False,'authority':'CHECKPOINT_CONSISTENCY_ONLY','product_authority':'NONE','formal_acceptance':False,'Go_SQL_native_model_executed':False,'Main_canonical_Source_writes':False,'STOP':True,'manifest_exclusions':['MF.json','postseal.json','seal.original-tool-io.json']}
save('HDF.json',hdf)
excluded={'MF.json','postseal.json','seal.original-tool-io.json'}
members=[pin(p) for p in sorted(O.rglob('*')) if p.is_file() and not (p.parent==O and p.name in excluded)]
mf=save('MF.json',{'schema':'researchos.independent-evidence-manifest.v1','members':members,'excluded_root_seal_envelopes':sorted(excluded)})
for ref in members:assert pin(ref['path'])==ref
post=save('postseal.json',{'status':'PASS','manifest':mf,'handoff':pin(O/'HDF.json'),'verified_members':len(members),'exact_sha256_bytes':True,'all_review_guards_closed':True,'formal_acceptance':False,'excluded_self_and_tool_return':['postseal.json','seal.original-tool-io.json']})
print(json.dumps({'HDF':pin(O/'HDF.json'),'MF':mf,'postseal':post,'failure_origins':failure_refs,'status':hdf['decision']},ensure_ascii=False))
