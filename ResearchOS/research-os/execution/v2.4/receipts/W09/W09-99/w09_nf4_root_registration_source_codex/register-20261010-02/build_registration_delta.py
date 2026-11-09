"""Continue the preserved successful registrar Source into a new NF5 namespace."""
import ast,copy,difflib,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;OLD=N.parent/'register-20261010-01';W=N.parent.parent
NF=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-05'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def replace(s,a,b):
 if a not in s and '\n' in a:a=a.replace('\n','\r\n');b=b.replace('\n','\r\n')
 assert a in s,('EXACT_REPLACE',a)
 return s.replace(a,b)
def write_source(name,changes):
 original=(OLD/name).read_bytes().decode();text=original
 for a,b in changes:text=replace(text,a,b)
 ast.parse(text,filename=name)
 edits=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,original,text,autojunk=False).get_opcodes():
  if tag!='equal':edits.append(dict(old_start=i,old_end=j,new_start=k,new_end=l,before=original[i:j],after=text[k:l]))
 restored=text
 for e in reversed(edits):restored=restored[:e['new_start']]+e['before']+restored[e['new_end']:]
 assert restored==original
 (N/name).write_bytes(text.encode());return dict(file=name,base_ref=ref(OLD/name),candidate_ref=ref(N/name),inverse_edits=edits)
source=copy.deepcopy(doc(OLD/'input-pins.json'));pins=source['refs']
for key,name in {'NF_hdf':'HDF.json','NF_mf':'MF.json','NF_contract':'root-calling-contract.json','NF_choice':'source.choice.json','NF_runtime':'full_w09_runtime.source.py','NF_prepare':'prepare_full_w09.source.py','NF_run':'run_full_w09.source.py','NF_launcher':'full_w09_launcher.source.py','NF_blueprint':'compiler-source-blueprint.json'}.items():pins[key]=ref(NF/name)
put(N/'input-pins.json',source)
choice=doc(NF/'source.choice.json')
inputs=[ref(OLD/n) for n in ('input-pins.json','register_w09_adoption.source.py','adoption_core.source.py','root-calling-contract.source.json','delta-controls.json')]+[pins[k] for k in pins if k.startswith('NF_')]
inputs+=[choice['common'][k] for k in ('resource_parent_ref','resource_owner_ref','resource_audit_ref')]
gr=pins['guard'];raw=Path(gr['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==gr['sha256']
gm=types.ModuleType('nf5_registration_guard');gm.__file__=gr['path'];exec(compile(raw,gr['path'],'exec'),gm.__dict__)
g=gm.SourceReadGuard(total_cap=256*1024*1024);g.acquire(inputs)
try:
 core=write_source('adoption_core.source.py',[
 ('fullw09-20261010-04','fullw09-20261010-05'),
 ("'source21','generation'):","'source21','generation','resource_parent_ref','resource_owner_ref','resource_audit_ref'):")])
 oldpin=ref(OLD/'input-pins.json')['sha256'];newpin=ref(N/'input-pins.json')['sha256']
 caller=write_source('register_w09_adoption.source.py',[(oldpin,newpin),
 ("OUTPUT_BASE=W/'w09_nf4_root_registration_root'","OUTPUT_BASE=W/'w09_nf5_root_registration_root'"),
 ("    scopes=core.make_native_scopes(request,pins,choice,contract)","    resource_refs=ctx['native'].validate_scratch_parent(choice['common'])\n    ctx['refs'].extend(resource_refs)\n    scopes=core.make_native_scopes(request,pins,choice,contract)")])
 contract=copy.deepcopy(doc(OLD/'root-calling-contract.source.json'))
 contract['source_bindings']={k:ref(N/name) for k,name in {'caller_ref':'register_w09_adoption.source.py','core_ref':'adoption_core.source.py'}.items()}
 contract.update(input_pins_ref=ref(N/'input-pins.json'),existing_native_contract_ref=pins['NF_contract'],
  generation='fullw09-20261010-05',native_scratch_parent='C:\\Users\\yqyyds\\.researchos\\w09-native-v5',
  scratch_parent_gate='Exact physical C parent/owner/project and real Root resource host audit are reobserved by NF5 under request/model guards. Resource-only witness is not an execution grant.',
  resource_parent_ref=choice['common']['resource_parent_ref'],resource_owner_ref=choice['common']['resource_owner_ref'],
  resource_audit_ref=choice['common']['resource_audit_ref'],formal_consumer_actual_TEMP_TMP='C:\\Users\\yqyyds\\.researchos\\w09-native-v5',
  prior_successful_partial_source_refs=[ref(OLD/n) for n in ('register_w09_adoption.source.py','adoption_core.source.py','input-pins.json','root-calling-contract.source.json')],
  prior_successful_controls_ref=ref(OLD/'delta-controls.json'),prior_controls_rerun=False,
  interface_schema_note='The four-selector registrar v1 schema is retained; generation and exact NF5 Source references distinguish this version.')
 contract['CLI']['prefix'][-1]=str(N/'register_w09_adoption.source.py');contract['CLI']['entrypoint']=str(N/'register_w09_adoption.source.py')
 put(N/'root-calling-contract.source.json',contract)
 put(N/'source-delta.json',dict(schema='researchos.nf5-registration-reference-delta.v1',source_deltas=[core,caller],
  exact_source_inverse=True,previous_partial_is_sealed=False,previous_successful_controls_ref=ref(OLD/'delta-controls.json'),
  old_controls_rerun=False,actual_TP_calls=0,actual_Main_writes=0,actual_Canon_writes=0))
finally:
 closed=g.close();put(N/'source-guard.closed.json',closed)
 assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
print(json.dumps(dict(status='NF5_REGISTRAR_SOURCE_BUILT',caller_ref=ref(N/'register_w09_adoption.source.py'),core_ref=ref(N/'adoption_core.source.py'),contract_ref=ref(N/'root-calling-contract.source.json')),ensure_ascii=False))

