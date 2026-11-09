import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;O=N/'continuation-cp532';E=R/'execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261025-current-chat';W=R/'.local/worktrees/source43-b-stop-finalpath-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write(chr(10))
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp532.pending');q.write_bytes(v);assert p.read_bytes()==b;os.replace(q,p)
for name,count in [('Source43-author-root-verification.json',241),('Source43-author-supplement-root-verification.json',37)]:
 v=read(N/name);assert v['verified_count']==count and not v['unresolved']
 for x in v['verified_refs']:assert ref(Path(x['path']))['sha256']==x['sha256']
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']];raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p);assert cp['revision']==531 and ow['revision']==317 and len(cp['failure_counters'])==2088
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda cwd,*a:subprocess.check_output(git+list(a),cwd=cwd)
assert g(R,'rev-parse','HEAD').decode().strip()=='4f4023c956f84d65743f39ce77d6c8899a21ada1';assert not g(R,'diff','--cached','--name-only');assert len(g(R,'status','--porcelain=v1','--untracked-files=no').splitlines())==20
for x in read(N/'selector-live-verification.json')['protected_source']:assert ref(Path(x['path']))['sha256']==x['sha256']
assert g(W,'rev-parse','HEAD').decode().strip()=='085b4711afe0c1288448b174eef24ecd5af0551b' and not g(W,'status','--porcelain=v1','--untracked-files=all')
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat();prior=read(N/'continuation-cp531/RESUME.current.json')
refs={k:ref(E/k)for k in ['FINAL-manifest.json','FINAL-supplement.json','FINAL-supplement-seal.json','diagnostic-ledger.json','claim-test-matrix.json']}
frozen={'status':'AUTHOR_PACKAGE_FROZEN_VERIFIED_PENDING_INDEPENDENT_REVIEW','commit':'085b4711afe0c1288448b174eef24ecd5af0551b','tree':'227d36324fd1053c285d0b2846a2b707ac2df6bd','refs':refs,'root_verifications':[ref(N/'Source43-author-root-verification.json'),ref(N/'Source43-author-supplement-root-verification.json')],'verified_reference_occurrences':278,'actual_authority':False,'formal_increment':0,'C57_issued':False}
new(O/'Source43-author-package-registered.json',frozen)
ledger=read(E/'diagnostic-ledger.json');items=[]
for category in ['old_failures_or_missing_exit','new_recorded_failures','launcher_binding_failures_without_subprocess_receipt']:
 for x in ledger[category]:items.append({'id':'source43-'+category+'-'+x['id'],'detail':x,'evidence_ref':refs['diagnostic-ledger.json']})
items.append({'id':'root012-display-truncation','detail':'012 full claimmatrix display exceeded output budget; raw retained and bounded013 + actual014 parser independently verified exact test counts.','evidence_ref':ref(N/'012-source43-final-index.recipe.result.json')})
assert len(items)==9;new(O/'new-records-ledger.json',{'distinct_mixed_records':9,'records':items,'product_failure_count':False,'old_011_absence':'Preserved as historical ordinal gap, no fabricated command/result','no_counter_reset':True})
before=list(cp['failure_counters']);existing={x.get('origin_key')for x in before}
for x in items:
 key='20261025|cp532-'+x['id'];assert key not in existing;cp['failure_counters'].append({'origin_key':key,'attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':x['detail'],'evidence_ref':x['evidence_ref'],'counter_reset':False})
assert cp['failure_counters'][:2088]==before and len(cp['failure_counters'])==2097
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v110',at=now,checkpoint_revision=532,ownership_revision=318,failure_records_preserved=2097,source43_author_package_ref=ref(O/'Source43-author-package-registered.json'),source43_author_ledger_import='DONE_CP532_8_DISTINCT_RECORDS')
resume['next_command']='Complete independent Source43 review of exact085b4711, then Root adopts only warranted Source scope and issues C57 against it. React Source13 real workbench implementation continues. Original data untouched; Main4f dirty20/protected9 preserved, formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=532,expected_previous_revision=531,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp532=rr,source43_author_package_ref=ref(O/'Source43-author-package-registered.json'));cp['evidence_index'].append({'kind':'SOURCE43_AUTHOR_FROZEN_EVIDENCE_VERIFIED_AND_FAILURES_PRESERVED','ref':rr,'formal_increment':0})
ow.update(revision=318,expected_previous_revision=317,updated_at=now,updated_by='codex:/root')
for k,v in ow['special_paths'].items():
 if isinstance(v,dict)and v.get('owner')=='codex:/root/source43_resume_20261025':v.update(state='FROZEN_AUTHOR_COMPLETE_PENDING_INDEPENDENT_REVIEW',source_edit_authority=False,evidence_ref=refs['FINAL-manifest.json'],supplement_seal_ref=refs['FINAL-supplement-seal.json'])
for p,n in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/n).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+chr(10)).encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+chr(10)).encode());swap(hp,raw[hp],('# Current verified continuation CP532'+chr(10)*2+'Read '+rr['path']+' first. Source43 author frozen and verified, independent review running; React13 building. C57 unissued. Main4f dirty20/protected9 stable; formal0/42/all22open, mixedrecords2097.'+chr(10)*2).encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':532,'ownership':318,'mixed_records':2097,'author_package':ref(O/'Source43-author-package-registered.json'),'resume':rr},ensure_ascii=False))
