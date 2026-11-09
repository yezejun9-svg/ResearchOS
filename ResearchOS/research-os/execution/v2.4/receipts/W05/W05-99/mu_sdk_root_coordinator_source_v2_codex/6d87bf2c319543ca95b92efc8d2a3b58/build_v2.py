"""Produce a narrow immutable v2 Source packet; no candidate execution."""
import ast, difflib, hashlib, json
from pathlib import Path

OLD=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_root_coordinator_source_codex/0436fddcf8d14b72b14ed4f5f67a045c')
OUT=Path(__file__).resolve().parent
def pin(path):
    raw=Path(path).read_bytes()
    return {'path':str(Path(path)), 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}
def put(name,value):
    with (OUT/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(OUT/name)
def rawput(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
    return pin(OUT/name)

expected={'handoff.json':('fdc1491dff9d0b87b32e3b80df95d09f517e97bf1c50fe4ccdb35f6da4a1aad1',4869),'manifest.json':('79a71ce51ac90aa05ac85ceb5ac54c75575d09d91d6e91a1d914bb831c9594b2',15779),'root_coordinator.py':('27c744f7410b6a9cf957f72bef3416bde370c45b028df79c121fed5932867890',34304)}
for name,(h,n) in expected.items():
    actual=pin(OLD/name)
    assert actual['sha256']==h and actual['bytes']==n
old_manifest=json.loads((OLD/'manifest.json').read_bytes())
for ref in old_manifest['members']:
    actual=pin(ref['path'])
    assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
before=(OLD/'root_coordinator.py').read_bytes()
old=b"    print(json.dumps(result, ensure_ascii=False), flush=True)\n    if result['state'] == 'RETAINED_UNCONFIRMED':\n        coordinator.retain_parent()\n    return result\n"
new=b"    if result['state'] == 'RETAINED_UNCONFIRMED':\n        try:\n            print(json.dumps(result, ensure_ascii=False), flush=True)\n        finally:\n            coordinator.retain_parent()\n    else:\n        print(json.dumps(result, ensure_ascii=False), flush=True)\n    return result\n"
assert before.count(old)==1
after=before.replace(old,new)
assert after.replace(new,old)==before
source_ref=rawput('root_coordinator.py',after)
for name,a,b in [('source.forward.diff',before,after),('source.inverse.diff',after,before)]:
    rawput(name,''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='v1/root_coordinator.py',tofile='v2/root_coordinator.py')).encode())
old_ast=ast.parse(before);new_ast=ast.parse(after)
old_other=[ast.dump(n,include_attributes=False) for n in old_ast.body if not isinstance(n,ast.FunctionDef) or n.name!='run_resident']
new_other=[ast.dump(n,include_attributes=False) for n in new_ast.body if not isinstance(n,ast.FunctionDef) or n.name!='run_resident']
assert old_other==new_other
compile(new_ast,str(OUT/'root_coordinator.py'),'exec')

# One focused matrix control: isolated run_resident AST, fake coordinator,
# fake output functions. No constructor/WinAPI/process/SQL/provider is invoked.
target=next(n for n in new_ast.body if isinstance(n,ast.FunctionDef) and n.name=='run_resident')
target_code=compile(ast.Module(body=[target],type_ignores=[]),'<run_resident pure control>','exec')
cases=[]
for mode in ('normal','BrokenPipeError','serialization_TypeError','output_RuntimeError'):
    events=[]
    class RetentionEntered(BaseException):pass
    class FakeCoordinator:
        def __init__(self,*args):events.append('construct')
        def run(self):events.append('run');return {'state':'RETAINED_UNCONFIRMED'}
        def retain_parent(self):events.append('retain_parent');raise RetentionEntered()
    class FakeJSON:
        @staticmethod
        def dumps(*args,**kwargs):
            events.append('serialize')
            if mode=='serialization_TypeError':raise TypeError('synthetic serialization failure')
            return 'synthetic retained result'
    def fake_print(*args,**kwargs):
        events.append('print')
        if mode=='BrokenPipeError':raise BrokenPipeError('synthetic stdout failure')
        if mode=='output_RuntimeError':raise RuntimeError('synthetic output failure')
    ns={'RootResidentCoordinator':FakeCoordinator,'json':FakeJSON,'print':fake_print}
    exec(target_code,ns)
    entered=False
    try:ns['run_resident']({}, {})
    except RetentionEntered:entered=True
    assert entered and events.count('retain_parent')==1 and events[-1]=='retain_parent'
    cases.append({'case':mode,'events':events,'retention_entered_exactly_once':True})
