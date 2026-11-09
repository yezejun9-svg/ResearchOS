"""New registrar reference/resource delta controls only; previous 36 are reused."""
import ast,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;OLD=N.parent/'register-20261010-01';NF=N.parent.parent/'full_w09_main_native_producer_source_codex/fullw09-20261010-05'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def module(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
core=module(N/'adoption_core.source.py');caller=module(N/'register_w09_adoption.source.py');runtime=module(NF/'full_w09_runtime.source.py')
choice=doc(NF/'source.choice.json');contract=doc(NF/'root-calling-contract.json');owncontract=doc(N/'root-calling-contract.source.json')
checks=[]
def check(name,ok):assert ok,name;checks.append(name)
check('generation-only-new-value',core.GENERATION==choice['common']['generation']=='fullw09-20261010-05')
check('runtime-owner-worker-keys-exact',core.NKEY==runtime.OWNER_KEY and core.NSLICE==runtime.SLICE)
pins=doc(N/'input-pins.json')['refs']
fake=dict(path=str(N/'CONTROL_ONLY_NOT_PUBLISHED'),sha256='0'*64,bytes=0)
pins.update(NR_hdf=fake,NR_mf=fake,NR_decision=fake)
request=dict(native_leases={k:dict(lease_id=str(i)*32,lease_issued_at='CONTROL_ONLY',lease_expires_at='CONTROL_ONLY') for i,k in enumerate(core.SELECTORS,1)},
 reviewed_source_audit_refs={'producer-author':fake,'producer-review':fake})
scopes=core.make_native_scopes(request,pins,choice,contract)
check('four-scopes-resource-triple-exact',len(scopes)==4 and all(all(s[k]==choice['common'][k] for k in ('resource_parent_ref','resource_owner_ref','resource_audit_ref')) for s in scopes.values()))
check('new-scope-exact-fields',all(set(s)==set(contract['scope_required_fields']) for s in scopes.values()))
check('input-self-pin-exact',caller.INPUT_PINS_SHA==ref(N/'input-pins.json')['sha256'])
check('new-output-root',str(caller.OUTPUT_BASE).endswith('w09_nf5_root_registration_root'))
tree=ast.parse((N/'register_w09_adoption.source.py').read_bytes());model=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='model')
calls=[n for n in ast.walk(model) if isinstance(n,ast.Call)]
parentcall=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='validate_scratch_parent')
scopecall=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='make_native_scopes')
check('real-parent-observed-before-scope-factory',parentcall.lineno<scopecall.lineno)
check('resource-refs-join-held-context',any(isinstance(n.func,ast.Attribute) and n.func.attr=='extend' and any(isinstance(a,ast.Name) and a.id=='resource_refs' for a in n.args) for n in calls))
check('no-Main-mutation-entrypoint',not hasattr(caller,'apply_profile'))
check('old-controls-preserved-not-rerun',doc(OLD/'delta-controls.json')['passed']==36)
for row in doc(N/'source-delta.json')['source_deltas']:
 text=(N/row['file']).read_bytes().decode()
 for e in reversed(row['inverse_edits']):
  assert text[e['new_start']:e['new_end']]==e['after']
  text=text[:e['new_start']]+e['before']+text[e['new_end']:]
 check('exact-source-inverse-'+row['file'],text.encode()==Path(row['base_ref']['path']).read_bytes())
check('own-contract-bindings-exact',all(owncontract['source_bindings'][k]==ref(N/name) for k,name in {'caller_ref':'register_w09_adoption.source.py','core_ref':'adoption_core.source.py'}.items()))
report=dict(schema='researchos.nf5-registration-delta-controls.v1',status='PASS',passed=len(checks),failed=0,checks=checks,
 synthetic_Source_only=True,no_synthetic_scope_request_audit_published=True,actual_TP_calls=0,actual_Main_writes=0,
 actual_Canon_writes=0,actual_Native_runs=0,actual_Go_runs=0,old_controls_rerun=False)
(N/'delta-controls.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='NF5_REGISTRAR_DELTA_PASS',passed=len(checks),report_ref=ref(N/'delta-controls.json')),ensure_ascii=False))

