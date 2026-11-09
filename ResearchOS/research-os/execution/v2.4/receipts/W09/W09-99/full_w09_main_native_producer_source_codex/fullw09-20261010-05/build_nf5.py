"""NF5 path/resource delta only; preserve sealed NF4 and its 35 prior controls."""
import ast,copy,hashlib,json,types,uuid
from pathlib import Path
N=Path(__file__).resolve().parent;OLD=N.parent/'fullw09-20261010-04';W=N.parent.parent
PARENT=Path('C:/Users/yqyyds/.researchos/w09-native-v5')
RP=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
RESOURCE=RP/'physical-C-native-v5-resource-parents.closed.root.json'
AUDIT=RP/'w09.physical-C-native-v5-resource-parent.actual-audit.root.json'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert ref(RESOURCE)==dict(path=str(RESOURCE),sha256='b85a53b28b489526cf7e7e68acb784ae0661283bea88b5e8c03e152e924ad698',bytes=2199)
assert ref(AUDIT)==dict(path=str(AUDIT),sha256='a5cd6eaa9c8880bfa9148cb9235fe92fc75f5af651ed2f045f6182962364751b',bytes=1103)
base=doc(OLD/'source.choice.json');oldcontract=doc(OLD/'root-calling-contract.json')
names=('full_w09_runtime.source.py','runtime-overrides.source.py','full_w09_launcher.source.py','prepare_full_w09.source.py','run_full_w09.source.py','compiler-source-blueprint.json','source.choice.json','root-calling-contract.json')
resource=doc(RESOURCE);marker=resource['resource_owner_marker_ref']
inputs=[ref(OLD/n) for n in names]+[ref(OLD/'HDF.json'),ref(OLD/'MF.json'),ref(RESOURCE),ref(AUDIT),marker,doc(AUDIT)['original_capture_ref']]
gr=base['common']['guard_ref'];raw=Path(gr['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==gr['sha256']
gm=types.ModuleType('nf5_source_guard');gm.__file__=gr['path'];exec(compile(raw,gr['path'],'exec'),gm.__dict__)
g=gm.SourceReadGuard(total_cap=256*1024*1024);g.acquire(inputs)
edits=[]
helper='''
def validate_scratch_parent(c):
    """Bind actual Root resource provenance and reobserve the exact physical C path."""
    parent=Path('C:/Users/yqyyds/.researchos/w09-native-v5')
    resource=decode(read_ref(c['resource_parent_ref']))
    require(resource['schema']=='researchos.w09-fixed-physical-C-resource-parent-intent.v1'
        and resource['actor_id']==ROOT_ACTOR and resource['project_identity_ref']==c['identity_ref']
        and resource['exact_parent_paths']==[str(parent.parent),str(parent)]
        and resource['resource_scope_only'] is True and resource['execution_grant'] is False
        and resource['RootScope_issued'] is False and resource['Native_calls']==0
        and resource['resource_owner_marker_ref']==c['resource_owner_ref'],'EXACT_ROOT_RESOURCE_ONLY')
    for directory in (parent.parent,parent):
        require(exact_path(directory).is_dir(),'ACTUAL_PHYSICAL_C_RESOURCE_PARENT')
    require(c['resource_owner_ref']['path']==str(parent/'RESOURCE_OWNER.json'),'EXACT_RESOURCE_OWNER_PATH')
    owner=decode(read_ref(c['resource_owner_ref']))
    require(owner==dict(schema='researchos.w09-native-private-resource-owner.v1',
        project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb',repository_root=str(R),scratch_parent=str(parent)),
        'EXACT_PROJECT_RESOURCE_OWNER')
    audits=actual_audit(c['resource_audit_ref'],ROOT_ACTOR,c['resource_parent_ref']['sha256'])
    return [c['resource_parent_ref'],c['resource_owner_ref'],*audits]
'''
def transform(name,changes,append=''):
 original=(OLD/name).read_bytes();text=original.decode('utf-8')
 applied=[]
 for a,b in changes:
  assert a in text,(name,a)
  count=text.count(a);text=text.replace(a,b);applied.append(dict(before=a,after=b,count=count))
 text+=append
 restored=text[:-len(append)] if append else text
 for e in reversed(applied):restored=restored.replace(e['after'],e['before'])
 assert restored.encode()==original,('EXACT_INVERSE',name)
 (N/name).write_bytes(text.encode());edits.append(dict(file=name,base_ref=ref(OLD/name),candidate_ref=ref(N/name),replacements=applied,appended=append))
try:
 common=[
 ('fullw09-20261010-04','fullw09-20261010-05'),
 ('C:/Users/yqyyds/AppData/Local/ResearchOS/w09-native-v4','C:/Users/yqyyds/.researchos/w09-native-v5'),
 ("'source21','generation')","'source21','generation','resource_parent_ref','resource_owner_ref','resource_audit_ref')"),
 ("    for ref in c['source21']:read_ref(ref)\n    return unique(refs+rr+audits+","    resource_refs=validate_scratch_parent(c)\n    for ref in c['source21']:read_ref(ref)\n    return unique(refs+rr+audits+resource_refs+")]
 # NF4 text retained original CRLF; match the exact existing byte newline style.
 for name in ('full_w09_runtime.source.py','runtime-overrides.source.py'):
  rawtext=(OLD/name).read_bytes().decode()
  changes=[(a if a in rawtext else a.replace('\n','\r\n'),b if a in rawtext else b.replace('\n','\r\n')) for a,b in common]
  transform(name,changes,helper)
 runtime=ref(N/'full_w09_runtime.source.py');oldsha=ref(OLD/'full_w09_runtime.source.py')['sha256']
 for name in ('prepare_full_w09.source.py','run_full_w09.source.py','full_w09_launcher.source.py'):transform(name,[(oldsha,runtime['sha256'])])
 (N/'compiler-source-blueprint.json').write_bytes((OLD/'compiler-source-blueprint.json').read_bytes())
 choice=copy.deepcopy(base);choice['common'].update(generation='fullw09-20261010-05',
  compiler_blueprint_ref=ref(N/'compiler-source-blueprint.json'),resource_parent_ref=ref(RESOURCE),resource_owner_ref=marker,resource_audit_ref=ref(AUDIT))
 for key,item in choice['selectors'].items():
  run=uuid.uuid4().hex;item.update(run_id=run,receipt_root=str(N/('actual-'+key+'-'+run)),scratch_root=str(PARENT/(key+'-'+run)),
    output_root=str(Path(choice['common']['source_root'])/'execution/receipts/W09/retrieval'/('run-'+run)))
  assert all(not Path(item[k]).exists() for k in ('receipt_root','scratch_root','output_root'))
 put(N/'source.choice.json',choice)
 text=json.dumps(oldcontract,ensure_ascii=False)
 contract=json.loads(text.replace('fullw09-20261010-04','fullw09-20261010-05'))
 contract['bound_source_refs']={k:ref(N/name) for k,name in contract['source_file_bindings'].items()}
 contract['scope_required_fields']+=['resource_parent_ref','resource_owner_ref','resource_audit_ref']
 contract['scratch_policy']['exact_parent']=str(PARENT)
 contract['scratch_policy']['Root_must_create_parent_separately']=False
 contract['scratch_policy'].update(Root_actual_parent_receipt_ref=ref(RESOURCE),Root_actual_parent_audit_ref=ref(AUDIT),
  resource_owner_marker_ref=marker,runtime_reobserves_exact_physical_parent=True,resource_receipt_is_execution_grant=False,
  future_formal_consumer_actual_TEMP_TMP=str(PARENT))
 put(N/'root-calling-contract.json',contract)
 for name in names:
  if name.endswith('.py'):ast.parse((N/name).read_bytes())
 put(N/'source-delta.json',dict(schema='researchos.nf5-physical-C-source-delta.v1',base_hdf_ref=ref(OLD/'HDF.json'),
  base_mf_ref=ref(OLD/'MF.json'),source_edits=edits,exact_Source_inverse=True,
  Source21_unchanged=choice['common']['source21']==base['common']['source21'],
  compiler_blueprint_byte_unchanged=(N/'compiler-source-blueprint.json').read_bytes()==(OLD/'compiler-source-blueprint.json').read_bytes(),
  old_NF4_controls_reused_not_rerun=ref(OLD/'delta-controls.json'),actual_Native_runs=0,actual_Go_runs=0,
  actual_RootScope_registration=False,Main_written=False,Canon_written=False))
finally:
 closed=g.close();put(N/'source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
print(json.dumps(dict(status='NF5_SOURCE_BUILT',runtime_ref=runtime,contract_ref=ref(N/'root-calling-contract.json')),ensure_ascii=False))

