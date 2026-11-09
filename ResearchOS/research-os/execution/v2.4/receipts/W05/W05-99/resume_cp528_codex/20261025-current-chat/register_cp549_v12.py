import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;O=N/'continuation-cp549';P=N.parent.parent/'qualification_maintenance_c57_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':p.relative_to(R.resolve()).as_posix()if p.is_relative_to(R.resolve())else str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def verify(p,sha):
 a=ref(p);assert a['sha256']==sha,str(p);return a
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp549.pending')
 with q.open('xb')as f:f.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
paths=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']];cp_p,ow_p,hp,sp=paths;raw={p:p.read_bytes()for p in paths};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==548 and ow['revision']==334 and len(cp['failure_counters'])==2212
prior=read(N/'continuation-cp548/RESUME.current.json');cv=read(N/'C57-v12-commit-root-verification.json');assert read(N/'067-c57-v12-commit-verify.recipe.result.json')['native_exit']==0
fpath=P/'C57-V12-FINALIZER.json';refs=[verify(fpath,'5f1a0508c53fa97a5265bb22f15415a084b3bb50070df0627e52a1d75ec269e5')];f=read(fpath);assert f['commit']==cv['commit']and f['tree']==cv['tree']and f['parent']==cv['parent']
for name,key in [('C57-V12-COMMIT-DELTA.patch','v12_delta_patch_sha256'),('C57-V12-STAGED-DELTA.patch','v12_delta_patch_sha256'),('C57-V12-CUMULATIVE-FULL.patch','cumulative_patch_sha256'),('C57-V12-STAGED-MANIFEST.json','v12_staged_manifest_sha256'),('C57-V12-PRETEST.json','source57_pre_post_snapshot_sha256'),('C57-V12-POSTTEST.json','source57_pre_post_snapshot_sha256'),('C57-FINALIZER.json','old_08d63_finalizer_sha256')]:refs.append(verify(P/name,f[key]))
ledger=P/'C57-V12-DIAGNOSTIC-INCREMENT-095-109.jsonl';refs.append(verify(ledger,f['diagnostic_increment_sha256']));events=[json.loads(x)for x in ledger.read_text(encoding='utf8').splitlines()]
for e in events:
 assert e['native_exit']==0
 for suffix,sha in e.items():
  if suffix in ['id','native_exit']:continue
  refs.append(verify(P/(e['id']+'.'+suffix),sha))
