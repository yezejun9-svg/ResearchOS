import ast,hashlib,json,sys,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'formal_profile_v4_adoption_source_root/adoptv4-20261009/v2'
V=W/'formal_profile_v4_adoption_independent_source_review_codex/adoptr2-01a12072'
P=W/'w09_formal_profile_v4_source_codex/profv4-01a12c10'
M=W/'main_c19_adoption_decision_supplement_codex/adoptsupp-01a11fea'
N=Path(__file__).resolve().parent
refs=[]
def require(v,c):
 if not v:raise AssertionError(c)
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
 require(type(r) is dict and set(r)=={'path','sha256','bytes'} and type(r['bytes']) is int,'EXACT_REF')
 p=Path(r['path']);require(p.is_absolute() and str(p.resolve(strict=True))==r['path'],'CANONICAL_PATH');b=p.read_bytes();require(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'EXACT_PIN '+str(p));return b
def fixed(p,s,n):
 r=dict(path=str(p.resolve(strict=True)),sha256=s,bytes=n);read(r);refs.append(r);return r
def load(r):refs.append(r);return json.loads(read(r))
def save(name,d):
 with (N/name).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
outref=fixed(S/'publication.outcome.activate.json','460723bb88ba1ac70642bae0b805f6dc274cd90063d8e066b5e128c7453329e2',2466);out=load(outref)
rootgr=fixed(S/'source-guard.cleanup.activate.json','08fad4c0c0be50e99343c119f20449920839febfc0e78a082dc0cda494b93fa9',38574);rootg=load(rootgr)
io_ref=pin(S/'publication.actual.original-tool-io.root.json');io=load(io_ref)
dr=fixed(V/'source-decision.json','eabe3d6b83f4cd272a6952904404d448fd1cfc33e6d98f257c11aaf8d52d1a0d',3335);decision=load(dr)
sh=fixed(S/'HDF.json','f722bad8d0d215ee184bf28c44977c8c74da4bdeca59b2c3e10085cd3bd7613a',2281);shdoc=load(sh);sm=load(shdoc['manifest_ref']);refs+=sm['members']
ph=load(shdoc['profile_source_handoff_ref']);pr=load(shdoc['profile_source_review_handoff_ref'])
source_manifest=load(ph['manifest_ref']);refs+=list(source_manifest['members'].values()) if isinstance(source_manifest['members'],dict) else source_manifest['members']
intent_ref=next(r for r in sm['members'] if Path(r['path']).name=='publication.intent.check.json');intent=load(intent_ref)
canon=intent['canonical_refs'];refs+=canon
main7ref=fixed(M/'actual-decision.json','d1037f351e2259796cd495e3a8877ed1bbf354d5af4d49e86f9a7b785e807749',7067);main7=load(main7ref);refs+=main7['final_target_refs']+main7['source21']
for e in rootg['entries']:refs.append({k:e[k] for k in ('path','sha256','bytes')})
refs+=out['after_target_refs']+[out['before_index_ref'],pin(__file__)]
sourceast=ast.parse(read(shdoc['writer_ref']));constants={}
for node in sourceast.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='PYREF':
  constants['PYREF']={kw.arg:ast.literal_eval(kw.value) for kw in node.value.keywords}
