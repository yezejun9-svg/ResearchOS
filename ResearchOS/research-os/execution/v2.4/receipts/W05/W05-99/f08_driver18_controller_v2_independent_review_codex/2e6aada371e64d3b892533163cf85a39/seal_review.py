from pathlib import Path
import hashlib
import json

OUT=Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def emit(name,value):
 p=OUT/name;p.write_bytes(json.dumps(value,ensure_ascii=False,indent=2).encode('utf-8')+b'\n');return ref(p)
def read(name):return json.loads((OUT/name).read_bytes())
review=read('source-review.json');before=read('inputs.before.json');after=read('inputs.after.json')
assert before==after
for r in before:assert ref(Path(r['path']))==r
assert review['verdict']=='REQUEST_CHANGES' and len(review['findings'])==1
native=read('review.native-observation.json');assert native['actual_native_exit']==0 and native['candidate_executed'] is False
emit('ownership.closed.json',{'schema':'researchos.independent-source-review.close.v1','actor':'codex:/root/f08_i17_binding_impl','author':'codex:/root/command_queue_impl','independent_non_author':True,'lease_id':OUT.name,'writer_status':'STOPPED_AFTER_SEAL','outside_namespace_writes':False})
author_controller=review['findings'][0]['source_ref']
handoff=emit('handoff.json',{
 'schema':'researchos.driver18.controller-v2.independent-review.handoff.v1',
 'actor':'codex:/root/f08_i17_binding_impl','reviewed_author':'codex:/root/command_queue_impl','independent_non_author':True,
 'writer_status':'STOPPED_AFTER_SEAL','verdict':'REQUEST_CHANGES',
 'reviewed_controller_ref':author_controller,
 'author_handoff_ref':next(r for r in before if r['path'].endswith('1f63ee1825f24a35b3e88759b5c24e6a\\handoff.json')),
 'author_manifest_ref':next(r for r in before if r['path'].endswith('1f63ee1825f24a35b3e88759b5c24e6a\\manifest.json')),
 'original_request_ref':next(r for r in before if r['path'].endswith('86a653e6772140f1b85f472613ef6d81\\handoff.json')),
 'review_ref':ref(OUT/'REVIEW.md'),'source_review_ref':ref(OUT/'source-review.json'),'deadline_evidence_ref':ref(OUT/'ast-deadline-evidence.json'),
 'inputs_before_ref':ref(OUT/'inputs.before.json'),'inputs_after_ref':ref(OUT/'inputs.after.json'),'input_count':len(before),'input_drift':[],
 'D18_C01':'STATICALLY_ADDRESSED_NOT_RUN','D18_I01':'REQUEST_CHANGES_FINAL_EVIDENCE_IO_AFTER_LAST_DEADLINE_CHECK',
 'critical_findings':[],'important_findings':review['findings'],
 'exact_transformations':8,'physical_unified_diff_hunks':5,'whole_forward_inverse_bytes_exact':True,
 'caps_I16_I18_I17_NULL_authority_launcher_unchanged':True,
 'actual_python_static_review_native_exit':native['actual_native_exit'],'candidate_helper_native_exit':None,
 'actual_controller_Go_SQL_helper_SDK_HTTP_model_calls':0,'mock_or_fake_target_PASS':False,
 'new_failure_origins':[],'old_counters_and_origins_modified':False,
 'I17_old_sealed_package_modified':False,'Main_canonical_author_package_modified':False,
 'source_acceptance':False,'formal_increment':0,'Root_execution_grant_issued':False,
 'tool_observations_ref':ref(OUT/'tool-observations.json'),
 'next_step':'Original author new namespace final post-IO deadline rejection, then fresh independent source review; no execution authorized here',
 'manifest':'manifest.json self-excluded; exact SHA/bytes emitted by actual terminal result',
 'seal_native_exit':None,'seal_exit_authority':'external actual terminal result only'})
members=[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json']
manifest=emit('manifest.json',{'schema':'researchos.whole-namespace-manifest.v1','root':str(OUT),'members':members,'file_count':len(members),'self_excluded':'manifest.json','total_bytes':sum(r['bytes'] for r in members)})
for r in members:assert ref(Path(r['path']))==r
print(json.dumps({'status':'STOPPED','verdict':'REQUEST_CHANGES','handoff':handoff,'manifest':manifest,'review':ref(OUT/'REVIEW.md'),'file_count':len(members)},ensure_ascii=False))
