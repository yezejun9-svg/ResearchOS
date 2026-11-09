from pathlib import Path
import ast,json,hashlib,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent;N=P/'integration_codex/cli43-fresh-held2-r331-c4f309c5528f5d42be5e7eeb146a20aa'
checks=[];refs={}
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def ref(x):
 p=path(x);b=p.read_bytes();v={'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};refs[v['path']]=v;return v
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def verify(x):
 p=path(x['path']);v=ref(p);ck('pin '+str(p),v['sha256']==x['sha256'] and v['bytes']==x['bytes']);return p
def read(x):ref(x);return json.loads(path(x).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def job(r):
 j=r['job_cleanup'];return r['actual_exit']==0 and r['error'] is None and r['timed_out'] is False and r['resumed'] is True and all(j[x] is True for x in ['assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and j['active_processes_last_observed']==0 and j['errors']==[]
try:
 prep=read(N/'root-caller-preparation.json');s=read(verify(prep['scope_ref']));g=read(verify(prep['grant_ref']));caller=verify(prep['new_caller_ref']);old=verify(prep['old_caller_ref'])
 ck('new caller supplied pin',ref(caller)['sha256']=='bc191ffe9a2752cd8e339371cd8f96c1c992742d63aeda92f2cc29a42e5ef6ad')
 raw=caller.read_bytes();orig=old.read_bytes();t=ast.parse(raw);ot=ast.parse(orig)
 def constants(tree):return {n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['SCOPE_SHA','GRANT_SHA']}
 c=constants(t);oc=constants(ot);inverse=raw
 for k in ['SCOPE_SHA','GRANT_SHA']:ck('unique constant '+k,raw.count(c[k].encode())==1);inverse=inverse.replace(c[k].encode(),oc[k].encode(),1)
 ck('whole inverse exact bytes AST',inverse==orig and ast.dump(ast.parse(inverse))==ast.dump(ot))
 ck('two constants actual',c['SCOPE_SHA']==prep['scope_ref']['sha256'] and c['GRANT_SHA']==prep['grant_ref']['sha256'])
 ck('grant actual sealed status',g['schema']=='researchos.cli43-compiler-authorization.v1' and g['actor']=='codex:/root' and g['status']=='ROOT_REGISTERED_EXECUTION_AUTHORIZED' and g['actual_registration_completed'] is True)
 verify(g['scope_ref']);ck('scope exact relative',g['scope_ref']['path']==(N/'scope_registration.json').relative_to(R).as_posix())
 ck('grant complete binding equals scope',all(s[k]==v for k,v in g['binding'].items()))
 for mfpath in [N/'grant-driver.manifest.json',verify(g['registration_refs']['manifest'])]:
  mf=read(mfpath)
  for x in mf['entries']:verify(x)
 for section in ['registration_refs','authority_review_refs']:
  for x in g[section].values():verify(x)
 ck('ordered four copies',[x['canonical_path'] for x in g['canonical_copies']]==['execution/v2.4/'+n+'.json' for n in ['checkpoint','path_ownership','step_state','commands']])
 for x in g['canonical_copies']:ck('live equals grant '+x['canonical_path'],verify(x['ref']).read_bytes()==(R/x['canonical_path']).read_bytes());ref(R/x['canonical_path'])
 cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json');oldcp=read(N/'checkpoint.original.json');cut=read(N/'failure-origins.cut.json')
 ck('tuple331159509 and old502+7',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[331,159,509] and cp['failure_counters']==oldcp['failure_counters']+cut['origins'])
 prepared=read(N/'prepared_refs.json')
 for x in prepared['desired_refs']:
  q=verify(x);canonical=R/'execution/v2.4'/q.name.replace('.desired','');ck('current desired '+q.name,q.read_bytes()==canonical.read_bytes())
 inv=read(verify(g['registration_refs']['invocation']));ck('actual registration native0 complete',inv['actual_exit']==0 and inv['wrapper_error'] is None and job(inv['result']))
 regaudit=read(verify(g['registration_refs']['audit']));ck('actual sealed tuple',regaudit['after']==[331,159,509] and regaudit['actual_registration_exit']==0)
 pre=read(verify(g['prelaunch_evidence_ref']));ck('grant-final preflight',pre['source_round']=='grant-final' and pre['point_in_time_only'] is True)
 for x in pre['git']:
  out=verify(x['stdout_ref']).read_bytes();verify(x['stderr_ref']);ck('preflight owned '+x['kind'],x['actual_stage_native_exit']==0 and x['wrapper_error'] is None and job(x['result']))
  if x['kind']=='head':ck('saved HEAD',out.decode().strip()==s['source_commit'])
  if x['kind']=='status':ck('saved status13 elevenD',hashlib.sha256(out).hexdigest()==s['main_git']['status_sha256'] and len(out.splitlines())==13 and sum(v.startswith(b' D ') for v in out.splitlines())==11)
  if x['kind']=='index':ck('saved index empty',out==b'')
 for k in ['time_window_ref','admission_ref']:verify(pre[k])
 for x in g['runtime_observation_refs']:
  d=read(verify(x));ck('runtime pointtime not lifecycle',d['all_observed_inputs_pre_pinned'] is True and d['point_in_time_only'] is True and d['Python_lifecycle_proof'] is False)
 head=(R/'.git/HEAD').read_text().strip();hp=R/'.git'/head[5:] if head.startswith('ref: ') else None;ck('direct HEAD', (hp.read_text().strip() if hp else head)==s['source_commit'])
 for k in ['runner_ref','launcher_ref','authorization_gate_ref','debug_tree_helper_ref','python_ref']:verify(s[k])
 roots=[s[k] for k in ['new_output_root','new_wrapper_root','new_export_root']];outputs=[N/n for n in ['root-launch.intent.json','root-launch.stdout.raw','root-launch.stderr.raw','root-launch.invocation.json']]
 ck('three unused roots and four outputs absent',all(not path(x).exists() for x in roots+outputs))
 calls=[n for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' and n.func.attr=='run'];ck('one subprocess timeout3900',len(calls)==1 and any(k.arg=='timeout' and ast.literal_eval(k.value)==3900 for k in calls[0].keywords))
 ck('caps and environment unchanged',s['launch_limits']=={'outer_timeout_seconds':3600,'inner_soft_deadline_seconds':3300,'termination_cleanup_seconds':5} and set(s['public_environment'])<={'SystemRoot','WINDIR','ComSpec','PATH','PATHEXT'} and s['limits']['SDK_MODEL_Node_external_paid_private_calls']==0)
 ck('nullable and first cause preserved',b"result.returncode if result else None" in raw and b"'first_cause': error" in raw and b"secondary.append" in raw and b"'caller_OS_lifecycle_qualification': False" in raw)
 for x in prep['late_origins_outside_sealed_registration_cut_at_snapshot']:
  if 'ref' in x:verify(x['ref'])
  else:ck('third origin pending at snapshot accurately nullable',x['sealed_ref'] is None and x['actual_outer_exit'] is None and x['actual_native_exit'] is None and x['process_launched'] is False)
 verify(prep['late_origins_snapshot_ref']);ck('late1 snapshot retained observational',prep['registered_origin_count']==509 and prep['observed_origin_count_at_snapshot']==510 and len(prep['late_origins_outside_sealed_registration_cut_at_snapshot'])==1)
 verify(prep['preparer_ref']);ast.parse(path(prep['preparer_ref']['path']).read_bytes())
 ck('supplied preparation pin',ref(N/'root-caller-preparation.json')['sha256']=='2961c9b09dce7f48618d1c57c455c960a5692057ad5a731597efcf7ccd22f89a')
 ck('actual grant supplied pin',ref(path(prep['grant_ref']['path']))['sha256']=='124f16da796d16dd4a066d3b5ed8a00db8e744f7ca690d614cf46b14b8ac0f81')
 ck('ownership correction scope exact',s['instrumentation_ref']['sha256']=='ef10204d2fe2d59af7b59e1bdb7d4a375f3880ce4bdae999ea10ec1b30ed40ca' and s['instrumentation_helper_ref']['sha256']=='091e045b1313f318191128b065b0486a81ced3991a3fcade73fe557d583e2ccc' and s['instrumented_source_ref']['sha256']=='6dbcdcc0fc12b2bd00a69f724cbe1f9598761fe467157273c6709344b1a1f29e')
 previous=ref(P/'cli43_root_caller_static_independent_review_codex/99b041cc563449b78c26766068bcf208/review.json')
 closerprep=read(N/'completion-reader-preparation.json');closer=verify(closerprep['new_ref']);oldcloser=verify(closerprep['old_ref']);cr=closer.read_bytes();ast.parse(cr)
 ck('closer exact supplied pin',ref(closer)['sha256']=='9746d725c5441a410fd7d4b737c190c13542d9ffd5001c890a4739d9165c9c69')
 for e in reversed(closerprep['edits']):
  ck('closer unique exact delta '+e['new'],cr.count(e['new'].encode())==1);cr=cr.replace(e['new'].encode(),e['old'].encode(),1)
 ck('closer whole byte inverse',cr==oldcloser.read_bytes())
 source=closer.read_text(encoding='utf-8')
 ck('closer no target imports or calls',all(not isinstance(v,ast.Import) or all(z.name in ['argparse','hashlib','json','re','sys'] for z in v.names) for v in ast.walk(ast.parse(source))) and 'subprocess' not in source)
 ck('closer nullable result and qualification retained',"completed.get('actual_inner_native_exit') if completed is not None else None" in source and "'independent_qualification': 'PENDING'" in source and "'source_acceptance': False" in source and "'separately_captured_outer_native_raw': False" in source)
 snap=read(verify(prep['late_origins_snapshot_ref']));ck('current snapshot tuple and pending1',snap['actual_registered_tuple']==[331,159,509] and snap['known_observed_origin_count']==510 and len(snap['outside_fixed_cut'])==1)
 for row in snap['outside_fixed_cut']:ck('late original payload complete',read(verify(row['ref']))==row['original_payload'] and row['original_payload']['actual_native_exit'] is None and row['original_payload']['outer_exit'] is None)
 for n in ['RESUME.authorized.before-caller.snapshot.manifest.json']:
  sm=read(N/n)
  for x in sm['entries']:verify(x)
 verify(snap['metadata_tool_observations_ref'])
 for x in list(refs.values()):
  now=path(x['path']).read_bytes();ck('after same '+x['path'],hashlib.sha256(now).hexdigest()==x['sha256'] and len(now)==x['bytes'])
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'reused_previous_caller_review_ref':previous,'scope_ref':prep['scope_ref'],'grant_ref':prep['grant_ref'],'caller_ref':prep['new_caller_ref'],'target_executions':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values()),'target_executions':0});raise