refs.append(verify(P/'C57-V12-DEPENDENCY-REUSE.md','0d969c4c4596fc37d3715231f06147c56c63305d9e3497f9228dcec789a0cfcf'))
g=lambda *a:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0']+list(a),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==prior['current_Main_HEAD']and not g('diff','--cached','--name-only');base=read(N/'React-Main-integration-baseline.json');assert g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==base['dirty_paths']
for x in base['protected_source']+base['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:
 p=Path(x['path']);verify(p if p.is_absolute()else R/p,x['sha256'])
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat();new(O/'C57-v12-finalizer-root-verification.json',{'finalizer':ref(fpath),'verified_refs':refs,'all_increment_native_exits_zero':True,'events':len(events),'dependency_reuse':ref(P/'C57-V12-DEPENDENCY-REUSE.md'),'formal_increment':0})
am=read(N/'continuation-cp547/C57-independent-phase2-exact57-amendment.json');am.update(schema='researchos.C57-independent-phase2-exact57-amendment.v2',at=now,candidate_commit=f['commit'],candidate_tree=f['tree'],candidate_parent=f['parent'],candidate_baseline=f['baseline'],source57_manifest_ref=ref(P/'C57-V12-COMMIT-SOURCE57-MANIFEST.json'),author_finalizer_ref=ref(fpath),Root_commit_verification_ref=ref(N/'C57-v12-commit-root-verification.json'),Root_finalizer_verification_ref=ref(O/'C57-v12-finalizer-root-verification.json'),previous_phase2_amendment_ref=ref(N/'continuation-cp547/C57-independent-phase2-exact57-amendment.json'),independent_static_fix_ref=cv['static_seal'])
am['source_snapshot_upgrade']={'allowed_delta':cv['delta'],'old_commit':f['parent'],'new_commit':f['commit'],'method':'After every running old-source command finishes, preserve old2 bytes+hashes and previous run manifests; upgrade own existing snapshot from exact new git blobs or use a new isolated snapshot. Verify all57/40pins, full commit diff exactly2, supplementary tests hashes and explicit source version before any v12 run. Never mutate source during an active old-source test. Directory label does not determine source version.','unaffected_reuse':'Completed08d63 assertions may be reused only with explicit unchanged source/dependency reasoning; oldnative tests are not v12 privilege acceptance.','new_required_checks':'Independent targeted dangerous-LUID admission disabled/enabled and malformed/safe cases, real safe business producer/current reader, C inherited and D noAI/native ACL regressions and necessary Host wiring. Real dangerous privilege tokens remain unexecuted, not presumed passed.'}
new(O/'C57-independent-phase2-v12-amendment.json',am)
pending={'status':'RAW_PRESERVED_PENDING_FINAL_PHASE2_DEDUP_IMPORT_NOT_ZERO','events':['Boot v12-dev-01 native compile1','Independent094 and094b cache prepare native1 each','Independent098 nominalD actuallyC environment observation, corrected108 allTEMP/TMP/TMPDIR/GOTMPDIR ownD','Token v12 auxiliary rg nestednative2 withouterPowerShell0, correctednewrecipe','Root collaboration.wait_agent aborted-before-dispatch three times at bootv12focused/finalv12/independent108 message boundaries'],'note':'Existing2212 records preserved unchanged; current raw files/seals remain append-only. Import exact final-review ledgers next; do not reset or treat pending aszero.'}
new(O/'pending-diagnostic-increment.json',pending)
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v127',at=now,checkpoint_revision=549,ownership_revision=335,failure_records_preserved=2212,C57_frozen_commit=f['commit'],C57_frozen_tree=f['tree'],C57_phase2_v12_amendment_ref=ref(O/'C57-independent-phase2-v12-amendment.json'),C57_pending_diagnostics_ref=ref(O/'pending-diagnostic-increment.json'))
resume['next_command']='Complete independent fixed73 review and v12 affected native tests on exact03aa4d/tree81059, upgraded own snapshot only after old commands finish; old08d63 remains historic. Static threeprivilegeP1 closed; Root57/40pins/delta2/clean/finalizer verified. Independent oldsource core/domain/Boot/87table typed census/actualholds/9SQLabortcuts/journal prefixes reportedpassed; finalseal pending. Pending diagnostic increment raw preserved, existing2212 notreset. MainReact7d preserved; no originaldata/Core/ACL/STOP/restart/Mainmerge; formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=549,expected_previous_revision=548,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp549=rr,C57_phase2_v12_amendment_ref=ref(O/'C57-independent-phase2-v12-amendment.json'));cp['evidence_index'].append({'kind':'C57_V12_EXACT_COMMIT_VERIFIED_STATIC_P1_CLOSED_AFFECTED_INDEPENDENT_TESTS_AUTHORIZED','ref':rr,'formal_increment':0});ow.update(revision=335,expected_previous_revision=334,updated_at=now,updated_by='codex:/root');ow['special_paths']['C57_boot6_source'].update(state='V12_FROZEN_IN_COMMIT03AA4D_NO_SOURCE_WRITES',evidence_ref=ref(N/'C57-v12-commit-root-verification.json'));ow['special_paths']['C57_independent_review'].update(state='PHASE2_V12_EXACT03AA4D_AFFECTED_TESTS_AND_FIXED73_FINALIZATION',evidence_ref=ref(O/'C57-independent-phase2-v12-amendment.json'))
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as out:out.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());swap(hp,raw[hp],('# Current verified continuation CP549\n\nRead '+rr['path']+' first. C57v12commit03aa4d/tree81059/parent08d63 frozen;57source/52cumulative/40pins verified, independentstaticP1closed. Phase2v12 affected retest authorized with sourceversion binding; independent fixed73 finalseal pending. Existing2212+pendingrawdiagnostics retained. MainReact7d preserved; formal0/42/all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':549,'ownership':335,'mixed_records':2212,'pending_diagnostics':True,'finalizer_refs':len(refs),'phase2_amendment':ref(O/'C57-independent-phase2-v12-amendment.json'),'resume':rr},ensure_ascii=False))
