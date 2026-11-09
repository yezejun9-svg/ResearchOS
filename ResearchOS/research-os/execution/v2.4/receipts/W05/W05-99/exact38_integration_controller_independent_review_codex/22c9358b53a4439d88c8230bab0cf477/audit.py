import pathlib,json,hashlib,ast
O=pathlib.Path(__file__).parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_preparation_codex/7b236231f51d42319f8c21c0db715b01'
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321'
T=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/parallel-source-and-go3-r320'
checks=[];readrefs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=pathlib.Path(p);p=p if p.is_absolute() else R/p
 b=p.read_bytes();readrefs[str(p)]={'path':str(p),'sha256':sha(b),'bytes':len(b)};return b
def check(n,v,d=None):checks.append({'name':n,'passed':bool(v),'details':d})
def verify(ref):
 b=read(ref['path']);check('ref:'+ref['path'],sha(b)==ref['sha256'] and len(b)==ref['bytes']);return b
def load(p):return json.loads(read(p))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
pins=[(P/'integrate_exact38.py','7ca8b3dcdfdfc4135da349bacefba7eb41ba18c425db43abb3e51df0fc2e155c'),(P/'handoff.json','6599312aca492d4830d8fb8013f3b0f4d7e8482b66f13bbea46e983a08ac87b7'),(P/'manifest.json','c4f68af65250d5f3a0500b8568ee4a4b9a0a972ed17212b0c95d361db93cb5c1'),(S/'scope_registration.json','b3412116292c8e30d7e29f546ac399ee9f25c4bf5f6f39c0bb62ed16142fa30b'),(S/'scope-freeze-audit.json','7ae456fd62c75b008ab2263da5a14998be1e6977fe718c208f8296a54bbeaa4f')]
for p,h in pins:check('pin:'+p.name,sha(read(p))==h)
scope=load(S/'scope_registration.json');mf=load(P/'manifest.json');check('manifest63',mf['count']==len(mf['entries'])==63)
for x in mf['entries']:verify(x)
def walk(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=set(v):verify(v)
  else:
   for value in v.values():walk(value)
 elif isinstance(v,list):
  for value in v:walk(value)
walk(scope)
protected=json.loads(verify(scope['protected_ref']));check('protected5172',len(protected)==5172)
for x in protected:verify(x)
runtime=json.loads(verify(scope['runtime_resources_ref']));check('runtime1211',len(runtime['files'])==1211)
for x in runtime['files']:verify(x)
exact=json.loads(verify(scope['exact38_ref']));review=json.loads(verify(scope['root14_review_ref']));prior_map=json.loads(verify(review['source38_final_hashes_ref']))
prior={x['relative_path']:x for x in prior_map}
check('independent-exact38-order',[x['path'] for x in exact]==review['minimum_future_integration_scope']['exact_unique_paths'])
for row in exact:
 old=prior[row['path']];check('independent-after:'+row['path'],row['after_sha256']==old['sha256'] and row['after_bytes']==old['bytes'] and row['after_git']['mode']==old['mode'] and row['after_git']['blob']==old['git_blob'])
 if row['before_worktree']:verify(row['before_worktree'])
 else:check('new-path-absent:'+row['path'],not (R/row['path']).exists())
def tree(p):
 out={}
 for line in read(p).decode('utf-8').splitlines():
  meta,name=line.split('\t',1);mode,kind,blob=meta.split();out[name]={'mode':mode,'kind':kind,'blob':blob}
 return out
before=tree(P/'tree-before.stdout.raw');after=tree(P/'tree-after.stdout.raw')
actualdelta=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))
check('complete-tree-delta-only38',actualdelta==[x['path'] for x in exact])
for row in exact:check('tree-modes-and-blobs:'+row['path'],before.get(row['path'])==row['before_git'] and after.get(row['path'])==row['after_git'])
for i in [1,2,3]:
 parents=read(P/f'parent-{i}.stdout.raw').decode().split();check(f'chain-parent-{i}',parents==[scope['source_chain'][i],scope['source_chain'][i-1]])
 delta=read(P/f'delta-{i}.stdout.raw').decode().splitlines();check(f'chain-delta-{i}',len(delta)==[38,2,1][i-1] and set(delta)<=set(actualdelta))
