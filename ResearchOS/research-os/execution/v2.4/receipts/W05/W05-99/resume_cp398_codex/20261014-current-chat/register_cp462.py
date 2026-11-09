import datetime, hashlib, json, os, subprocess
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');BASE=Path(__file__).parent;OUT=BASE/'continuation-cp462'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp462.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
mirrors={}
for name,sub,manifest in [('mu-m1-independent-review-20261014','mu_m1_01_independent_review_codex','FINAL-manifest.json'),('root-schema25-independent-review-20261014','root_schema25_independent_review_codex','manifest.json')]:
 src=Path('C:/Users/yqyyds/.codex/researchos-build-worktrees')/name;dst=ROOT/'execution/v2.4/receipts/W17/W17-03'/sub/'20261014-current-chat';dst.mkdir(parents=True,exist_ok=False)
 m=read(src/manifest);members=m if isinstance(m,list) else m['members']
 for entry in members:
  source=src/entry['path'];assert source.resolve().is_relative_to(src.resolve()) and ref(source)['sha256']==entry['sha256'];dest=dst/entry['path'];dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(source.read_bytes())
 if not (dst/manifest).exists():
  with (dst/manifest).open('xb') as f:f.write((src/manifest).read_bytes())
 mirrors[sub]=dst
cp_p=ROOT/'execution/v2.4/checkpoint.json';ow_p=ROOT/'execution/v2.4/path_ownership.json';h_p=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';s_p=ROOT/'execution/v2.4/step_state.json'
raw={p:p.read_bytes() for p in [cp_p,ow_p,h_p,s_p]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==461 and ow['revision']==247 and len(cp['failure_counters'])==1396
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==cp['head']=='454492f78fc0536966c8c8343d4bdd2fd99250b7'
assert ref(ROOT/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
for m in read(ROOT/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:assert ref(ROOT/m['path'])['sha256']==m['sha256']
OUT.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
source=['internal/host/runtime_coding_windows.go','internal/host/runtime_coding_windows_test.go']
scope={'schema':'researchos.go-predeclared-any-checker-repair/1','at':now,'owner':'codex:/root/coding_any_repair','model':'gpt-6-sol','reasoning_effort':'high','model_choice_reason':'Bounded production AST checker and regression repair, independent security review follows','base_commit':cp['head'],'worktree':'C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-repair-20261014','paths':source,'baseline':[ref(ROOT/p) for p in source],'requirements':['Accept Go predeclared any conversion without granting missing same-package helper authority; retain existing closure, offline import, TestMain/init, embed and helper guards','Regression must demonstrate prior rejection of any(nil), new acceptance, and missingHelper still rejected','Run current production checker on exact real326 source inventory via isolated read-only fixture, no API/DB/GUI actions and no ownCLI target source edits','Do not change read/write scope, tools/native policies, runtime provider, installed SDK, contracts or migrations','Freeze exact2 patch/input/test receipts; independent review before Main/package/activation'],'formal_increment':0}
new(OUT/'source-scope.json',scope)
diagnostics=[('old-desktop-screenshot-timeout',1,'Old GUI screenshot timed out after3s; DOM snapshot saved, subsequent new GUI screenshot successful'),('prepare-retry08-rejected',1,'Actual normal GUI CODING_PREPARE_REJECTED, no confirmation/new configuration; readonly checker reproduced any alias omission'),('optional-unfinished-review-read',1,'Optional unfinished FINAL-report read returned1; later real report found'),('mu-m1-author-worker-routing',5,'Author initial versioned pause routed to old parser; report acknowledges local raw not captured'),('mu-m1-author-old-bundle',1,'Native harness stale bundle mismatch; failed raw retained, current bundle rebuilt'),('mu-m1-author-whitespace',1,'Pre-freeze Windows newline translation; retained failure report, restoredLF'),('mu-m1-review-setup',3,'Reviewer missing environment, minimal snapshot missing packages and generator assertion retained in independent report'),('storage-r1-independent-findings',4,'Independent counterexamples found cancellation, principal, carry and missing state witness gaps; R2 changes made, not accepted'),('manifest-shape-diagnostic',1,'Root assumed dict for list-shaped storage review manifest; read-only AttributeError abf495, corrected shape inspection')]
for key,attempts,detail in diagnostics:
 origin='20261014|'+key;assert not any(x.get('origin_key')==origin for x in cp['failure_counters'])
 cp['failure_counters'].append({'origin_key':origin,'attempts':attempts,'status':'DIAGNOSTIC_PRESERVED','detail':detail,'counter_reset':False,'actual_models':0})
resume={'schema':'researchos.current-chat-resume.v40','at':now,'checkpoint_revision':462,'ownership_revision':248,'head':cp['head'],'project_id':cp['project_id'],'current_step_id':'W05-99','goal_status':'ACTIVE','accepted_formal_cases':0,'required_formal_cases':42,'required_parent_tasks':22,'failure_records_preserved':len(cp['failure_counters']),'source_scope_ref':ref(OUT/'source-scope.json'),'desktop':{'pid':65728,'core_pid':61952,'launcher_session':94341,'package':'C:/Users/yqyyds/.codex/researchos-resource-cache/normal-status-combined-5ddc0abb-20261014','coding_result':'PREPARE_REJECTED_NO_CONFIGURATION_OR_MODEL','old_electron_numeric_exit':0},'mu_m1_review_ref':ref(mirrors['mu_m1_01_independent_review_codex']/'FINAL-report.json'),'root_storage_r1_review_ref':ref(mirrors['root_schema25_independent_review_codex']/'report.md'),'root_storage_r2':'isolated12top tests PASS; independent R2 pending; no Main/DB integration','phone_ready':False,'next_command':'Fix predeclared any checker exact2 in isolated source, independently review and build before replacing normal Desktop package. Mu M1 source/native synthetic independently approved but Core integration open. Continue storage R2 review.'}
new(OUT/'RESUME.current.json',resume);rr=ref(OUT/'RESUME.current.json')
cp.update(revision=462,expected_previous_revision=461,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp462=rr,coding_any_source_scope_ref=ref(OUT/'source-scope.json'),mu_m1_independent_review_ref=resume['mu_m1_review_ref'],root_storage_r1_review_ref=resume['root_storage_r1_review_ref'])
cp['evidence_index'].append({'kind':'LIVE_CODING_CHECKER_REPAIR_AND_M1_STORAGE_REVIEW','ref':rr,'formal_increment':0})
ow.update(revision=248,expected_previous_revision=247,updated_at=now,updated_by='codex:/root')
ow['special_paths']['coding_any_repair']={'owner':scope['owner'],'ref':ref(OUT/'source-scope.json'),'paths':source,'worktree':scope['worktree']}
ow['path_lease_transfers'].append({'at':now,'actor':'codex:/root','new_owner':scope['owner'],'new_subtask':'W05-99/go-any-checker','new_worktree':scope['worktree'],'paths':source,'scope_ref':ref(OUT/'source-scope.json'),'kind':'ISOLATED_SOURCE_LEASE'})
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(h_p,'handoff.before.raw.md')]: (OUT/name).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(h_p,raw[h_p],('# Current verified continuation CP462\n\nRead `'+rr['path']+'` first. Actual coding PREPARE rejected; bounded any checker source repair registered. Mu M1 source/native synthetic reviewed, storageR2 review pending. Formal0/42 all22open.\n\n').encode()+raw[h_p]);assert s_p.read_bytes()==raw[s_p]
print(json.dumps({'checkpoint':462,'ownership':248,'failure_records':len(cp['failure_counters']),'resume':rr,'scope':ref(OUT/'source-scope.json')}))
