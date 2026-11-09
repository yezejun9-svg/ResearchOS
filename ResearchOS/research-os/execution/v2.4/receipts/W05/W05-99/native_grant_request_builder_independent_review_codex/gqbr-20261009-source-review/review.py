import sys
sys.dont_write_bytecode=True
import ast,copy,collections,hashlib,json,ntpath,os,re
from pathlib import Path
N=Path(__file__).resolve().parent
B=N.parent.parent
C=B/'native_grant_archive_request_builder_source_codex/gqb-1a11ee4f162766098eda3028b0679f2'
D=B/'integration_codex/native-cleanup-controller-source-root-1791517434000'
checks=[];inputs={}
def ck(name,value):
 checks.append({'name':name,'pass':bool(value)})
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes()
 return {'path':str(p),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def verify(v):
 actual=pin(v['path']);expected={k:v[k] for k in ('path','sha256','bytes')}
 expected['path']=str(Path(expected['path']).resolve())
 expected['sha256']='sha256:'+expected['sha256'].removeprefix('sha256:')
 ck('pin:'+expected['path'],actual==expected);inputs[expected['path']]=expected
 return actual
def fixed(p,h,n):return verify({'path':str(p),'sha256':h,'bytes':n})
def add(p):return verify(pin(p))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
fixed(C/'HDF.json','50981bdb61b1a0cdd0c9ce183f4bd464ffcdf1817c2025478d5b531bd41508c6',4119)
fixed(C/'MF.json','ddaba804b9bc820952aa1c26cf347bc34801f4ac91ba308ecafa3e4d9e7f4731',4949)
hdf=read(C/'HDF.json');mf=read(C/'MF.json')
ck('fourteen-members',mf['member_count']==len(mf['members'])==14)
for v in mf['members']:verify(v)
for k,v in hdf.items():
 if isinstance(v,dict) and set(('path','sha256','bytes'))<=set(v):verify(v)
prov=read(C/'source-provenance.json')
verify(prov['config_ref']);verify(prov['helper_ref'])
checksmeta=read(C/'final-source-checks.json');verify(checksmeta['control_source_ref'])
cfg=read(prov['config_ref']['path']);verify(cfg['HarnessConfig']);hc=read(cfg['HarnessConfig']['path'])
fixed(D/'controller-config.prepared.json','8a25b52e2f2500e175684c059df427b320c327457e774a2b6a1d4bb274078162',4954)
canon=read(D/'controller-config.prepared.json')['canonical_unchanged_refs']
ck('four-canonical',len(canon)==4)
for v in canon:verify(v)
ck('canonical-checkpoint364',read(canon[0]['path'])['revision']==364)
raw=Path(hdf['source_ref']['path']).read_bytes();source=raw.decode('utf-8')
helper=Path(hdf['helper_ref']['path']).read_text(encoding='utf-8')
tree=ast.parse(source);htree=ast.parse(helper)
funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
hfuncs={x.name:x for x in htree.body if isinstance(x,ast.FunctionDef)}
dump=lambda x:ast.dump(x,include_attributes=False)
def constants(t):
 out={}
 for x in t.body:
  if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name):
   try:out[x.targets[0].id]=ast.literal_eval(x.value)
   except (ValueError,TypeError):pass
 return out
const=constants(tree);hconst=constants(htree)
ck('CAP-fixed-expression',any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CAP' for t in n.targets) and ast.unparse(n.value)=='128 * 1024 * 1024' for n in tree.body))
const['CAP']=128*1024*1024
for name in prov['pure_metadata_functions_statically_embedded']:
 ck('pure-function-AST:'+name,dump(funcs[name])==dump(hfuncs[name]))
for name in prov['pure_metadata_constants_statically_embedded']:
 ck('constant-equality:'+name,type(const[name]) is type(hconst[name]) and const[name]==hconst[name])
def block(f):
 nodes=f.body
 start=next(i for i,n in enumerate(nodes) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='config_ref')
 end=next(i for i,n in enumerate(nodes[start:],start) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='manifest') if f.name=='compose' else next(i for i,n in enumerate(nodes[start:],start) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Tuple) and any(isinstance(a,ast.Name) and a.id=='chosen' for a in n.targets[0].elts))
 return [dump(n) for n in nodes[start:end]]
