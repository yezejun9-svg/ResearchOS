import ast,copy,hashlib,json,sys,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'formal_profile_v4_adoption_source_root/adoptv4-20261009/v2'
B=W/'formal_profile_v4_adoption_independent_source_review_codex/adoptr-01a12072'
N=Path(__file__).resolve().parent
def require(v,c):
 if not v:raise AssertionError(c)
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def fixed(p,s,n):
 r=pin(p);require((r['sha256'],r['bytes'])==(s,n),'EXACT_PIN '+str(p));return r
def save(n,v):
 with (N/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/n)
sh=fixed(S/'HDF.json','f722bad8d0d215ee184bf28c44977c8c74da4bdeca59b2c3e10085cd3bd7613a',2281)
sm=fixed(S/'MF.json','d1560561fc9456795e6f2e203a6b8521716a873d7f0077958286e402f490021a',2878)
wr=fixed(S/'adopt_formal_profile.source.py','5351fa901261af615b6f4afa9abc9f3329ec2a8e6415bdb5669dbac4ec078077',8796)
br=fixed(B/'source-decision.json','f2bf92348cf710038abb7a11d8034d0f6aede9e26a169164b5379001002b30ca',2859)
bc=fixed(B/'controls.json','7a6fa7cb0a4eeccfc6d4473ce8c6e9b4d31ffcd15a9ea241f0f654fd6f69e4cf',10508)
inverse=fixed(S/'adopter.v1.full-byte-inverse.py','c5a3e4eae036f6468b8a63c3a4e51a082b1182a6a27484f0bc3393b417bfb668',8759)
h=json.loads(Path(sh['path']).read_bytes());mf=json.loads(Path(sm['path']).read_bytes());require(h['manifest_ref']==sm,'HDF_MF')
src=Path(wr['path']).read_bytes();before=Path(inverse['path']).read_bytes()
old=b"a['actor_id']!=ACTOR";new=b"a['actor_id']=='codex:/root/attach_fixture_source_review'"
require(before.count(old)==1 and src==before.replace(old,new,1),'SINGLE_COMPLETE_BYTE_REPLACEMENT')
writer=types.ModuleType('adopter_v2_independent');writer.__file__=wr['path'];sys.modules[writer.__name__]=writer
exec(compile(src,wr['path'],'exec'),writer.__dict__)
prepared=writer.prepare();ph,psh,psm,prh,prm,canon,refs,targets,indexbefore,after=prepared
refs+=[sh,sm,br,bc,inverse,wr,pin(__file__),pin(targets[0]),*mf['members']]
unique={}
for r in refs:
 writer.read(r);key=r['path'].casefold();require(key not in unique or unique[key]==r,'NO_ALIAS');unique[key]=r
