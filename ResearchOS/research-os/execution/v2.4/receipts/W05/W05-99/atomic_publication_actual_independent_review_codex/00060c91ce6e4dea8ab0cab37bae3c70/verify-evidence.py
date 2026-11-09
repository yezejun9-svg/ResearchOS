import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
B=D.parent.parent
A=B/'integration_codex/controller-atomic-publication-root-2e926de963bc46f2'
C=B/'integration_codex/native-positive-controller-config-v2-root-0da7b5a0b3f84a13'
refs={}
def normalized(r):
 return dict(path=str(Path(r['path'])),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes'])
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def add(r):
 r=normalized(r);k=r['path'].casefold()
 assert k not in refs or refs[k]==r,('conflicting pin',r['path'])
 refs[k]=r
def walk(x):
 if isinstance(x,dict):
  if all(k in x for k in ('path','sha256','bytes')):add(x)
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
def read(p):
 add(pin(p));return json.loads(Path(p).read_bytes())
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
for folder in (A,C):
 for p in folder.iterdir():
  assert p.is_file() and not p.is_symlink()
  add(pin(p))
actual=read(A/'validation.closed.json')
assert pin(A/'validation.closed.json')['sha256']=='5b353a25e8746223809d5536978dd6750dd04648ab34ae237e932b3767c18a52'
inner=read(A/'inner.closed.json');inv=read(A/'atomic-cases.invocation.json')
source=read(A/'source-input.reviewed.json')
rio=read(A/'original-tool-io.json')
walk(actual);walk(inner);walk(inv);walk(source)
runtime={normalized(r)['path'].casefold():normalized(r) for r in actual['runtime_refs']}
assert len(runtime)==101
guard_counts=[]
for n in ('inner-source-guard.cleanup.actual.json','outer-source-guard.cleanup.actual.json'):
 g=read(A/n);walk(g)
 assert g['closed'] and g['verification']=='PASSED' and not g['errors'] and not g['failure'] and g['retained_handles_count']==0
 assert len(g['entries'])==101
 entries={normalized(e)['path'].casefold():normalized(e) for e in g['entries']}
 assert entries==runtime
 assert all(e['verified'] and e['final_path_match'] and e['closed'] for e in g['entries'])
 guard_counts.append(len(entries))
assert inv['actual_native_exit']==0 and inv['result']['actual_exit']==0
result=inv['result'];job=result['job_cleanup']
assert result['error'] is None and not result['timed_out']
assert job['job_idle_confirmed'] and job['primary_exit_confirmed'] and job['handles_closed']
assert job['active_processes_last_observed']==0 and not job['errors'] and not job['termination_requested']
assert rio['result']['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in rio['result']['output']
assert inner['cases_passed']==['complete-publication','duplicate-no-clobber','rename-failure-cleanup','partial-ready-deferral']
e=inner['case_evidence']
assert e[0]['prepublish_missing_observations']==20 and e[0]['partial_observations']==0
assert e[0]['final_ref']==e[1]['final_unchanged_ref']
assert not e[2]['final_exists'] and e[2]['remaining_temp_files']==[]
assert (e[3]['incomplete_phase'],e[3]['complete_phase'])==('running','release')
assert json.loads(Path(e[0]['final_ref']['path']).read_bytes())=={'content':'public-'*300000}
assert Path(e[1]['rename_time_winner_unchanged_ref']['path']).read_bytes()==b'{"winner":"other-public-writer"}'
assert Path(e[3]['ready_ref']['path']).read_bytes()==b'{"public":true}'
scratch=Path(e[0]['final_ref']['path']).parent
assert not (scratch/'rejected.json').exists()
assert not list(scratch.glob('*.pending'))
cfg=read(C/'controller.public.config.json');prep=read(C/'controller-config.prepared.json')
assert pin(C/'controller.public.config.json')['sha256']=='9d561a6be761ebb2e61bb72a7bee22b07e188cee3877105827f4ca48ba6928fc'
assert pin(C/'controller-config.prepared.json')['sha256']=='cdfd9d634ed641f8f781af9a13f3e1f2c665ad7c056093807ae32186448072a5'
walk(cfg);walk(prep)
hc=read(cfg['HarnessConfig']['path']);walk(hc)
inventory=read(cfg['CompilerInventory']['path'])
frozen={normalized(r)['path'].casefold():normalized(r) for r in cfg['FrozenInputs']}
assert len(cfg['FrozenInputs'])==len(frozen)==4083
g=read(C/'config-input-source-guard.cleanup.actual.json');walk(g)
assert g['closed'] and g['verification']=='PASSED' and not g['errors'] and not g['failure'] and g['retained_handles_count']==0
assert len(g['entries'])==4083
assert {normalized(e)['path'].casefold():normalized(e) for e in g['entries']}==frozen
assert all(e['verified'] and e['final_path_match'] and e['closed'] for e in g['entries'])
sets={}
for key in ('build_inputs','product_inventory','compiler_tool_refs'):
 values=inventory[key];sets[key]=len(values)
 for r in values:assert frozen[normalized(r)['path'].casefold()]==normalized(r)
assert sets==dict(build_inputs=3793,product_inventory=599,compiler_tool_refs=8)
assert frozen[normalized(inventory['GoRef'])['path'].casefold()]==normalized(inventory['GoRef'])
harness_keys=('RootProgram','ControlProgram','BackupProgram','EnrollmentProgram','PythonProgram','BrokerSource','PrivateStdinHelper')
for key in harness_keys:assert frozen[normalized(hc[key])['path'].casefold()]==normalized(hc[key])
for key,value in cfg.items():
 if isinstance(value,dict) and 'sha256' in value:assert frozen[normalized(value)['path'].casefold()]==normalized(value)
assert hc['Case']=='positive-replay' and hc['CaseID']=='73df768bc70b4f64'
assert not Path(cfg['ControllerDirectory']).exists() and not Path(hc['OutputDirectory']).exists()
assert len(cfg['Environment'])==20
assert cfg['Environment']['GOPROXY']==cfg['Environment']['GOSUMDB']==cfg['Environment']['GOWORK']=='off'
assert cfg['Environment']['GOTOOLCHAIN']=='local'
assert not any(any(s in k.upper() for s in ('TOKEN','SECRET','PASSWORD','API_KEY')) for k in cfg['Environment'])
assert actual['canonical_unchanged_refs']==prep['canonical_unchanged_refs']
cio=read(C/'original-tool-io.json')
assert cio['result']['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in cio['result']['output']
assert not prep['formal_acceptance'] and prep['native_cases_executed']==0
for key in ('Owner_credential_reads','private_key_reads','issuer_signatures','original_trial_DB_writes','provider_requests'):assert prep[key]==0
for r in list(refs.values()):assert pin(r['path'])==r,('pin drift',r['path'])
out=dict(schema='researchos.atomic-publication-and-positive-config-independent-evidence.v1',base_refs=list(refs.values()),atomic_actual=dict(cases=inner['cases_passed'],inner_outer_guard_counts=guard_counts,result=result,case_evidence=e,original_outer_exit=rio['result']['exit_code'],limitations=['Controlled fsync gate observed 20 prepublication missing reads; not a universal schedule proof.','Rename race injects winner after precheck and exercises actual Windows os.rename refusal.','Partial ready case tests syntactic phase transition only; no Root approval or release consumed.','Runtime guards pin listed Python files; this is not complete imported-bytecode runtime closure.']),public_configuration=dict(frozen_input_count=4083,coverage=sets,GoRef_explicitly_frozen=True,harness_refs_covered=list(harness_keys),pyc_refs_count=sum(r['path'].lower().endswith('.pyc') for r in frozen.values()),guard_entries_verified_closed=4083,controller_directory_exists=False,fixture_output_exists=False,environment_keys=sorted(cfg['Environment']),config_ref=pin(C/'controller.public.config.json'),prepared_ref=pin(C/'controller-config.prepared.json'),limitations=['Preparation and pure context/guard validation only.','No future native child Python import closure is claimed.','Concrete Root launch and each approval/signature require separate review.']),canonical_refs=prep['canonical_unchanged_refs'],all_current_pins_match=True,new_mechanical_errors=0,authority='NONE',formal_acceptance=False)
r=save('evidence.json',out)
print(json.dumps(dict(evidence_ref=r,base_refs=len(refs),atomic_cases=4,atomic_guards=guard_counts,config_guard=4083,GoRef_covered=True,pyc_refs=out['public_configuration']['pyc_refs_count'],drift=0,new_mechanical_errors=0)))