ck('same-snapshot-metadata-validation-block',block(funcs['compose'])==block(hfuncs['run']))
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
imports=[a.name for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) for a in n.names]
ck('imports-stdlib-only',set(imports)=={'sys','hashlib','json','ntpath','os','Path','re','collections'})
ck('no-runtime-helper-execution',not any(isinstance(n.func,ast.Name) and n.func.id in ('exec','eval','compile','__import__') for n in calls))
opens=[n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='open']
ck('only-rb-and-exclusive-xb-open',len(opens)==2 and sorted(ast.literal_eval(n.args[0]) for n in opens)==['rb','xb'])
ck('no-native-process-sign-archive-calls',not any(isinstance(n.func,ast.Attribute) and n.func.attr in ('system','popen','spawn','mkdir','read_bytes','read_text','write_bytes','write_text','rename','unlink') for n in calls))
readcalls=[n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='read']
ck('sole-bounded-read-expression',len(readcalls)==1 and ast.unparse(readcalls[0])=="stream.read(value['bytes'] + 1)")
bbody=funcs['bounded_read'].body
ck('length-before-digest',len(bbody)==5 and 'len(raw)' in ast.unparse(bbody[2]) and 'hashlib.sha256' in ast.unparse(bbody[3]))
ck('builder-fixed-config-helper',const['CONFIG']==prov['config_ref'] and const['HELPER']==prov['helper_ref'])
ck('fixed-case',const['CASE_ID']=='t12cl149d6f49321')
ck('fixed-flag',const['FULL_FLAG']=='--select-full-current-grant-public-pins')
ck('fixed-fresh-request-archive',not os.path.lexists(hdf['fixed_request_path']) and not os.path.lexists(hdf['fixed_archive_output_directory']))
ck('request-parent-exists',Path(hdf['fixed_request_path']).parent.is_dir())
ck('no-TTL-or-auth-rewrite',not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id in ('snap','snapshot','payload','ready','observed') for t in n.targets) for n in ast.walk(funcs['compose'])))
# Extract only named pure functions. No candidate module, main, compose, writer,
# helper module, SourceReadGuard, native entrypoint or real payload is executed.
allowed={'require','pairs','decode','digest','canonical','inside','exact','ref','rawpin','plain','same','counter','inventory_roles','validate_grant','validate_selection','validate_ref','bounded_read','select_full'}
env={'hashlib':hashlib,'json':json,'ntpath':ntpath,'os':os,'Path':Path,'re':re,'collections':collections}
env.update(const)
selected=ast.Module(body=[funcs[n] for n in funcs if n in allowed],type_ignores=[])
exec(compile(ast.fix_missing_locations(selected),'<independent-pure-AST-subset>','exec'),env)
purecanonical=env['canonical']
env['canonical']=lambda value: purecanonical(value,False)
def control(name,fn,reject=False):
 try:value=fn()
 except (ValueError,TypeError,KeyError,OSError) as e:
  ck(name,reject);return
 ck(name,not reject and value is not False)
# Bounded read controls use a fake stream and record every requested size/close.
state={};events=[]
class FakeStream:
 def __enter__(self):return self
 def __exit__(self,*args):events.append('closed')
 def read(self,n):
  events.append(('read',n))
  if state.get('error'):raise OSError('expected synthetic stream error')
  return b'a'*min(n,state['actual'])
class FakePath:
 def __init__(self,p):self.p=p
 def open(self,mode):
  events.append(('open',mode));return FakeStream()
