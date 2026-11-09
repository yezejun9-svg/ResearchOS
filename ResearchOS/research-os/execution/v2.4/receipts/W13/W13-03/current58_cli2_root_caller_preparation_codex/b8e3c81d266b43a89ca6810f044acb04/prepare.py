"""IO + AST only; does not import or execute the caller or launcher."""
import ast,difflib,hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).parent
P05=ROOT/'execution/v2.4/receipts/W05/W05-99'
OLD=P05/'integration_codex/cli43-fresh-held2-r331-c4f309c5528f5d42be5e7eeb146a20aa'
NEW=P05/'integration_codex/cli58-fresh-held2-r334-v2-0e298790cd484ec9ba319a379e7e34ed'
REVIEW=P05/'cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0'
reads={}
def read(p):
    p=Path(p);b=p.read_bytes();reads[str(p)]=b;return b
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
    with (OUT/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def put(n,b):
    with (OUT/n).open('xb') as f:f.write(b)
mf=json.loads(read(OLD/'root-launch.closed.manifest.json'))
oldref=next(x for x in mf['members'] if Path(x['path']).name=='root-launch-once.v2.py')
base=read(oldref['path']);assert pin(oldref['path'])==oldref
assert oldref['sha256']=='bc191ffe9a2752cd8e339371cd8f96c1c992742d63aeda92f2cc29a42e5ef6ad' and len(base)==4540
read(OLD/'root-caller-preparation.json')
for name in ['handoff.json','review.json']:
    read(REVIEW/name)
scope_raw=read(NEW/'scope_registration.json')
assert hashlib.sha256(scope_raw).hexdigest()=='459f00078d742e754631294d17210329280c2e1fec0cf7925b94fb4333c3bc84' and len(scope_raw)==8853
scope=json.loads(scope_raw)
for key in ['launcher_ref','owned_process_helper_ref']:
    b=read(scope[key]['path']);assert hashlib.sha256(b).hexdigest()==scope[key]['sha256'] and len(b)==scope[key]['bytes']
assert scope['source_commit']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
assert scope['launch_limits']=={'outer_timeout_seconds':3600,'inner_soft_deadline_seconds':3300,'termination_cleanup_seconds':5}
text=base.decode();nl='\r\n' if b'\r\n' in base else '\n'
edits=[]
def change(old,new,why):
    global text
    old=old.replace('\n',nl);new=new.replace('\n',nl)
    assert text.count(old)==1,(why,text.count(old))
    text=text.replace(old,new,1);edits.append({'old':old,'new':new,'reason':why})
change("OUT = Path(__file__).absolute().parent","OUT = None\nREGISTRATION = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli58-fresh-held2-r334-v2-0e298790cd484ec9ba319a379e7e34ed'",'Separate future Root caller output from fixed actual registration input')
change("SCOPE_SHA = 'f71b60ad316aa3034ff3da5cd79c6aac4c4e5997425d86e7b84d2f9fc02ec89b'","SCOPE_SHA = '459f00078d742e754631294d17210329280c2e1fec0cf7925b94fb4333c3bc84'",'Exact current58 Root scope pin')
change("GRANT_SHA = '124f16da796d16dd4a066d3b5ed8a00db8e744f7ca690d614cf46b14b8ac0f81'","GRANT_SHA = None",'No old or invented grant SHA')
change("sys.dont_write_bytecode = True\nscope_path = OUT / 'scope_registration.json'",'''sys.dont_write_bytecode = True
need(len(sys.argv) == 3, 'Root must supply actual grant SHA and a fresh allocated caller output directory')
GRANT_SHA = sys.argv[1]
need(len(GRANT_SHA) == 64 and all(c in '0123456789abcdef' for c in GRANT_SHA), 'Explicit actual grant SHA')
OUT = Path(sys.argv[2])
need(OUT.is_absolute() and '..' not in OUT.parts and str(OUT.resolve()) == str(OUT), 'Canonical caller output')
need(OUT.is_relative_to(ROOT / 'execution/v2.4/receipts') and OUT != ROOT / 'execution/v2.4/receipts', 'Public receipt output only')
need(not OUT.is_relative_to(Path(__file__).resolve().parent) and not OUT.is_relative_to(REGISTRATION), 'Do not write sealed preparation or registration namespaces')
need(OUT.is_dir() and not any(OUT.iterdir()), 'Root must separately allocate a new empty caller directory')
scope_path = REGISTRATION / 'scope_registration.json' ''','Explicit arguments, fixed scope path, and no output allocation by this source')
change("scope = json.loads(scope_path.read_bytes().decode('utf-8'))",'''scope = json.loads(scope_path.read_bytes().decode('utf-8'))
need(scope['source_commit'] == 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7', 'Current58 source only')
need(scope['registration_namespace'] == REGISTRATION.relative_to(ROOT).as_posix(), 'Fixed actual registration namespace')
need(scope['launch_limits'] == {'outer_timeout_seconds': 3600, 'inner_soft_deadline_seconds': 3300,
                              'termination_cleanup_seconds': 5}, 'Original bounded launch limits')''','Bind exact new source identity without changing caller process or qualification logic')
candidate=text.encode()
ast.parse(candidate)
reverse=text
for edit in reversed(edits):
    assert reverse.count(edit['new'])==1
    reverse=reverse.replace(edit['new'],edit['old'],1)
assert reverse.encode()==base
suffix=base[base.index(b'result = None'):]
assert candidate[candidate.index(b'result = None'):]==suffix
bt,nt=ast.parse(base),ast.parse(candidate)
bd={n.name:ast.dump(n,include_attributes=False) for n in bt.body if isinstance(n,ast.FunctionDef)}
nd={n.name:ast.dump(n,include_attributes=False) for n in nt.body if isinstance(n,ast.FunctionDef)}
assert bd==nd
put('root-launch-once.current58.proposed.py',candidate)
save('edits.inverse.json',{'baseline_ref':oldref,'candidate_ref':pin(OUT/'root-launch-once.current58.proposed.py'),'edits':edits,'whole_inverse':True})
put('source.diff',''.join(difflib.unified_diff(base.decode().splitlines(True),text.splitlines(True),fromfile=str(Path(oldref['path'])),tofile=str(OUT/'root-launch-once.current58.proposed.py'))).encode())
before=[{'path':k,'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for k,v in reads.items()]
save('inputs.before.json',before)
assert before==[pin(p) for p in reads]
save('inputs.after.json',[pin(p) for p in reads])
save('static-audit.json',{'AST_only':True,'candidate_imported':False,'candidate_executed':False,'baseline_newline':repr(nl),
 'whole_inverse_exact':True,'original_need_pin_save_AST_unchanged':bd==nd,'result_try_except_finally_tail_bytes_unchanged':True,
 'input_count':len(before),'input_drift':0,'caller_subprocess_timeout_seconds':3900,'launcher_owned_timeout_seconds':3600,
 'runner_soft_deadline_seconds':3300,'owned_cleanup_seconds':5,'caller_OS_lifecycle_qualification':False,
 'helper_ref':scope['owned_process_helper_ref'],'helper_imported_or_executed':False,
 'old_grant_SHA_not_in_candidate':'124f16da796d16dd4a066d3b5ed8a00db8e744f7ca690d614cf46b14b8ac0f81' not in text,
 'new_grant_path_derived_from_actual_scope':True,'future_grant_SHA':None,'future_Root_caller_output':None,'future_currentbinding_ref':None,
 'new_failure_origins':[]})
save('contract.json',{'schema':'researchos.current58-cli2-root-caller-preparation.v1','state':'SOURCE_PREPARATION_ONLY',
 'owner':'codex:/root/command_queue_impl','sole_future_actor':'codex:/root',
 'argv':['PINNED_PYTHON','-I','-S','-X','utf8',str(OUT/'root-launch-once.current58.proposed.py'),'ACTUAL_GRANT_SHA256','ROOT_ALLOCATED_EMPTY_CALLER_OUTPUT_ABS'],
 'cwd':str(ROOT),'scope_ref':pin(NEW/'scope_registration.json'),'source_commit':scope['source_commit'],
 'actual_grant_ref':None,'future_grant_path':str(Path(scope['new_authorization_root'])/'authorization.execute.json'),
 'grant_path_rule':'Only the already hashed fixed scope supplies new_authorization_root; caller argv supplies SHA, never an alternate grant path.',
 'current_binding_ref':None,'binding_rule':'Caller need not accept a separate currentbinding override. Exact full scope is fixed; existing launcher/gate validate actual sealed grant binding, Root registration, source authority/copies and independent reviews. Actual Root binding/seal must be supplied before executing, not inferred here.',
 'output_contract':'Root separately allocates a NEW empty canonical absolute public receipt directory. Caller refuses its own sealed preparation tree and the fixed registration namespace. It performs no mkdir; four files use original xb opens. An attempted reuse fails before launching.',
 'outputs':['root-launch.intent.json','root-launch.stdout.raw','root-launch.stderr.raw','root-launch.invocation.json'],
 'preserved_boundaries':{'caller':'original subprocess.run timeout3900; no claimed owned Job lifecycle','launcher':'same pinned launcher invokes helper6a4 owned process timeout3600','runner':'3300 soft deadline; original2 cases and all controls unchanged','cleanup':5},
 'new_grant_and_Root_authorization':'OPEN; this is not a grant producer and no actual grant was read or assumed.',
 'known_finalization_limit':'Original finally captures receipt-write errors as secondary and preserves first error in its invocation attempt. Subsequent sys.stderr.write / final print can themselves fail without a new protected fallback, so an outer stream/write error may change the observed exit presentation. The full original body is preserved per Root instruction; no runtime proof or suppression is claimed.',
 'narrow_future_fix_if_required':'A separate reviewed delta could guard only fallback stderr/print and preserve their errors as secondary; not implemented or needed to claim success now.',
 'source_acceptance':False,'formal_increment':0,'actual_candidate_or_Go_SQL_HTTP_Node_SDK_model_calls':0,
 'old_r331_evidence':'Source/manifest/interface reference only; not current58 fresh compiler or case qualification.'})
print(json.dumps({'caller':pin(OUT/'root-launch-once.current58.proposed.py'),'contract':pin(OUT/'contract.json'),'input_count':len(before),'edits':len(edits),'candidate_execution':0},ensure_ascii=False))