control_ref=put('retention-output-control.json',{'schema':'researchos.root-sdk-coordinator-v2-delta-control.v1','controls':1,'passed':1,'matrix_cases':cases,'other_module_AST_unchanged':True,'full_bytes_inverse_roundtrip':True,'source_ref':source_ref,'candidate_entry_calls':0,'candidate_imports':0,'real_native_WinAPI_SQL_provider_calls':0,'scope':'run_resident isolated AST with fake coordinator/output; RetentionEntered sentinel replaces the intentional resident loop.'})
fixed_ref=rawput('fixed-pins.json',(OLD/'fixed-pins.json').read_bytes())
for name in ('input.no-provider.template.json','input.model-trial.template.json','root-execution-authority.template.json','independent-source-review.template.json'):
    doc=json.loads((OLD/name).read_bytes())
    doc['source_ref' if name=='independent-source-review.template.json' else 'coordinator_source_ref']=source_ref
    if 'fixed_pins_ref' in doc:doc['fixed_pins_ref']=fixed_ref
    put(name,doc)
inputs=[pin(OLD/name) for name in ('handoff.json','manifest.json','root_coordinator.py','fixed-pins.json','source-controls.v3.json','original-final-source-controls-io.json','REPORT.md')]
put('reuse-evidence.json',{'old_packet_refs':inputs,'old_manifest_members_verified':len(old_manifest['members']),'previous_controls_reused_not_rerun':40,'previous_fixed_roles_reused_not_rehashed':24,'fixed_pins_bytes_unchanged':(OUT/'fixed-pins.json').read_bytes()==(OLD/'fixed-pins.json').read_bytes(),'historical_failures_not_recounted':[710,711,712,716],'new_tool_failures':0})
rawput('REPORT.md',b'# Root coordinator v2: output failure retention\n\nDecision: IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW.\n\nThe only Source change is run_resident: when cleanup is uncertain, JSON serialization and print are inside a try block whose finally always calls retain_parent. Successful output, BrokenPipeError, serialization TypeError, and other output RuntimeError all enter retention exactly once in the focused fake control. The prior packet remains immutable.\n\nThe prior 24 fixed Source/binary role pins and 40 controls are reused, not rerun or promoted to actual runtime evidence. All other module AST is unchanged; full-byte forward/inverse restoration is verified. New candidate imports/entrypoints, real WinAPI/native/SQL/provider calls, and Main/canonical writes are zero.\n\nNO_PROVIDER remains only bootstrap evidence inspection. MODEL_TRIAL still requires actual successful bootstrap evidence, independent non-author Source review, and separate Root runtime authorization. Parent/Host/C7 native lifecycle, provider reconciliation, and formal acceptance remain OPEN. No READY or execution approval is issued.\n')
put('build-result.json',{'source_ref':source_ref,'control_ref':control_ref,'fixed_pins_ref':fixed_ref,'new_controls':1,'new_controls_passed':1,'new_tool_failures':0,'candidate_native_SQL_provider_calls':0,'Main_canonical_writes':0,'decision':'IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW'})
print(json.dumps({'source_ref':source_ref,'control_ref':control_ref,'new_controls':1,'passed':1,'matrix_cases':len(cases),'other_AST_unchanged':True,'inverse_roundtrip':True,'prior_controls_reused':40,'prior_role_pins_reused':24}))
