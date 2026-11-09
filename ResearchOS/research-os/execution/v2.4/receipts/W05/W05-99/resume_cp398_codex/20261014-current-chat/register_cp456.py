"""Register finite Desktop STATUS repair; preserve all prior counters and acceptance."""
import datetime, hashlib, json, os, subprocess
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).parent/'continuation-cp456'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp456.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
paths=[ROOT/'execution/v2.4'/x for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
cp_p,ow_p,h_p,s_p=paths;raw={p:p.read_bytes() for p in paths};cp,ow=read(cp_p),read(ow_p)
assert cp['revision']==455 and ow['revision']==242 and len(cp['failure_counters'])==1389
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==cp['head']=='c465d1356480d6e6a90da84656724f9fc02b31c7'
assert ref(ROOT/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
for m in read(ROOT/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:assert ref(ROOT/m['path'])['sha256']==m['sha256']
now=datetime.datetime.now(datetime.timezone.utc).isoformat();OUT.mkdir(exist_ok=False)
source=['apps/desktop/main/lib/desktop-management.js','apps/web/src/workbench.jsx','tests/ui/desktop/desktop-management-boundary.test.mjs','tests/ui/desktop/coding-authorization-boundary.test.mjs']
scope={'schema':'researchos.desktop-original-qualification-status-repair/1','at':now,'owner':'codex:/root/qualification_status_repair','model':'gpt-6-astra','reasoning_effort':'high','model_choice_reason':'Native authority and original-request security lifecycle requires architecture reasoning','base_commit':cp['head'],'worktree':'C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014','paths':source,'source_baselines':[ref(ROOT/p) for p in source],'observed_problem':'Consumed settled original qualification cannot STATUS after writer expiry/renewal/revision changes; coding PREPARE requires fresh original STATUS and deadlocks. GUI actual error retained.','requirements':['Permit original read-only STATUS across writer authority/lease version changes only with same original project/session/selection generation and unchanged native host identity. Validate before and after async reply. Preserve request id/hash and consumed monotonic state.','Keep confirm strict original context and one-shot. Do not replace original context to rearm confirm or assert current authority.','Expose historical original-request recheck distinctly from current-context authorization; historical terminal status permits bounded next coding PREPARE only via existing fresh ten-second terminal gate and current coding context/resource/native authority checks.','Preserve blocked session/selection/host changes, unknown or nonterminal original operations, private pending barrier, timeout, malformed/replayed replies and stale STATUS.','No API/DB bypass, no root ownCLI target fix, no contracts/migrations/main.js/pin/installedMu changes.','Tests use current changed production source and actual bound handlers; compile frontend and verify original management/coding suite; no real model calls in source work.'], 'actual_fixture_model_calls':0,'formal_increment':0,'root_live_process':'65164 and 66364 remain untouched during repair','next':'Independent source review, source-bound package, normal original-session revalidation; do not claim hotloaded fix.'}
new(OUT/'source-scope.json',scope);sr=ref(OUT/'source-scope.json')
resume={'schema':'researchos.current-chat-resume.v38','at':now,'checkpoint_revision':456,'ownership_revision':243,'head':cp['head'],'project_id':cp['project_id'],'current_step_id':'W05-99','goal_status':'ACTIVE','accepted_formal_cases':0,'required_formal_cases':42,'required_parent_tasks':22,'failure_records_preserved':len(cp['failure_counters']),'source_scope_ref':sr,'phone_ready':False,'next_command':'Repair bounded Desktop STATUS lease-context deadlock in isolated C worktree; independently review/build before normal activation. Continue M1 bounded scope analysis and new coding observer.'}
new(OUT/'RESUME.current.json',resume);rr=ref(OUT/'RESUME.current.json')
cp.update(revision=456,expected_previous_revision=455,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp456=rr,qualification_status_source_scope_ref=sr)
cp['evidence_index'].append({'kind':'ORIGINAL_QUALIFICATION_STATUS_CONTEXT_REPAIR_SCOPE','ref':rr,'formal_increment':0})
ow.update(revision=243,expected_previous_revision=242,updated_at=now,updated_by='codex:/root')
ow['special_paths']['qualification_status_repair']={'owner':scope['owner'],'ref':sr,'paths':source,'worktree':scope['worktree']}
ow['path_lease_transfers'].append({'at':now,'actor':'codex:/root','new_owner':scope['owner'],'new_subtask':'W05-99/original-qualification-status-context','new_worktree':scope['worktree'],'paths':source,'scope_ref':sr,'kind':'ISOLATED_SOURCE_LEASE'})
for p,n in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(h_p,'handoff.before.raw.md')]: (OUT/n).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode())
replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode())
replace(h_p,raw[h_p],('# Current verified continuation CP456\n\nRead `'+rr['path']+'` first. Exact4 Desktop original STATUS recovery repair registered. Original consumed request is never reconfirmed. M0 V6 source accepted uninstalled; formal0/42 all22 open.\n\n').encode()+raw[h_p])
assert s_p.read_bytes()==raw[s_p]
print(json.dumps({'checkpoint':456,'ownership':243,'scope':sr}))
