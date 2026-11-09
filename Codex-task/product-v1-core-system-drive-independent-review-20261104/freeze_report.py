from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parent;A=R.parent/'product-v1-core-system-drive-author-20261104'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,v):
 p=R/name;assert not p.exists(),str(p);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=json.loads((A/'final/source-manifest.json').read_text());assert sha(A/'final/source-manifest.json')=='0f0e0e6a0025a878927be99c00ba89c1fc067ae0f3e551f2e7ff66b7d7bb431e'
assert sha(A/'final/FROZEN.json')=='c5622e19aa93d9edc2e315aa36604f2e95dfe7ef3821dd50dda8d476bbc7abab'
for rel,pin in m['source_sha256'].items():assert sha(A/'final/source'/rel)==pin and sha(R/'attempt-02/snapshot'/rel)==pin
rel='apps/desktop/main/lib/desktop-management.js';old=(A/'source-write-01/before'/rel).read_bytes();new=(A/'final/source'/rel).read_bytes()
start=b'function managedControlEnvironment(ambient, options) {';end=b'\nfunction createDesktopManagement(options)'
assert old.split(start,1)[0]==new.split(start,1)[0] and old.split(end,1)[1]==new.split(end,1)[1]
assert hashlib.sha256(old).hexdigest()==m['baseline_sha256'][rel]
put('readback.json',{'source_sha256':m['source_sha256'],'no_drift':True,'entire_before_function_prefix_equal':True,'entire_after_function_suffix_equal':True,'prefix_sha256':hashlib.sha256(new.split(start,1)[0]).hexdigest(),'suffix_sha256':hashlib.sha256(new.split(end,1)[1]).hexdigest(),'core_cwd_native_identity_pipe_job_stop_unchanged':True})
r2=json.loads((R/'attempt-02/result.json').read_text());r3=json.loads((R/'attempt-03/result.json').read_text());assert r2['counts']=={'tests':36,'pass':35,'fail':1,'cancelled':0,'skipped':0};assert r3['exit_code']==0 and r3['counts']['pass']==2
raw=(R/'attempt-02/stdout.raw').read_text();assert len(re.findall(r'^not ok ',raw,re.M))==1 and 'not ok 2 - independent: conflicting WINDIR aliases' in raw
events=[json.loads((R/'attempt-01-failure.json').read_text()),{'origin_key':'core-system-drive-independent-js-path-escape','classification':'INDEPENDENT_FIXTURE_PATH_ESCAPE_ERROR','raw_tool_chunk':'398b9a','raw_ref':str(R/'attempt-02/stdout.raw'),'raw_sha256':sha(R/'attempt-02/stdout.raw'),'attempt_exit_code':1,'product_original_suite_pass':34,'detail':'Independent JS string used single backslashes; F:\\OS\\WINDOWS became a drive-relative string and was correctly rejected. Source unchanged. Only two corrected extra cases rerun, c80306 exit0/2PASS.','resolution_ref':str(R/'attempt-03/result.json')}]
put('report.json',{
 'schema':'researchos.independent-source-review.v1','decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_increment':0,'pending_blockers':[],
 'source_sha256':m['source_sha256'],'manifest_ref':str(A/'final/source-manifest.json'),'manifest_sha256':sha(A/'final/source-manifest.json'),'freeze_ref':str(A/'final/FROZEN.json'),'freeze_sha256':sha(A/'final/FROZEN.json'),'no_drift':True,
 'scope':'Core managed environment only: derive one SystemDrive from a required validated SystemRoot and matching optional WINDIR. Source admission only.',
 'findings':[
  {'ref':'apps/desktop/main/lib/desktop-management.js:795','result':'The fixed inherited-environment allowlist remains unchanged. All ambient SystemDrive case aliases are ignored; no credential, proxy, runtime override or synthetic home is newly forwarded.'},
  {'ref':'apps/desktop/main/lib/desktop-management.js:804','result':'Rejects missing/nonstring/relative/UNC/device/placeholder/control/traversal/extra-colon/bare-volume roots. Uses Windows path rules, validates normalized drive root, requires optional retained WINDIR to match case-insensitively, and derives uppercase drive only from SystemRoot.'},
  {'ref':'apps/desktop/main/lib/desktop-management.js:817','result':'Drive does not come from bundle, dataRoot or cwd. Owned data/web/listen overrides retain prior values.'},
  {'ref':'readback.json','result':'Original baseline hash verified. Entire code prefix before environment and suffix after environment are byte-identical, independently proving no changes to Core cwd/Native identity/pipe/Job/stop code in this slice.'}
 ],
 'independent_checks':{
  'method':'Exact frozen production function and actual failure helper extracted into a C-only CommonJS module requiring node:path. Frozen unit test copied byte-for-byte; no full management module startup/native import/child process code run.',
  'frozen_environment_suite':{'passed':34,'failed':0,'raw_ref':str(R/'attempt-02/stdout.raw'),'enclosing_process_exit_code':1,'enclosing_failure':'Only independent path-escape fixture below; not a frozen-source assertion failure.'},
  'extra_cases':{'passed':2,'failed':0,'exit_code':0,'ref':str(R/'attempt-03/result.json'),'raw_ref':str(R/'attempt-03/stdout.raw'),'raw_tool_chunk':'c80306'},
  'accepted_distinct_case_count':36,'no_skip':True,'node_sha256':'5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6','command_refs':[str(R/'attempt-02/command.json'),str(R/'attempt-03/command.json')]
 },
 'second_static_reader':{'agent':'prompt_flow_review','result':'No P1/P2. Fixed allowlist and 17-line environment-only diff; Native/cwd/pipe/Job unchanged. Validation is path-format and derivation, not actual directory existence or runtime proof.','runtime_or_test_execution':0},
 'author_checks_referenced_not_recounted':{'pure_cases':54,'exit_code':0,'ref':str(A/'final/summary.json'),'existing_management_smoke_cases':20,'independent_reexecution_of_old20':False},
 'qualification_limits':[
  'No GUI, Core, Native, model, user auth/config, old DB or cache DB was accessed or run by this review.',
  'SystemRoot remains a trusted platform input; syntactic validation does not authenticate the directory, inspect reparse points, or prove it exists.',
  'Core cwd remains its original repository/installed-resource basis. This slice is not Core filesystem/cwd isolation and does not change Go Harness child environment.',
  'Windows Shell cache artifact causality is an inference, not established by pure tests. A fresh independently validated bundle and new Root scope must prove actual runtime behavior.',
  'Old poisoned build05 assets, extras, manifest guard failure and original counters remain untouched. No guard relaxation or deletion was performed.'
 ],
 'diagnostic_events':events,
 'carryforward_only':{'ref':str(A/'final/diagnostics.json'),'rootcause_proposal_sha256':'1190a49389bede880d37d61fe3e3229134d58196d0db5dc6e582579023261cd2','count_again':False},
 'counter_reset':False,'pending_operations':[],'uncertain_outcomes':[]
})
files=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ['EVIDENCE-MANIFEST.json','archive-file-list.json']]
put('EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-review-evidence.v1','files':files})
put('archive-file-list.json',[row['path'] for row in files]+[str(R/'EVIDENCE-MANIFEST.json')])
print(json.dumps({name:sha(R/name) for name in ['report.json','EVIDENCE-MANIFEST.json','archive-file-list.json']}))
