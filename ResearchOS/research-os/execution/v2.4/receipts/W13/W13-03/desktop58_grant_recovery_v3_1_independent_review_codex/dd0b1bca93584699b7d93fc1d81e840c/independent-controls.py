"""Independent v3.1 AST predicate controls only; no observer/gate/recovery calls."""
import ast, copy, datetime, difflib, hashlib, json, pathlib, sys
sys.dont_write_bytecode=True
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
P05=R/'execution/v2.4/receipts/W05/W05-99'
S=P05/'scope7_grant_recovery_cim_precision_revision_source_preparation_codex/8e81f98236dc47399ff5ffd243919350/scope7_grant_recover.v3_1.proposed.py'
OLD=P05/'scope7_grant_recovery_postgate_observer_source_preparation_codex/7716ce1dbb0849eb9dc0fd52457047e8/scope7_grant_recover.v3.proposed.py'
A=pathlib.Path(__file__).parent
def ref(p):
 b=p.read_bytes()
 return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
 with (A/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(A/name)
raw=S.read_bytes();assert ref(S)['sha256']=='cae680256241a8f6f1d1d4be7e42222acef465532d97056ec1ad0d9fe9c24b3a'
tree=ast.parse(raw); oldtree=ast.parse(OLD.read_bytes())
F={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
OF={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}
changed=[n for n in OF if ast.dump(F[n])!=ast.dump(OF[n])]
assert changed==['observe'] and set(F)-set(OF)=={'cim_birth_microsecond'}
context={'datetime':datetime}
exec(compile(ast.Module(body=[F[n] for n in ('need','stamp','cim_birth_microsecond')],type_ignores=[]),'<pure timestamp helpers>','exec'),context)
obs=F['observe']
start=next(i for i,n in enumerate(obs.body) if isinstance(n,ast.Expr) and ast.unparse(n).endswith("' owned CIM PID/creation/parent chain mismatch')"))
end=next(i for i,n in enumerate(obs.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='classification' for t in n.targets))
code=compile(ast.Module(body=obs.body[start:end],type_ignores=[]),'<exact identity and UID predicates>','exec')
born=134359248965439659
epoch=datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)
def row(pid,birth,ppid,cmd):
 normalized=birth//10
 return {'ProcessId':pid,'ParentProcessId':ppid,'CreationDateCimUtc':(epoch+datetime.timedelta(microseconds=normalized)).isoformat(),'CreationTime100nsFromCIM':normalized*10,'CommandLine':cmd}
uid='9eccde97a9fa4815941768cacaf590dc'
own=row(102,born,101,'Get-CimInstance Win32_Process '+uid)
parent=row(101,born-10000000,100,S.name+' '+uid)
wrapper=row(100,born-20000000,99,S.name+' '+uid)
base={'phase':'synthetic','python_pid':101,'wrapper_pid':100,'python_birth':born-10000000,
 'result':{'owned_child_pid':102,'creation_time_100ns':born},'SOURCE':S,'UID':uid,
 'own':own,'parent':parent,'wrapper':wrapper,'value':{'all_uid_processes':[own,parent,wrapper]}}
checks=[]
def test(name,mutate,expected):
 data=copy.deepcopy(base);mutate(data); env=dict(context);env.update(data)
 try:
  exec(code,env)
  outcome='live' if env['matching'] else 'empty'
  error=None
 except (RuntimeError,ValueError,TypeError) as exc:
  outcome='reject';error=str(exc)
 assert outcome==expected,(name,outcome,expected)
 checks.append({'name':name,'expected':expected,'observed':outcome,'error':error,'passed':True})
test('nondivisible genuine 100ns timestamps preserve valid chain',lambda d:None,'empty')
test('same PID different child generation rejected',lambda d:d.update(own=row(102,born-10,101,'Get-CimInstance Win32_Process '+uid)),'reject')
test('same PID different Python generation rejected',lambda d:d.update(parent=row(101,born-10000010,100,S.name+' '+uid)),'reject')
test('wrong child PID rejected',lambda d:d['own'].update(ProcessId=103),'reject')
test('wrong parent chain rejected',lambda d:d['parent'].update(ParentProcessId=99),'reject')
test('non-microsecond derived timestamp rejected',lambda d:d['own'].update(CreationTime100nsFromCIM=born),'reject')
test('ISO and converted timestamp mismatch rejected',lambda d:d['own'].update(CreationDateCimUtc=row(102,born+10,101,'')['CreationDateCimUtc']),'reject')
test('extra UID process retained',lambda d:d['value']['all_uid_processes'].append(row(104,born-30000000,90,uid)),'live')
test('same PID with different birth cannot be excluded',lambda d:d['value']['all_uid_processes'].append(row(102,born-30000000,90,uid)),'live')
test('duplicate UID identity rejected',lambda d:d['value']['all_uid_processes'].append(copy.deepcopy(d['own'])),'reject')
test('missing CIM timestamp rejected',lambda d:d['own'].pop('CreationDateCimUtc'),'reject')
birth=context['cim_birth_microsecond']
offset=copy.deepcopy(own)
utc=datetime.datetime.fromisoformat(offset['CreationDateCimUtc'])
offset['CreationDateCimUtc']=utc.astimezone(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
assert birth(offset)==born//10
checks.append({'name':'qualified timezone normalized consistently','passed':True})
mf=json.loads((S.parent/'manifest.json').read_bytes())
hf=json.loads((S.parent/'handoff.json').read_bytes())
refs=mf['members']+[hf['manifest_ref'],hf['source_ref'],hf['report_ref']]
for item in refs:assert ref(R/item['path'])==item,item
assert set(p.name for p in S.parent.iterdir())=={pathlib.Path(x['path']).name for x in mf['members']}|set(mf['excluded'])
prior=R/'execution/v2.4/receipts/W13/W13-03/desktop58_grant_recovery_v3_independent_review_codex/6ed5d8f8202d49d6a9eb4c9bb63a90e2'
counter=json.loads((prior/'precision-counterexample.json').read_bytes())
assert counter['historical_actual_FILETIME_used']==born
state={'source_ref':ref(S),'source_manifest_ref':ref(S.parent/'manifest.json'),'source_handoff_ref':ref(S.parent/'handoff.json'),
 'source_member_refs_verified':len(refs),'exact_source_inventory':True,'changed_existing_functions':changed,
 'added_functions':['cim_birth_microsecond'],'checks':checks,'failed_checks':[],
 'original_FILETIME_decimal':str(born),'CIM_FILETIME_decimal':str(born//10*10),
 'prior_review_numeric_display_correction':{'path':ref(prior/'review.json'),'field':'requests[0].counterexample.actual_historical_FILETIME',
 'sealed_value_decimal':'134359248965439660','exact_raw_counterexample_value_decimal':str(born),
 'cause':'JavaScript Number precision when serializing prior review; original precision-counterexample.json and precision-controls.py preserve correct integer',
 'changes_blocker_reason':False},
 'actual_process_probes':0,'actual_gate_executions':0,'actual_recovery_executions':0,'canonical_writes':0,'grant_tail_writes':0}
with (A/'source.diff.txt').open('x',encoding='utf-8',newline='') as f:f.write(''.join(difflib.unified_diff(OLD.read_text(encoding='utf-8').splitlines(True),S.read_text(encoding='utf-8').splitlines(True))))
out=write('independent-controls.json',state)
print(json.dumps({'audit_root':A.relative_to(R).as_posix(),'controls_ref':out,'checks':len(checks),'failed':0},ensure_ascii=False))