for p in scope['old_deleted_paths']:check('old-deletion:'+p,not (R/p).exists())
cp=load(R/'execution/v2.4/checkpoint.json');ow=load(R/'execution/v2.4/path_ownership.json');check('current320148417',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[320,148,417])
for n in ['checkpoint','path_ownership','step_state','commands']:
 raw=read(R/f'execution/v2.4/{n}.json');check('preparation-canonical-current:'+n,raw==read(P/f'canonical.before.{n}.json'));(O/f'canonical-before-{n}.json').write_bytes(raw)
controller=read(P/'integrate_exact38.py');syntax=ast.parse(controller.decode('utf-8'));check('AST-valid-no-assert',not any(isinstance(n,ast.Assert) for n in ast.walk(syntax)))
source=controller.decode('utf-8');check('fixed-56-git-bound',3*3+6+1+1+38+1==scope['maximum_owned_Git_invocations'])
for token in ["'merge','--ff-only','--no-autostash','--no-edit'",'GIT_NO_REPLACE_OBJECTS',"'core.hooksPath='",'GIT_CONFIG_NOSYSTEM',"'filter.','include.','includeif.'",'runtime_snapshot(\'runtime.precommit\')','canonical_protected();require(not list(hooks.iterdir())','sys.flags.no_site','sys.flags.utf8_mode']:
 check('required-static-token:'+token,token in source)
# Actual r320 registration output SHAPES (read only) against consumer access keys.
actual={n:load(T/n) for n in ['registration-audit.json','invocation.json','canonical-write.intent.json','canonical-write.verified.json','manifest.json']}
required={'registration-audit.json':['actor','actual_registration_exit','before','after','invocation_ref','intent_ref','verified_ref'],'invocation.json':['actor','actual_exit','automatic_retry','counter_reset','review_ref','runner_sha256','wrapper_sha256','stdout_sha256','stderr_sha256'],'canonical-write.intent.json':['Main_head','transition','metadata','unchanged'],'canonical-write.verified.json':['checkpoint','ownership','failure_origins','intent_ref'],'manifest.json':['entries','count']}
for n,keys in required.items():check('registration-shape:'+n,all(k in actual[n] for k in keys))
intent=actual['canonical-write.intent.json'];check('metadata-order',[x['path'] for x in intent['metadata']]==['execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json'])
check('unchanged-order',[x['path'] for x in intent['unchanged']]==['execution/v2.4/step_state.json','execution/v2.4/commands.json'])
for x in intent['metadata']:
 check('desired/original-refs',all(k in x for k in ['original_ref','desired_ref']));done=load(T/('canonical-write.'+pathlib.Path(x['path']).stem+'.done.json'));check('done-shape','sha256' in done)
for n in ['register.py','run.py','seal.v2.py','prepared_refs.json','audit.json']:read(T/n)
out=pathlib.Path(scope['new_output_root']);preconditions={'output_parent_exists':out.parent.exists(),'operation_leaf_exists':out.exists(),'prelaunch_parent_creation_required':not out.parent.exists(),'actual_future_grant_present':False,'actual_integration_executed':False}
for p in [P/'integrate_exact38.py',S/'scope_registration.json',S/'scope-freeze-audit.json',P/'grant.contract.json',P/'forward-only-recovery.json']:
 target=O/('input-'+p.name);target.write_bytes(read(p))
save('read_audit.json',{'schema':'researchos.exact38-controller-independent-static-audit.v1','checks':checks,'failed_checks':[c for c in checks if not c['passed']],'reads':list(readrefs.values()),'preconditions':preconditions,'registrar_shape_reference':str(T),'runtime_lifecycle_claim':False,'controller_or_helper_imported':False,'native_executions':0})
print(json.dumps({'checks':len(checks),'failed_checks':[c for c in checks if not c['passed']],'read_refs':len(readrefs),'preconditions':preconditions},ensure_ascii=False))
