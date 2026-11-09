import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;O=N/'continuation-cp531';W=R/'.local/worktrees/source43-b-stop-finalpath-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix() if p.is_relative_to(R.resolve()) else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp531.pending');q.write_bytes(v);assert p.read_bytes()==b;os.replace(q,p)
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']];raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p);assert cp['revision']==530 and ow['revision']==316 and len(cp['failure_counters'])==2086
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda cwd,*a:subprocess.check_output(git+list(a),cwd=cwd)
assert g(R,'rev-parse','HEAD').decode().strip()=='4f4023c956f84d65743f39ce77d6c8899a21ada1';assert not g(R,'diff','--cached','--name-only');assert len(g(R,'status','--porcelain=v1','--untracked-files=no').splitlines())==20
for x in read(N/'selector-live-verification.json')['protected_source']:assert ref(Path(x['path']))['sha256']==x['sha256']
candidate=read(N/'Source43-candidate-root-verification.json');s=read(N/'continuation-cp529/source43-resume-scope.json')
assert g(W,'rev-parse','HEAD').decode().strip()==candidate['head'] and not g(W,'status','--porcelain=v1','--untracked-files=all')
assert set(candidate['source43'])==set(s['source_allowlist'])
pins=s['mechanical_source41_pins'];verified=[]
for rel,want in pins.items():
 expected=want if isinstance(want,str) else want['sha256']
 actual=ref(W/rel);assert actual['sha256']==expected,(rel,expected,actual);verified.append(actual)
assert len(verified)==41
for x in candidate['source_pins']:assert ref(W/x['path'])['sha256']==x['sha256']
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat();prior=read(N/'continuation-cp530/RESUME.current.json')
new(O/'Source43-candidate-registered.json',{'status':'CLEAN_SOURCE_CANDIDATE_PENDING_INDEPENDENT_REVIEW','commit':candidate['head'],'tree':candidate['tree'],'source_count':43,'root_candidate_verification':ref(N/'Source43-candidate-root-verification.json'),'unchanged_accepted_mechanical41':verified,'author_final_manifest_status':'PENDING_AUTHOR_INDEX_NOT_SOURCE_MUTATION','author_receipts':str(R/'execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261025-current-chat'),'formal_increment':0})
review=read(N/'Source43-independent-review.unissued.json');review.update(schema='researchos.Source43-independent-review.scope.v1',status='REGISTERED_INDEPENDENT_REVIEW',candidate_commit=candidate['head'],candidate_tree=candidate['tree'],candidate_ref=ref(O/'Source43-candidate-registered.json'),source_allowlist=s['source_allowlist'],accepted_mechanical41_pins=pins,author_final_manifest_expected=str(R/'execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261025-current-chat/FINAL-manifest.json'),at=now)
review['requirements'].append('Author FINAL indexing may finish concurrently with initial static review. Do not freeze independent verdict until exact author FINAL, ledger and evidence references have been received and verified. Source commit must remain exactclean throughout.')
new(O/'Source43-independent-review-scope.json',review)
records=read(N/'root-pending-records-cp531.json')['records'];before=list(cp['failure_counters'])
for x in records:cp['failure_counters'].append({'origin_key':'20261025|cp531-'+x['id'],'attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':x,'evidence_ref':ref(N/'root-pending-records-cp531.json'),'counter_reset':False})
assert cp['failure_counters'][:2086]==before and len(cp['failure_counters'])==2088
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v109',at=now,checkpoint_revision=531,ownership_revision=317,failure_records_preserved=2088,source43_candidate_ref=ref(O/'Source43-candidate-registered.json'),source43_independent_review_scope_ref=ref(O/'Source43-independent-review-scope.json'),C57_unissued_preparation_ref=ref(N/'C57-source-card.unissued.json'),active_source_cards=[prior['react_frontend_source_scope_ref']],source43_author_ledger_import='PENDING_AUTHOR_FREEZE')
resume['next_command']='Independently review exact Source43 commit085b4711 before Root adoption and C57 issuance; obtain author FINAL before verdict. React Source13 implementation proceeds in isolated worktree. Main4f dirty20/protected9 preserved; no original data/Host/API/STOP/fence/restart. Formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=531,expected_previous_revision=530,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp531=rr,source43_independent_review_scope_ref=ref(O/'Source43-independent-review-scope.json'));cp['evidence_index'].append({'kind':'SOURCE43_CLEAN_CANDIDATE_INDEPENDENT_REVIEW_REGISTERED','ref':rr,'formal_increment':0})
ow.update(revision=317,expected_previous_revision=316,updated_at=now,updated_by='codex:/root')
for k,v in ow['special_paths'].items():
 if isinstance(v,dict) and v.get('owner')=='codex:/root/source43_resume_20261025':v.update(state='SOURCE_FROZEN_PENDING_FINAL_INDEX_AND_INDEPENDENT_REVIEW',source_edit_authority=False,candidate_ref=ref(O/'Source43-candidate-registered.json'))
ow['special_paths']['source43_independent_review']={'owner':review['owner'],'state':'REGISTERED','scope_ref':ref(O/'Source43-independent-review-scope.json'),'write_scope':[review['review_worktree'],review['own_receipts'],review['own_temporary_root'],review['own_ascii_native_fixture_root']],'source_edit_authority':False,'original_data_or_process_authority':False}
for p,n in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/n).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode());swap(hp,raw[hp],('# Current verified continuation CP531'+chr(10)*2+'Read '+rr['path']+' first. Source43 clean085b4711 awaiting independentreview; React13 building. C57 exact57 preparation unissued. Formal0/42/all22open, mixedrecords2088.'+chr(10)*2).encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':531,'ownership':317,'mixed_records':2088,'review_scope':ref(O/'Source43-independent-review-scope.json'),'resume':rr},ensure_ascii=False))