def boundary(size,actual,wrong=False,error=False):
 events.clear();state.update(actual=actual,error=error)
 env['Path']=FakePath
 value={'path':'D:/fixture/public.json','bytes':size,'sha256':'sha256:'+hashlib.sha256(b'a'*size).hexdigest() if type(size) is int and 0<=size<1024 else 'sha256:'+'a'*64}
 if wrong:value['sha256']='sha256:'+'0'*64
 try:return env['bounded_read'](value)==b'a'*size
 finally:
  if events:ck('bounded-read-and-close:'+repr(size),events==[('open','rb'),('read',size+1),'closed'])
  else:ck('invalid-size-rejected-before-open:'+repr(size),type(size) is not int or size<0 or size>const['CAP'])
  env['Path']=Path
for name,size,actual,reject,wrong,error in [
 ('zero',0,0,False,False,False),('exact',11,11,False,False,False),('short',11,10,True,False,False),
 ('one-extra',11,12,True,False,False),('huge-virtual',11,10**15,True,False,False),('zero-extra',0,1,True,False,False),
 ('wrong-sha',11,11,True,True,False),('bool',True,0,True,False,False),('float',11.0,0,True,False,False),
 ('negative',-1,0,True,False,False),('above-cap',const['CAP']+1,0,True,False,False),
 ('cap-short',const['CAP'],0,True,False,False),('read-error',11,0,True,False,True)]:
 control('fake-stream:'+name,lambda s=size,a=actual,w=wrong,e=error:boundary(s,a,w,e),reject)
control('duplicate-json-rejected',lambda:env['decode'](b'{"a":1,"a":2}'),True)
control('NaN-rejected',lambda:env['decode'](b'{"a":NaN}'),True)
control('uint64-exact',lambda:env['decode'](b'{"a":18446744073709551615}')['a']==18446744073709551615)
def rp(role,path,sha='sha256:'+'a'*64,size=3):return {'role':role,'path':path,'sha256':sha,'bytes':size}
temp='D:/synthetic-only/temp'
testcfg={'Environment':{'TEMP':temp}}
testhc={'OutputDirectory':'D:/synthetic-only/harness','BackupProgram':rp('backup','D:/resident/backup.exe'),'ControlProgram':rp('control','D:/resident/control.exe')}
opts={'Plan':const['PLAN'],'SourceRoot':temp+'/src','TargetRoot':temp+'/dst','Snapshot':temp+'/backup','Destination':temp+'/restored','KeyFile':'NEVER_READ_PRIVATE_KEY'}
pins=[rp('source-program',testhc['BackupProgram']['path']),rp('target-program',testhc['ControlProgram']['path'])]
for role in sorted(env['inventory_roles']()):
 prefix,name=role.split(':',1);v=const['INVENTORY'][name]
 pins.append(rp(role,opts['SourceRoot' if prefix=='source-inventory' else 'TargetRoot']+'/'+name,v['sha256'],v['bytes']))
