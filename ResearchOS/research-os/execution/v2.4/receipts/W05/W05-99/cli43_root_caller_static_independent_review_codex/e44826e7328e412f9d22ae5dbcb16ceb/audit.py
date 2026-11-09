from pathlib import Path
import ast,hashlib,json,traceback
R=Path('D:/作品集/ResearchOS/research-os'); P=R/'execution/v2.4/receipts/W05/W05-99'
N=P/'integration_codex/cli43-fresh-held2-r327-efa7776ec48e4a7abaa92ce85eb0dace'
OLD=P/'integration_codex/cli43-fresh-held2-r326-477e329b79944cb0b33f9ead24811760'
O=P/'cli43_root_caller_static_independent_review_codex/e44826e7328e412f9d22ae5dbcb16ceb'
checks=[]; refs=[]
def path(v):
 p=Path(v); return p if p.is_absolute() else R/p
def pin(p):
 p=path(p); b=p.read_bytes(); return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(label,ok):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok: raise ValueError(label)
def verify(r):
 a=pin(r['path']); check('pin '+r['path'],a['sha256']==r['sha256'] and a['bytes']==r['bytes']); refs.append(r); return path(r['path'])
def read(p):return json.loads(path(p).read_bytes())
def save(name,v):
 with (O/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
try:
 caller=N/'root-launch-once.v2.py'; scopepath=N/'scope_registration.json'
 check('caller supplied SHA',pin(caller)['sha256']=='665031b99edc5031ebd5e40a80abb1c09bc39a33ab623d8b4d099823240f60dc')
 check('scope supplied SHA',pin(scopepath)['sha256']=='320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137')
 old=(OLD/'root-launch-once.v2.py').read_bytes(); raw=caller.read_bytes()
 inv=raw.replace(b'320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137',b'68a0986a0bfcf39948ab2f696e33ef9ec05b39bb5a23f8787f92bf0129fe3566').replace(b'4b7ba306f378ef9a736619e36ec70e5a1c5d614481c069dedab01efdad841ac8',b'93329e2cd46e334043ded2000cf196c2fd0273be6454954720cae830063eac62')
 check('wholebyte inverse only scope/grant constants',inv==old)
 tree=ast.parse(raw.decode('utf-8')); calls=[x for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id=='subprocess' and x.func.attr=='run']
 check('one subprocess run',len(calls)==1); check('caller timeout3900',any(k.arg=='timeout' and isinstance(k.value,ast.Constant) and k.value.value==3900 for k in calls[0].keywords))
 s=read(scopepath); G=Path(s['new_authorization_root']); gp=G/'authorization.execute.json'; g=read(gp)
 check('grant supplied SHA',pin(gp)['sha256']=='4b7ba306f378ef9a736619e36ec70e5a1c5d614481c069dedab01efdad841ac8')
 check('registered actual grant',g['actual_registration_completed'] is True and g['status']=='ROOT_REGISTERED_EXECUTION_AUTHORIZED' and g['actor']=='codex:/root')
 verify(g['scope_ref']); check('grant scope path actual',path(g['scope_ref']['path'])==scopepath)
 for k,v in g['binding'].items():check('binding '+k,k in s and s[k]==v)
 check('actual expected tuple',s['expected_registration']==[327,155,459]); check('two exact cases',s['ordered_cases']==['real-existing-open-readonly','real-existing-self-send'])
 check('inner bounds unchanged',s['launch_limits']=={'outer_timeout_seconds':3600,'inner_soft_deadline_seconds':3300,'termination_cleanup_seconds':5})
 check('public environment exact keys',set(s['public_environment'])=={'SystemRoot','WINDIR','ComSpec','PATH','PATHEXT'})
 check('prohibited external calls0',s['limits']['SDK_MODEL_Node_external_paid_private_calls']==0)
 for k in ['launcher_ref','runner_ref','authorization_gate_ref','python_ref','toolchain_lock_ref']:verify(s[k])
 for r in g['registration_refs'].values():verify(r)
 for r in g['authority_review_refs'].values():verify(r)
 check('4 canonical copies',len(g['canonical_copies'])==4)
 for row in g['canonical_copies']:
  cp=verify(row['ref']); live=path(row['canonical_path']); check('live canonical '+row['canonical_path'],cp.read_bytes()==live.read_bytes())
 gm=read(G/'manifest.json'); check('grant manifest cardinality',gm['count']==len(gm['entries']) and gm['excluded_only_self'] is True)
 for r in gm['entries']:verify(r)
 pre=read(verify(g['prelaunch_evidence_ref'])); check('3 prelaunch git records',len(pre['git'])==3)
 for x in pre['git']:
  r=x['result']; j=r['job_cleanup']; check('owned prelaunch '+x['kind'],r['actual_exit']==0 and not r['timed_out'] and r['error'] is None and x['wrapper_error'] is None and x['actual_stage_native_exit']==0 and r['resumed'] is True and all(j[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and j['errors']==[])
  out=verify(x['stdout_ref']); verify(x['stderr_ref'])
  if x['kind']=='head':check('prelaunch head',out.read_text().strip()==s['source_commit'])
  elif x['kind']=='status':check('prelaunch status',pin(out)['sha256']==s['main_git']['status_sha256'] and pin(out)['bytes']==s['main_git']['status_bytes'])
  elif x['kind']=='index':check('prelaunch empty index',out.read_bytes()==b'')
 complete=read(G/'grant.completed.json'); check('grant completed no launch',complete['launcher_executions']==0 and complete['source_acceptance'] is False and complete['formal_increment']==0 and complete['point_in_time_not_lifecycle'] is True); verify(complete['grant_ref'])
 for k in ['new_output_root','new_wrapper_root','new_export_root']:check('absent '+k,not Path(s[k]).exists())
 for name in ['root-launch.intent.json','root-launch.stdout.raw','root-launch.stderr.raw','root-launch.invocation.json']:check('absent '+name,not (N/name).exists())

 dm=read(N/'grant-driver.manifest.json');check('grant driver manifest supplied SHA',pin(N/'grant-driver.manifest.json')['sha256']=='bd183d7befd9defa002adb97d75391060d67a430363902d62368e219bb25c5e2')
 for entry in dm['entries']:verify(entry)
 cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json');oldcp=read(N/'checkpoint.original.json');cut=read(N/'failure-origins.cut.json')
 check('live tuple327155459',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[327,155,459]);check('old450 complete plus9',cp['failure_counters']==oldcp['failure_counters']+cut['origins'] and len(oldcp['failure_counters'])==450 and len(cut['origins'])==9)
 headfile=R/'.git/HEAD';head=headfile.read_text(encoding='utf-8').strip();headactual=(R/'.git'/head[5:]).read_text(encoding='utf-8').strip() if head.startswith('ref: ') else head
 check('direct Git HEAD no native',headactual==s['source_commit']==cp['head'])
 prep=read(N/'root-caller-preparation.json')
 for key in ['old_caller_ref','new_caller_ref','scope_ref','grant_ref']:verify(prep[key])
 check('preparation point snapshot not rewritten',prep['registered_origin_count']==459 and prep['observed_origin_count']==462 and prep['launcher_executed'] is False)
 prior=P/'cli43_root_caller_static_independent_review_codex/c92ef1c0c4c04651b3e8ce74f45bc28e/review.json'; check('reused prior review SHA',pin(prior)['sha256']=='95b743ab85492fe670278f5e501d2544a1c5251a3b81cb8e15b698d1e024c57a')
 save('audit.json',{'checks':checks,'checked_ref_rows':refs,'actual_target_execution':False,'full_resource_tree_rehashed':False,'new_failure_origins':[pin(O/'failure-origin.3dbc41.json')]})
 review={'schema':'researchos.cli43-root-caller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_ONCE_ONLY_PINNED_LAUNCHER_CALL','requested_changes':[],'caller_ref':pin(caller),'scope_ref':pin(scopepath),'grant_ref':pin(gp),'prior_review_ref':pin(prior),'scope_review_ref':g['authority_review_refs']['runner_review_ref'],'registration_review_ref':g['authority_review_refs']['registration_review_ref'],'grant_manifest_ref':pin(G/'manifest.json'),'preparation_ref':pin(N/'root-caller-preparation.json'),'audit_ref':pin(O/'audit.json'),'whole_byte_inverse_equal':True,'changed_constants_only':['SCOPE_SHA','GRANT_SHA'],'canonical_copies_verified_live':g['canonical_copies'],'actual_registration':[327,155,459],'checks_passed':len(checks),'limits':'One pinned Python -I -S -X utf8 subprocess. Caller3900 does not change inner3300/launcher3600/cleanup5. Caller retains nullable native exit, first cause, secondary errors and raw refs; no caller Job or OS lifecycle qualification. Pre-pin/intent errors remain before launch with ordinary stderr, not fabricated child invocation.','reuse':'Prior caller95b743 plus immediate r326 caller55bf, r327 boundbeef/registration42312 reused. No full34311 backing-tree rehash, fresh graph or complete loaded-OS claim; inner gate must revalidate at actual launch.','pending_note':'Preparation point-time459/462 retained. Later Root reports late7/observed466 including own3dbc41; fixed459 cut/grant unchanged. No inferred native failure for NULL network/tool diagnostics.','actual_caller_execution':False,'actual_product_execution':False,'new_failure_origins':[pin(O/'failure-origin.3dbc41.json')],'source_acceptance':False,'formal_increment':0,'status':'STOPPED'}
 save('review.json',review)
 print(json.dumps({'checks':len(checks),'review':pin(O/'review.json')},ensure_ascii=True))
except BaseException:
 save('audit.failure.json',{'traceback':traceback.format_exc(),'checks':checks,'actual_target_execution':False}); raise
