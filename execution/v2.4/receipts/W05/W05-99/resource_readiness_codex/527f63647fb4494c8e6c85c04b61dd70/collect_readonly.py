from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,os
ROOT=Path('D:/作品集/ResearchOS/research-os');OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p)}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(n,d):
 with (OUT/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
cp=read(ROOT/'execution/v2.4/checkpoint.json');state=read(ROOT/'execution/v2.4/step_state.json')
canonical={n:sha(ROOT/n) for n in ['execution/v2.4/checkpoint.json','execution/v2.4/step_state.json','execution/v2.4/path_ownership.json','execution/v2.4/commands.json']}
save('canonical-before.json',canonical)
selected=[r for r in state['steps'] if r['id'] in ('W13-03','W14-01')]
save('checkpoint-selected.json',{'checkpoint_ref':ref(ROOT/'execution/v2.4/checkpoint.json'),'revision':cp['revision'],'blocked_resources':cp['blocked_resources'],'blocked_steps':cp['blocked_steps'],'selected_steps':selected})
sources=['execution/v2.4/receipts/W13/W13-03/screen_reader_observation_codex.json','execution/v2.4/receipts/W13/W13-03/screen-reader-summary-20261005T173436Z.md',
 'execution/v2.4/receipts/W13/W13-03/workspace_review_round2_interruption_codex.json','execution/v2.4/receipts/W13/W13-03/progress_round7_codex.json',
 'execution/v2.4/receipts/W13/W13-03/independent_permission_observation_round5_codex.json','execution/v2.4/receipts/W14/W14-01/live_qualification_blocked_codex.json',
 'execution/v2.4/receipts/W14/W14-01/runtime_integration_recovery_codex.json','execution/v2.4/receipts/W14/W14-01/doctor_candidate_preflight_codex.json',
 'tests/ui/w1303/screen_reader_run.py','execution/toolchains/locked.json']
save('input-refs.json',[ref(ROOT/n) for n in sources])
locked=read(ROOT/'execution/toolchains/locked.json')['tools'];python=locked['python']['path']
def run(stem,argv):
 start=datetime.now(timezone.utc).isoformat();p=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=60,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 for suffix,raw in [('stdout',p.stdout),('stderr',p.stderr)]:
  with (OUT/(stem+'.'+suffix)).open('xb') as f:f.write(raw)
 receipt={'actualargv':argv,'cwd':str(ROOT),'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':p.returncode,'measurement_mode':'READ_ONLY_RESOURCE_METADATA','stdout_ref':ref(OUT/(stem+'.stdout')),'stderr_ref':ref(OUT/(stem+'.stderr'))}
 save(stem+'.invocation.json',receipt);return p
probe=run('availability',[python,'-B','-X','utf8',str(OUT/'probe.py')]);assert probe.returncode==0
observed=json.loads(probe.stdout.decode('utf-8'));save('availability.json',observed)
for name in ['python','node']:
 tool=locked[name];assert sha(Path(tool['path']))==tool['sha256'];run(name+'-version',[tool['path'],*tool['version_argv']])
signature=run('nvda-signature',['powershell.exe','-NoProfile','-NonInteractive','-Command',"$s=Get-AuthenticodeSignature -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/nvda-w1303/nvda_2026.2.exe'; [pscustomobject]@{Status=[string]$s.Status;SignerSubject=$s.SignerCertificate.Subject;Thumbprint=$s.SignerCertificate.Thumbprint}|ConvertTo-Json -Compress"])
save('canonical-after.json',{n:sha(ROOT/n) for n in canonical})
summary={'status':'READ_ONLY_RESOURCE_READINESS_NOT_ACCEPTANCE','actor':'codex:/root/sources_parent_impl','checkpoint_revision_observed':cp['revision'],'created_at':datetime.now(timezone.utc).isoformat(),'availability_ref':ref(OUT/'availability.json'),
 'actual_invocation_refs':[ref(OUT/(n+'.invocation.json')) for n in ['availability','python-version','node-version','nvda-signature']],
 'findings':[
 {'branch':'W13-03 physical screen reader','historical_block':'OS foreground ownership; 8 attempts/0PASS, not NVDA absence','current_observation':'See actual assets, Authenticode and module metadata. No target GUI was launched, so foreground access today remains UNVERIFIED; a different current foreground PID does not prove the blocker resolved.','next':'No download/install is necessary if pinned existing NVDA hash and portable binary are present. Root may prepare a separately authorized bounded physical observation only after a legitimate foreground/session state change; never substitute DOM/ARIA evidence or repeat the old focus workaround.'},
 {'branch':'W13-03 independent workspace review','historical_block':'Actual second review stopped by platform cybersecurity screening; no independent final acceptance','current_observation':'Later permission-observation PASS_IN_SCOPE explicitly excludes workspace security acceptance. Tool presence does not remove platform disposition; this task does not retry or reconstruct the rejected review.','next':'Keep this gate BLOCKED pending legitimate platform disposition/external change. Other permitted UI/CLI branches can continue; do not route around the rejection.'},
 {'branch':'W13 GUI evidence','historical_block':'632 actual Electron checks across six stages were already PASS at recorded inputs, including51 accessibility checks; full card remained PARTIAL','current_observation':'Existing original GUI evidence is present; current availability is measured, no new GUI result or old source-currentness assumed. Screen reader and independent workspace acceptance remain distinct.','next':'After approved input changes, use existing source fingerprint/cache eligibility rules to identify affected stages, rather than rerunning unchanged observations or claiming old632 as current.'},
 {'branch':'W14-01 fixed Mu/provider','historical_block':'One live deepseek-flash request ended UNKNOWN; later /models401; original inference HTTP body/status not preserved','current_observation':'Built Mu worker/SDK asset availability and process credential presence/hash are measured only. Previous missing-runtime explanation was already superseded; no evidence here reconciles UNKNOWN or proves usable/different credentials.','next':'Need an existing authoritative outcome/usage record for the exact old dispatch and valid authorization for the fixed model endpoint before any new live execution. New credential or a later401 cannot settle old effect/cost. No provider probe/retry performed.'},
 {'branch':'W14 frozen doctor issue','historical_block':'Original unmodified isolated doctor issue was reserved for a real product-agent task','current_observation':'New W05 doctor work is construction work and cannot be relabelled as W14 product-agent LIVE coding. Existing contract requires freezing a still-unresolved real issue immediately before the product run.','next':'When resources and outcome are legitimately resolved, re-evaluate current issue availability and freeze an actual unresolved user-visible issue under the unchanged first_real_coding_task_policy; do not reintroduce a fixed bug.'}],
 'canonical_changed_during_readonly':[n for n,h in canonical.items() if sha(ROOT/n)!=h],
 'limits':{'product_or_source_edits':0,'canonical_writes':0,'failure_counter_changes_by_this_task':0,'provider_calls':0,'GUI_processes_started':0,'new_tool_installs_or_execution':0,'private_DB_DPAPI_protected_labels_read':False,'other_project_configuration_read':False,'formal_acceptance':0,'screen_reader_current_pass_claimed':False}}
save('summary.json',summary);print(json.dumps({'summary_ref':ref(OUT/'summary.json'),'availability_exit':probe.returncode,'signature_exit':signature.returncode},ensure_ascii=False))