alias=copy.deepcopy(next(p for p in pins if p['role']==const['ALIAS_TARGET']));alias['role']='migration-sql';pins.append(alias)
backup=rp('encrypted-backup-manifest',opts['Snapshot']+'/manifest.json')
rehearsal=rp('isolated-restore-rehearsal',opts['Destination']+'/prepared-abandonment-rehearsal.json')
pins += [backup,rehearsal]+[rp('encrypted-backup-payload:'+n+'.enc',opts['Snapshot']+'/'+n+'.enc') for n in ('state.sqlite','workspace_2')]
pins += [rp('fixture-evidence:'+n,testhc['OutputDirectory']+'/'+n) for n in ('before.rows.json','fixture.public.json','00-rehearsal/invocation.json','00-rehearsal/stdout.raw','00-rehearsal/stderr.raw')]
payload={'schema':'researchos.recovery-migration-grant.v1','purpose':'RESEARCHOS_PREPARED_SCHEMA23_TO24_V1','stage':'APPLY_ORIGINAL','binding':{'plan_id':const['PLAN'],'backup':backup,'rehearsal':rehearsal},'options':opts,'pins':pins,'private_metadata':'NEVER_FOLLOW'}
manifest={'files':[{'name':'state.sqlite'},{'name':'workspace_2'}]}
before=copy.deepcopy(payload)
choose=lambda p=payload,m=manifest,flag=const['FULL_FLAG']:env['select_full'](p,testcfg,testhc,m,flag)
entries=choose()
ck('two-cipher-complete61',len(entries)==61)
ck('source28-target29',sum(p['role'].startswith('source-inventory:') for p in entries)==28 and sum(p['role'].startswith('target-inventory:') for p in entries)==29)
ck('all-entries-exact-four-fields',all(set(p)=={'role','path','sha256','bytes'} for p in entries))
ck('all-original-refs-exact',all(p in pins for p in entries) and payload==before)
ck('unique-role-path',len({p['role'] for p in entries})==len({ntpath.normcase(p['path']) for p in entries})==61)
ck('alias-verified-not-selected',not any(p['role']=='migration-sql' for p in entries))
ck('private-and-program-not-selected',not any('NEVER_' in json.dumps(p) or p['role'] in ('source-program','target-program') or p['role'].startswith('fixture-evidence:') for p in entries))
for flag in ('','--select-full',True):
 control('bad-flag:'+str(flag),lambda f=flag:choose(flag=f),True)
for name,m in [('missing-cipher',{'files':[{'name':'state.sqlite'}]}),('extra-cipher',{'files':[{'name':'state.sqlite'},{'name':'workspace_2'},{'name':'extra'}]}),('duplicate',{'files':[{'name':'state.sqlite'},{'name':'state.sqlite'}]}),('traversal',{'files':[{'name':'../private'}]})]:
 control('manifest:'+name,lambda m=m:choose(m=m),True)
for name,edit in [
 ('alias-conflict',lambda p:next(x for x in p['pins'] if x['role']=='migration-sql').update(bytes=123)),
 ('missing-inventory',lambda p:p['pins'].pop(2)),
 ('duplicate-role',lambda p:p['pins'].append(copy.deepcopy(p['pins'][2]))),
 ('unsupported-private',lambda p:p['pins'].append(rp('private-key','D:/private/key.pem'))),
 ('wrong-fixed-hash',lambda p:p['pins'][2].update(sha256='sha256:'+'0'*64)),
 ('wrong-root',lambda p:p['pins'][2].update(path='D:/elsewhere/a.sql')),
 ('bool-size',lambda p:p['pins'][2].update(bytes=True)),
 ('backup-binding-mismatch',lambda p:p['binding'].update(backup=rp('encrypted-backup-manifest',opts['Snapshot']+'/other.json')))
]:
 p=copy.deepcopy(payload);edit(p)
 control('grant:'+name,lambda p=p:choose(p=p),True)
# No real compose or writer; static final lifecycle/reread/order reviewed separately.
author=read(hdf['controls_ref']['path'])
ck('author45controls-disclosed-source-only',len(author['controls'])==author['count']==45 and all(x['result']=='PASS' for x in author['controls']) and not author['actual_compose'] and not author['actual_builder_main'])
for value in list(inputs.values()):verify(value)
save('input-pins.json',list(inputs.values()))
save('guard.final.json',{'state':'RELEASED','kind':'pin-before-after-observation-only','all_inputs_unchanged':all(c['pass'] for c in checks if c['name'].startswith('pin:')),'os_read_handles_acquired':False,'retained_handles_count':0,'canonical_unchanged_count':4})
save('checks.json',{'checks':checks,'count':len(checks),'all_pass':all(c['pass'] for c in checks),'input_count':len(inputs),'executed_only_extracted_pure_functions':True,'actual_main_compose_writer_helper_native_SQL_Go_API_private_model':False})
print(json.dumps({'checks':len(checks),'input_count':len(inputs),'all_pass':all(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']]},ensure_ascii=True))
sys.exit(0 if all(c['pass'] for c in checks) else 1)