read(constants['PYREF']);require(str(Path(sys.executable).resolve())==constants['PYREF']['path'],'LOCKED_PYTHON');refs.append(constants['PYREF'])
gp=fixed(R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py','e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
# Finite Native packet baseline only; no repeat of its 22461-check audit.
nh=fixed(W/'checkpoint_r369_native_source_root/cp369-c19-20261009/Main-C19-actual-handoff.root.json','cc4e8de2bf69b1b322fb500369b85bc4d737b26f761fa746a52e8088c6257835',4474)
nhdoc=load(nh)
nrh=fixed(W/'main_c19_native_actual_independent_review_codex/review-1a12035-v2/HDF.json','49dd4ae646af95ecc38004f9650245e7e6ed9e04aa9fe8711b5fd945dd840270',6428)
nrm=fixed(W/'main_c19_native_actual_independent_review_codex/review-1a12035-v2/MF.json','eba83d3e4d1ade81a0566fed856e9cb3df3b1fa488f43868cf67f53b0254940a',6343)
native_refs=[nh,nrh,nrm,nhdoc['producer_closed_ref'],nhdoc['native_packet_ref']];refs+=native_refs
unique={}
for r in refs:
 read(r);k=r['path'].casefold();require(k not in unique or unique[k]==r,'NO_REF_ALIAS');unique[k]=r
gm=types.ModuleType('actual_profile_publication_guard');gm.__file__=gp['path'];sys.modules[gm.__name__]=gm;exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024)
checks=[]
def check(n,v,detail=None):require(v,n);checks.append(dict(name=n,passed=True,detail=detail))
guard.acquire(list(unique.values()))
try:
 check('Source_authorization_exact_actor_and_decision',decision['decision']=='SOURCE_ACCEPTED_FOR_ROOT_PROFILE_V4_PUBLICATION' and decision['actor_id']=='codex:/root/attach_fixture_source_review' and decision['actor_role']=='INDEPENDENT_NON_AUTHOR')
 check('actual_outcome_exact_authorization',out['adopter_independent_review_ref']==dr and decision['writer_ref']==shdoc['writer_ref'] and decision['profile_source_handoff_ref']==out['profile_source_handoff_ref']==shdoc['profile_source_handoff_ref'] and decision['profile_source_review_handoff_ref']==out['profile_source_review_handoff_ref']==shdoc['profile_source_review_handoff_ref'])
 result=io['original_tool_result'];args=io['original_tool_args'];cmd=args['cmd'];lines=result['output'].splitlines()
 check('original_actual_outer_and_locked_Python_zero',result['chunk_id']=='cdf6c5' and type(result['exit_code']) is int and result['exit_code']==0 and 'ROOT_SOURCE_PYTHON_EXIT=0' in lines)
 check('original_actual_output_exact_outcome',json.loads(lines[0])['outcome_ref']==outref)
 expected="& '"+constants['PYREF']['path']+"' -I -S -B -X utf8 '"+decision['writer_ref']['path']+"' activate '"+dr['path']+"' "+dr['sha256']+' '+str(dr['bytes'])
 check('original_actual_exact_argv',cmd.splitlines()[0]==expected and args['workdir']==str(R))
 check('actual_final_phase_two_targets_verified',out['mode']=='activate' and out['phase']=='TWO_TARGETS_VERIFIED' and out['error'] is None and out['index_anchor_published'] is True)
 check('actual_root_guard_bound_closed',out['guard_cleanup_ref']==rootgr and rootg['verification']=='PASSED' and rootg['closed'] is True and not rootg['errors'] and rootg['retained_handles_count']==0 and out['all_handles_closed'] is True and out['retained_handles_count']==0)
 targets=[R/'execution/v2.4/formal_case_index.py',R/'execution/v2.4/formal_profile_w09.py']
 check('exact_two_fixed_Main_target_refs',[pin(p) for p in targets]==out['after_target_refs'])
 check('exact_reviewed_source_bytes_on_Main',[p.read_bytes() for p in targets]==[read(r) for r in ph['after_refs']])
 old=read(out['before_index_ref']);current=targets[0].read_bytes()
 check('full_index_inverse_pinned',out['before_index_ref']==ph['original_index_ref'] and len(old)==66854 and hashlib.sha256(old).hexdigest()=='970ab391f2dd10a4f5e2713355a4a68757814994ef87b9aa92b9e555c12f1205')
 check('original_W07_prefix_51719_preserved',old[:51719]==current[:51719])
 check('original_CLI_guard_preserved',ast.dump(ast.parse(old).body[-1])==ast.dump(ast.parse(current).body[-1]))
 check('stage_consumed_after_anchor_publication',not (targets[0].parent/'formal_case_index.adoptv4-20261009.stage').exists())
 check('Main7_all_exact_unchanged',len(main7['final_target_refs'])==7 and all(pin(r['path'])==r for r in main7['final_target_refs']))
 check('Source21_all_exact_unchanged',len(main7['source21'])==21 and all(pin(r['path'])==r for r in main7['source21']))
 cp,ow,ss,cm=[json.loads(read(r)) for r in canon]
 check('four_Canon_exact_before_unchanged',len(canon)==4 and cp['revision']==369 and ow['revision']==173 and cm['revision']==39)
 check('no_current_formal_case_count_increase',cp['work_in_progress']['formal_cases_current']==0 and cp['work_in_progress']['accepted_card_count']==40)
 check('RootApprovedFormalCaptureindex_absent','w09_root_delivery_capture_index_ref' not in cp['work_in_progress'])
 check('publication_nonformal_and_no_retry',out['formal_case_accepted_delta']==0 and out['parent_acceptance'] is False and out['actual_formal_evidence_evaluated'] is False and out['automatic_retry'] is False and out['automatic_rollback'] is False)
 if native_refs:check('Native_actual_finite_baseline_unchanged',all(pin(r['path'])==r for r in native_refs),dict(ref_count=len(native_refs),rerun=False,qualification_unchanged=True))
 resultref=save('actual-byte-checks.json',dict(schema='researchos.profile-v4-actual-byte-checks.v1',checks=checks,actual_outcome_ref=outref,original_actual_tool_io_ref=io_ref,Main_after_refs=out['after_target_refs'],canonical_refs=canon,Main7_refs=main7['final_target_refs'],Source21_refs=main7['source21'],Native_baseline_refs=native_refs,adopter_rerun=False,dispatcher_rerun=False,Native_rerun=False,Main_or_Canon_written=False,formal_acceptance=False))
finally:
 closure=guard.close();gr=save('sourceguard.final.json',closure)
require(closure['closed'] is True and closure['retained_handles_count']==0 and not closure['errors'],'ACTUAL_REVIEW_GUARD_CLOSED')
actualdecision=save('actual-decision.json',dict(schema='researchos.profile-v4-independent-actual-adoption-decision.v1',decision='SOURCE_ADOPTION_ACTUAL_VERIFIED_NONFORMAL',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',source_publication_decision_ref=dr,actual_outcome_ref=outref,original_actual_tool_io_ref=io_ref,Main_after_refs=out['after_target_refs'],full_index_inverse_ref=out['before_index_ref'],before_profile='ABSENT',actual_byte_checks_ref=resultref,actual_SourceGuard_ref=gr,retained_handles_count=0,checks=len(checks),Source_adopted=True,formal_acceptance=False,formal_case_accepted_delta=0,parent_acceptance=False,current_formal_Actual_gate=False,RootApprovedFormalCaptureindex=False,Main_or_Canon_written_by_reviewer=False,STOP=True,FINAL=True))
print(json.dumps(dict(actual_decision_ref=actualdecision,checks_ref=resultref,guard_ref=gr,checks=len(checks),held_refs=len(unique)),ensure_ascii=False))
