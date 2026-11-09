import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;O=B/'continuation-cp507';E=R/'execution/v2.4/receipts/W05/W05-99';S=E/'owned_core_stop_source_codex/20261015-current-chat';W=R/'.local/worktrees/owned-core-stop-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b;t=p.with_name(p.name+'.cp507.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==506 and ow['revision']==292 and len(cp['failure_counters'])==1583
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)
assert len(subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=R,text=True).splitlines())==20
for v in read(E/'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:assert ref(R/v['path'])['sha256']==v['sha256']
idxp=S/'FINAL-RECEIPT-INDEX.json';assert ref(idxp)['sha256']=='2a43ef48c86466a5c86ea1cd76f3f53ededbf78d6291f120756cd712e7a0cf93';idx=read(idxp);assert len(idx['raw_failures'])==6 and idx['raw_command_counts']['incomplete']==0
verified=[]
for key,v in idx['candidates'].items():
 d=S/('candidate-'+key+'-final');mp=d/'manifest.json';assert ref(mp)['sha256']==v['manifest']['sha256'];m=read(mp)
 for file,tag in [('source.patch','patch'),('CUT-LEDGER.md','cut_ledger')]:assert ref(d/file)['sha256']==v[tag]['sha256']
 assert len(m['paths'])==19
 changed=subprocess.check_output(['git','diff','--name-only','4f4023c956f84d65743f39ce77d6c8899a21ada1',v['commit']],cwd=R,text=True).splitlines();assert set(changed)==set(m['paths'])
 assert subprocess.check_output(['git','rev-parse',v['commit']+'^{tree}'],cwd=R,text=True).strip()==v['tree']
 for rel,h in m['paths'].items():
  b=subprocess.check_output(['git','show',v['commit']+':'+rel],cwd=R);assert hashlib.sha256(b).hexdigest()==h['sha256'] and len(b)==h['bytes']
 for c in m['commands']:
  p=S/c['path'];assert hashlib.sha256((p/'stdout.bin').read_bytes()).hexdigest()==c['stdout_sha256'];assert hashlib.sha256((p/'stderr.bin').read_bytes()).hexdigest()==c['stderr_sha256'];assert (p/'before.json').is_file() and (p/'after.json').is_file()
 verified.append({'candidate':key,'commit':v['commit'],'tree':v['tree'],'manifest_ref':ref(mp),'patch_ref':ref(d/'source.patch'),'cutledger_ref':ref(d/'CUT-LEDGER.md'),'paths':19,'command_refs_verified':len(m['commands'])})
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=W,text=True).strip()=='56e44e1b8a5086c26074c13db14173c5b1ab6116';assert not subprocess.check_output(['git','status','--porcelain'],cwd=W)
now=datetime.datetime.now(datetime.timezone.utc).isoformat();O.mkdir(exist_ok=False);new(O/'stop-source-artifact-verification.json',{'at':now,'candidates':verified,'source_acceptance':False,'actual_operation_authority':False,'known_source_gaps':['independent compiled Root operation anchor absent/fullCommitE2E notrun','S202 foreignSID/Host/root/reparse missingfullnegativefixtures','S211 zeroaction timeout/cancel/fullguardmatrix incomplete','S208 private fixedSQLallowlist audit pending','strict worker/verifier proof parser narrowerthan possiblefutureacceptedhistorical classes; currentactual native/F01 proof missing'],'tests_rerun_by_Root':0,'formal_increment':0})
old=list(cp['failure_counters'])
for i,x in enumerate(idx['raw_failures'],1):
 origin='20261015|owned-core-stop-source-failure-'+str(i);assert not any(y.get('origin_key')==origin for y in old);cp['failure_counters'].append({'origin_key':origin,'attempts':1,'status':'SOURCE_TEST_OR_DIAGNOSTIC_FAILURE_PRESERVED','detail':x,'evidence_ref':ref(idxp),'counter_reset':False})
assert cp['failure_counters'][:1583]==old and len(cp['failure_counters'])==1589
resume=read(B/'continuation-cp506/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v85',at=now,checkpoint_revision=507,ownership_revision=293,failure_records_preserved=1589,active_source_cards=['CP503 qualificationA-r2 realconsumerF03/8calls4toolspositivefixtures'],owned_core_stop_source_index_ref=ref(idxp),owned_core_stop_source_artifact_verification_ref=ref(O/'stop-source-artifact-verification.json'),owned_core_stop_source_state='FROZEN_56E44E1B_EXACT19_NOT_ACCEPTED_ANCHOR_FULLCOMMIT_AND_CUT_GAPS',next_command='CompleteA-r2 realentry29matrix and8/4positivecontrols thenindependentreview. STOP19 final56e44e1b+intermediate2ed frozenverified;6failsimported; not Sourceaccepted. IndependentastraSTOPanchor design3filereview running; revision03architectClease/F01/neverjobcontinues. AfteranchoracceptedissueNEWSourcecardfrom56eworktree fornonemptytwoBuildGrantCLI E2EplusS202/S211/SQLallowlist gaps inoriginal19. No actualstop/backup/DB/model/replay/newrequest/migration. Main4f/old20/indexempty/f3consumedUNKNOWN unchanged; formal0/42/all22open.')
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=507,expected_previous_revision=506,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp507=rr,owned_core_stop_source_index_ref=ref(idxp),owned_core_stop_source_artifact_verification_ref=ref(O/'stop-source-artifact-verification.json'));cp['evidence_index'].append({'kind':'OWNED_CORE_STOP_SOURCE19_CANDIDATES_FROZEN_NOT_ACCEPTED_AND_6_RAW_FAILURES_PRESERVED','ref':rr,'formal_increment':0})
ow.update(revision=293,expected_previous_revision=292,updated_at=now,updated_by='codex:/root');ow['special_paths']['stop_anchor_independent_design_review']['state']='REVIEW_RUNNING';ow['special_paths']['owned_core_stop_source_frozen']={'owner':'codex:/root/owned_core_stop_builder','state':'SOURCE56E44E1B_FROZEN_NOT_ACCEPTED_NO_ACTIVE_CONSTRUCTION','index_ref':ref(idxp),'guard_ref':ref(O/'stop-source-artifact-verification.json')}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/name).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP507\n\nRead `'+rr['path']+'` first. SourceSTOP19frozen56e/2ed NOTaccepted; 6rawfailsimported. OnlyactiveSourceA-r2; STOPanchorindependentdesignreview running andarchitectCproofanalysis. ActualSTOPUNAVAILABLE/F01broadNOT_PROVABLE. Main4f/f3consumedUNKNOWN untouched. Formal0/42/all22open; preservedrecords1589.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':507,'ownership':293,'failure_records':1589,'resume':rr,'stop_source_artifacts':ref(O/'stop-source-artifact-verification.json')}))