gm=types.ModuleType('adopter_v2_real_source_guard');gm.__file__=writer.GP['path'];sys.modules[gm.__name__]=gm
exec(compile(writer.read(writer.GP),writer.GP['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024)
checks=[]
def check(n,v,detail=None):require(v,n);checks.append(dict(name=n,passed=True,detail=detail))
guard.acquire(list(unique.values()))
try:
 check('exact_complete_one_replacement_and_full_inverse',src==before.replace(old,new,1) and src.replace(new,old,1)==before)
 check('receipt_namespace_exact_v2',writer.N==S.resolve() and all(Path(r['path']).parent==S.resolve() for r in mf['members']))
 check('profile_source_and_review_HDF_exact_bindings',psh==h['profile_source_handoff_ref'] and prh==h['profile_source_review_handoff_ref'])
 check('fresh_Main_before_and_profile_absent',targets[0].read_bytes()==indexbefore and not targets[1].exists())
 execute_ast=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
 class ReachedGuard(Exception):pass
 ready=dict(decision='SOURCE_ACCEPTED_FOR_ROOT_PROFILE_V4_PUBLICATION',actor_role='INDEPENDENT_NON_AUTHOR',actor_id='codex:/root/attach_fixture_source_review',writer_ref=wr,profile_source_handoff_ref=psh,profile_source_review_handoff_ref=prh)
 def replay(doc):
  env=dict(writer.__dict__);env['prepare']=lambda:(ph,psh,psm,prh,prm,canon,[],targets,indexbefore,after);env['decode']=lambda ref:doc;env['pin']=lambda p:wr
  def stop(ref):raise ReachedGuard('SOURCE_GATE_PASSED_BEFORE_ANY_MAIN_WRITE')
  env['read']=stop;exec(compile(ast.Module(body=[execute_ast],type_ignores=[]),wr['path'],'exec'),env)
  try:env['execute']('activate',wr)
  except ReachedGuard:return 'SOURCE_GATE_PASSED_BEFORE_ANY_MAIN_WRITE'
  except (ValueError,KeyError,TypeError) as e:return str(e)
  raise AssertionError('UNEXPECTED_EXECUTION_RETURN')
 check('canonical_designated_non_author_positive',replay(ready)=='SOURCE_GATE_PASSED_BEFORE_ANY_MAIN_WRITE')
 prior=json.loads(Path(bc['path']).read_bytes())
 replays=[]
 for example in prior['counterexamples']:
  doc=copy.deepcopy(ready);doc['actor_id']=example['input']['actor_id'];result=replay(doc)
  check('original_counterexample_now_rejects_'+example['label'],result=='ROOT_ADOPTER_NONSIGNED_SOURCE_REVIEW')
  replays.append(dict(label=example['label'],prior_controls_ref=bc,actor_id=doc['actor_id'],prior_actual=example['actual'],current_actual=result,Main_written=False))
 for actor in ('codex:/root','codex:/root/another_reviewer','CODEX:/ROOT/ATTACH_FIXTURE_SOURCE_REVIEW'):
  doc=copy.deepcopy(ready);doc['actor_id']=actor;check('non_exact_actor_rejected_'+actor,replay(doc)=='ROOT_ADOPTER_NONSIGNED_SOURCE_REVIEW')
 for field in ('decision','actor_role','writer_ref','profile_source_handoff_ref','profile_source_review_handoff_ref'):
  doc=copy.deepcopy(ready);doc[field]='incorrect';check('exact_'+field+'_binding_retained',replay(doc)!='SOURCE_GATE_PASSED_BEFORE_ANY_MAIN_WRITE')
 check('after_controls_Main_before_and_profile_absent',targets[0].read_bytes()==indexbefore and not targets[1].exists())
 for r in canon:writer.read(r)
 check('four_Canonical_files_unchanged',True)
 controls=save('controls.json',dict(schema='researchos.adopter-v2-delta-source-controls.v1',evidence_kind='NON_AUTHORITATIVE_SOURCE_CONTROLS',checks=checks,original_counterexample_replays=replays,actual_Main_publication=False,actual_formal_evidence=False))
finally:
 closure=guard.close();gr=save('sourceguard.final.json',closure)
require(closure['closed'] is True and not closure['errors'] and closure['retained_handles_count']==0,'REAL_SOURCE_GUARD_CLOSED')
fr=save('findings.json',dict(blocking_count=0,findings=[],closed=['ADOPTER-F1'],baseline_decision_ref=br,scope='ONLY_ADOPTER_V2_ACTOR_GATE_DELTA'))
dr=save('source-decision.json',dict(schema='researchos.adopter-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_PROFILE_V4_PUBLICATION',actor_role='INDEPENDENT_NON_AUTHOR',actor_id='codex:/root/attach_fixture_source_review',writer_ref=wr,source_handoff_ref=sh,source_manifest_ref=sm,profile_source_handoff_ref=psh,profile_source_review_handoff_ref=prh,baseline_decision_ref=br,findings_ref=fr,controls_ref=controls,actual_SourceGuard_ref=gr,retained_handles_count=0,checks=len(checks),qualification='SOURCE_PUBLICATION_QUALIFICATION_ONLY',Root_actual_publication_required=True,Main_adopted=False,Canonical_writes=False,formal_case_accepted_delta=0,parent_acceptance=False,STOP=True,FINAL=True))
mr=save('MF.json',dict(schema='researchos.adopter-independent-source-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
hr=save('HDF.json',dict(schema='researchos.adopter-independent-source-handoff.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_PROFILE_V4_PUBLICATION',actor_id='codex:/root/attach_fixture_source_review',manifest_ref=mr,decision_ref=dr,source_handoff_ref=sh,source_manifest_ref=sm,writer_ref=wr,controls_ref=controls,findings_ref=fr,actual_SourceGuard_ref=gr,retained_handles_count=0,Main_adopted=False,Canonical_writes=False,formal_case_accepted_delta=0,parent_acceptance=False,STOP=True,FINAL=True))
for r in unique.values():writer.read(r)
check('postseal_Main_unchanged_profile_absent',targets[0].read_bytes()==indexbefore and not targets[1].exists())
print(json.dumps(dict(handoff_ref=hr,manifest_ref=mr,decision_ref=dr,findings_ref=fr,controls_ref=controls,guard_ref=gr,held_refs=len(unique),sealed_checks=len(checks)-1,postseal_check=True),ensure_ascii=False))
