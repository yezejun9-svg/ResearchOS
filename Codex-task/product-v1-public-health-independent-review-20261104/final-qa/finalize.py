from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((R/name).read_bytes())
def pin(name):
 p=R/name;return{'ref':name,'sha256':sha(p),'bytes':p.stat().st_size}
def save(name,v):
 p=R/name;assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
i=read('inputs.json');nd=read('no-drift.json');assert nd['C_author_and_live_exact2_match']
checks=[]
for phase in ['required-tests','independent-tests-02','ipc-syntax']:
 result=read(phase+'.result.json');assert result['exit_code']==0
 assert sha(R/(phase+'.stdout.raw'))==result['stdout_sha256'] and sha(R/(phase+'.stderr.raw'))==result['stderr_sha256']
 checks.append({'name':phase,**result,'result':pin(phase+'.result.json'),'command':pin(phase+'.command.json'),'stdout':pin(phase+'.stdout.raw'),'stderr':pin(phase+'.stderr.raw')})
assert checks[0]['tap_summary']['pass']==135 and checks[1]['tap_summary']['pass']==6
diagnostics=[]
for row in read('author/final/diagnostics.json')['events']:diagnostics.append({'origin_key':row['origin'],'source':'AUTHOR_DIAGNOSTICS_CARRYFORWARD_NOT_RECOUNTED',**row})
diagnostics.extend([
 {'origin_key':'public-health-review-flat-channel-prefix','classification':'INDEPENDENT_FIXTURE_CHANNEL_NAME_ERROR','first_exit_code':1,'raw_ref':'independent-tests.stdout.raw','affected_test':'independent real flat bridge reaches public health while adjacent Host route stays authenticated','failure':'Fixture lookup omitted actual ros: channel prefix; handler was undefined before intended assertions.','corrected_by':'fixture-correction.json','resolved_ref':'independent-tests-02.result.json','product_source_changed':False},
 {'origin_key':'public-health-review-preprobe-gate-assumption','classification':'INDEPENDENT_FIXTURE_EXPECTATION_ERROR','first_exit_code':1,'raw_ref':'independent-tests.stdout.raw','affected_test':'independent failed actual ensureCore health probe cannot be replaced by a synthetic ready body','failure':'Fixture wrongly assumed a failed preliminary probe removes valid discovery. Existing ensureCore DOWN_NO_LAUNCH retains valid discovery, so a later fixed GET may truthfully observe recovery. Corrected case asserts exact new read/no principal/no spawn and its actual ready result.','corrected_by':'fixture-correction.json','resolved_ref':'independent-tests-02.result.json','product_source_changed':False}
])
assert len({d['origin_key'] for d in diagnostics})==len(diagnostics)
report={'schema':'researchos.public-health.independent-source-review.v1','reviewer':'codex:/root/implementation_review','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_acceptance_increment':0,'pending_blockers':[],
 'source_scope_path':read('author/final/source-manifest.json')['scope_path'],'base_head':i['base_head'],'source_sha256':i['source_sha256'],'source_count':2,'production_count':1,'test_count':1,
 'manifest_sha256':i['source_manifest_sha256'],'source_manifest_sha256':i['source_manifest_sha256'],'freeze_sha256':i['freeze_sha256'],'summary_sha256':i['metadata_pins']['final/summary.json'],'author_diagnostics_sha256':i['metadata_pins']['final/diagnostics.json'],
 'manifest_ref':'author/final/source-manifest.json','freeze_ref':'author/final/FROZEN.json','inputs':pin('inputs.json'),'no_drift':pin('no-drift.json'),
 'independent_checks':checks,'counts':{'required_pass':135,'new_public_health_cases_within_required':77,'existing_UI_compatibility_cases_within_required':58,'independent_pass':6,'combined_distinct_final_pass_events':141,'final_fail':0,'final_skip':0,'syntax_is_not_test_acceptance':True},
 'source_review':{'only_production_delta_public_health_request_selection':True,'proof':'Replace new let req/public-health branch with original principal/request block; entire IPC source then equals frozen pre-change text after line-ending normalization. V2/authority tickets/write lifetimes/provider classification/remaining transport and principal behavior unchanged.','new_exception':'Only exact client status + method health, after existing ensureCore/discovery checks, with absent/null or own-key-empty plain/null-prototype body. Fixed GET /healthz, empty payload and headers. No caller URL, method, path, identity, token or authority adoption.','not_a_grant':'Public health remains observation only; no principal file fabrication, auth refresh fallback, writer/Harness/model permission grant.'},
 'independent_case_details':['Actual registered ros:statusHealth bridge succeeds with missing legacy store and strict actual health fields; neighboring ros:statusHost remains denied','Public exception does not call mutable legacy request producer; fixed request/empty headers remain literal','Valid discovered Host may be truthfully re-observed ready after failed preliminary probe; no spawn/principal and exact new public request','Non-health caller payload cannot opt provider/session/workspace/Host routes into public exemption','Unauthorized actual transport result remains unavailable and invokes no credential fallback or HTTP retry','Actual bridge transport rejection feeds actual Header monitor unavailable, without fake green or resource launch'],
 'resolved_context_issue':{'origin_key':'desktop-public-health-legacy-principal-precondition','status':'CLOSED_SOURCE_AND_PURE_ACTUAL_BRIDGE_RECHECK','prior_report_sha256':'581db6d53a2b160da5aba24fee362d69bd69c20f777242b16e57452ed3d4468c','prior_UI8_review_preserved':'9a774cb3c31ddf18509fb68e029d0bac0d2a2af8eaf8bd0a0cf7fe386195cda4','real_GUI_confirmation':'NOT_RUN_BY_REVIEWER_ROOT_NEXT_SCOPE_REQUIRED'},
 'diagnostic_events':diagnostics,'author_failed_raw_preserved':{'stdout':pin('author/checks-01/pure-tests.stdout.raw'),'stderr':pin('author/checks-01/pure-tests.stderr.raw'),'diagnostics':pin('author/final/diagnostics.json')},'reviewer_failed_raw_preserved':{'result':pin('independent-tests.result.json'),'stdout':pin('independent-tests.stdout.raw'),'stderr':pin('independent-tests.stderr.raw'),'correction':pin('fixture-correction.json')},
 'diagnostic_merge_policy':'Author four ENOENT test failures share one existing sparse-dependency origin; two readonly disconnects share one existing transport origin. Keep references/counts and do not recount prior2502. Two reviewer fixture errors are separately classified. No raw failure erased or counter reset.',
 'evidence_inputs':{'C_public_source_files':len(i['files']),'author_evidence_manifest_hash_checked':i['metadata_pins']['EVIDENCE_MANIFEST.json'],'author_evidence_files_hash_checked':i['author_evidence_files'],'no_full_repository_archive':True},
 'limits':['Frozen exact2 source/fixture approval only. No real GUI/Native/CLI/model/old DB/auth file or real HTTP socket executed in independent QA.','Actual fresh-profile Host badge/health after merge and rebuild must be observed by Root separately. Prior smoke health issue is not retroactively marked passed.','Healthy service observation does not establish Harness model/read-scope/cancel qualification or writer authority.','Source integration/protected history/counter updates remain Root responsibilities; reviewer only verified exact2 and C necessary inputs.'],
 'archive_file_list':'archive-file-list.json','evidence_manifest':'EVIDENCE-MANIFEST.json','pending_operations':[],'uncertain_outcomes':[],'counter_reset':False,'no_D_writes':True}
save('report.json',report)
files=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts and p.name not in ['archive-file-list.json','EVIDENCE-MANIFEST.json']:
  files.append({'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
save('EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-source-evidence.v1','root':str(R),'files':files,'formal_increment':0})
save('archive-file-list.json',[v['path'] for v in files]+['EVIDENCE-MANIFEST.json'])
print(json.dumps({'decision':report['decision'],'report':str(R/'report.json'),'report_sha256':sha(R/'report.json'),'archive_file_list_sha256':sha(R/'archive-file-list.json'),'manifest_sha256':sha(R/'EVIDENCE-MANIFEST.json'),'files':len(files),'formal_increment':0}))
