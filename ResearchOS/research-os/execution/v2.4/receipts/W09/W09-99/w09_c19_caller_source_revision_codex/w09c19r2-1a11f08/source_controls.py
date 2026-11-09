import ast,copy,hashlib,io,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).resolve().parent
OLD=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_caller_source_codex/w09c19-1a11f08'
C=json.loads((N/'source.integration.choice.json').read_bytes());oldC=json.loads((OLD/'source.integration.choice.json').read_bytes())
checks=[]
def ck(label,value):
 assert value,label
 checks.append(dict(label=label,status='PASS'))
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
before={x['path']:Path(x['path']).read_bytes() for x in json.loads((N/'input-pins.before.json').read_bytes())}
for name in ('prepare_w09_c19.actual_owned.py','run_w09_c19.actual_owned.py'):
 oldraw=(OLD/name).read_bytes();raw=(N/name).read_bytes();oa=ast.parse(oldraw);na=ast.parse(raw)
 of={x.name:ast.dump(x,include_attributes=False) for x in oa.body if isinstance(x,ast.FunctionDef)}
 nf={x.name:ast.dump(x,include_attributes=False) for x in na.body if isinstance(x,ast.FunctionDef)}
 ck('all-existing-functions-AST-unchanged:'+name,all(nf[k]==v for k,v in of.items()))
 ck('only-one-added-binding-function:'+name,set(nf)-set(of)=={'bind_canonical_input_vector'})
 ck('no-fixed-CP364-hash-in-caller:'+name,b'==364' not in raw and oldC['checkpoint_ref']['sha256'].encode() not in raw)
 ck('live-vector-added-to-held-guard:'+name,b'canonical_refs+[vector_ref' in raw)
 ck('exact-CP-sha-bytes-revision-still-required:'+name,b'assert pin(canonical[0])["sha256"]==checkpoint_sha and pin(canonical[0])["bytes"]==checkpoint_bytes' in raw and b'assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision' in raw)
 actual=raw.decode().split('def invoke(',1)[1]
 expected=oldraw.decode().split('def invoke(',1)[1]
 if name.startswith('prepare'):actual=actual.replace('canonical_input_vector_ref=vector_ref,project_identity_ref=pin(identity)','project_identity_ref=pin(identity)',1)
 ck('entire-native-and-cleanup-body-unchanged:'+name,actual==expected)
newprep=(N/'prepare_w09_c19.actual_owned.py').read_text();newrun=(N/'run_w09_c19.actual_owned.py').read_text()
ck('prepare-explicit-six-args','assert len(sys.argv)==7' in newprep)
ck('producer-explicit-ten-args','assert len(sys.argv)==11' in newrun)
ck('same-vector-bound-by-pinned-isolation-ready','assert isolation["canonical_input_vector_ref"]==vector_ref' in newrun)
ck('all-six-v6-and-selected-order-identical',C['sources']==oldC['sources'] and C['selected_tests']==oldC['selected_tests'])
ck('all-five-paths-unchanged',C['fixed_paths']==oldC['fixed_paths'])
ck('all-five-actual-paths-still-absent',all(not Path(x).exists() for x in C['fixed_paths'].values()))
ck('old-four-canonical-preserved-in-provenance',len(C['provenance_original']['canonical_refs'])==4 and C['provenance_original']['checkpoint_ref']==oldC['checkpoint_ref'] and C['provenance_original']['checkpoint_revision']==364)
fixed={str((R/'execution/v2.4'/(x+'.json')).resolve()) for x in ('checkpoint','path_ownership','step_state','commands')}
ck('no-frozen-canonical-used-as-runtime-input',not any(str(Path(x['path']).resolve()) in fixed for x in C['original_input_refs']))
restored=copy.deepcopy(C);pro=restored.pop('provenance_original');restored.pop('canonical_input_binding');restored['original_input_refs']+=pro['canonical_refs'];restored['checkpoint_ref']=pro['checkpoint_ref'];restored['checkpoint_revision']=pro['checkpoint_revision']
ck('complete-choice-inverse-identical',restored==oldC)
for ref in C['sources'].values():
 a=pin(ref['path']);ck('v6-source:'+Path(ref['path']).name,(a['sha256'],a['bytes'])==(ref['sha256'],ref['bytes']))
for item in json.loads((N/'caller-complete-inverse.json').read_bytes()):
 ck('complete-old-byte-inverse:'+Path(item['original_ref']['path']).name,''.join(x for op in item['opcodes'] for x in op['old_lines']).encode()==Path(item['original_ref']['path']).read_bytes())
 ck('complete-new-byte-forward:'+Path(item['candidate_ref']['path']).name,''.join(x for op in item['opcodes'] for x in op['new_lines']).encode()==Path(item['candidate_ref']['path']).read_bytes())

# Execute only the parameter-binding function, replacing file streams with an
# in-memory vector. No caller top level, product/native process, or actual vector.
read_requests=[];memory={}
class VirtualPath:
 def __init__(self,p):self.p=Path(p.p if isinstance(p,VirtualPath) else p)
 def is_absolute(self):return self.p.is_absolute()
 def resolve(self,strict=False):
  p=self.p.resolve()
  if strict:assert str(p) in memory
  return VirtualPath(p)
 @property
 def name(self):return self.p.name
 def is_relative_to(self,p):return self.p.is_relative_to(p)
 def open(self,mode):
  assert mode=='rb'
  raw=memory[str(self.p)]
  class Stream(io.BytesIO):
   def read(self,n=-1):read_requests.append(n);return super().read(n)
  return Stream(raw)
 def __str__(self):return str(self.p)
ns={'Path':VirtualPath,'R':R,'json':json,'hashlib':hashlib}
binding=(N/'canonical-binding.function.py').read_bytes();exec(compile(binding,'<parameter-binding-only>','exec'),ns)
fn=ns['bind_canonical_input_vector']
canonical=[R/'execution/v2.4'/(x+'.json') for x in ('checkpoint','path_ownership','step_state','commands')]
vector_path=str((N/'canonical-input-vector.json').resolve())
def fixture(revision):
 raw={p:json.dumps({'revision':revision,'SYNTHETIC_SOURCE_CONTROL_ONLY':p.name}).encode() for p in canonical}
 refs=[dict(path=str(p.resolve()),sha256=hashlib.sha256(raw[p]).hexdigest(),bytes=len(raw[p])) for p in canonical]
 return raw,dict(schema='researchos.w09-c19-canonical-input-vector.v1',checkpoint_revision=revision,refs=refs)
def invoke(raw,vector,**changes):
 vraw=json.dumps(vector).encode();vp=changes.get('vector_path',vector_path);memory[vp]=vraw
 cp=vector['refs'][0]
 args=[canonical,raw,changes.get('checkpoint_sha',cp['sha256']),changes.get('checkpoint_bytes',cp['bytes']),changes.get('checkpoint_revision',vector['checkpoint_revision']),vp,changes.get('vector_sha',hashlib.sha256(vraw).hexdigest()),changes.get('vector_bytes',len(vraw))]
 return fn(*args)
for revision in (7,11):
 raw,vec=fixture(revision);vref,refs=invoke(raw,vec)
 ck('dynamic-synthetic-revision:'+str(revision),vref['path']==vector_path and refs==vec['refs'])
 ck('bounded-vector-read:'+str(revision),read_requests[-1]==vref['bytes']+1)
def rejected(label,raw,vec,reason,**kw):
 try:invoke(raw,vec,**kw)
 except AssertionError as e:ck(label,str(e)==reason)
 else:raise AssertionError('invalid vector accepted:'+label)
raw,vec=fixture(7)
rejected('wrong-vector-hash',raw,vec,'CANONICAL_VECTOR_PIN',vector_sha='0'*64)
rejected('wrong-vector-size',raw,vec,'CANONICAL_VECTOR_PIN',vector_bytes=1)
rejected('vector-size-cap',raw,vec,'CANONICAL_VECTOR_SIZE',vector_bytes=65537)
rejected('wrong-vector-namespace',raw,vec,'CANONICAL_VECTOR_NAMESPACE',vector_path=str((R/'canonical-input-vector.json').resolve()))
rejected('wrong-vector-basename',raw,vec,'CANONICAL_VECTOR_NAMESPACE',vector_path=str((N/'other.json').resolve()))
for label,mutate,reason in [
 ('missing-canonical',lambda x:x['refs'].pop(),'CANONICAL_VECTOR_EXACT_FOUR'),
 ('extra-canonical',lambda x:x['refs'].append(copy.deepcopy(x['refs'][0])),'CANONICAL_VECTOR_EXACT_FOUR'),
 ('duplicate-canonical',lambda x:x['refs'].__setitem__(3,copy.deepcopy(x['refs'][0])),'CANONICAL_REF_FIXED_UNIQUE_PATH'),
 ('foreign-canonical-path',lambda x:x['refs'][3].__setitem__('path',str(R/'AGENTS.md')),'CANONICAL_REF_FIXED_UNIQUE_PATH'),
 ('extra-ref-key',lambda x:x['refs'][3].__setitem__('owner','invented'),'CANONICAL_REF_FIELDS'),
 ('wrong-ref-hash',lambda x:x['refs'][3].__setitem__('sha256','0'*64),'CANONICAL_REF_PIN'),
 ('bool-ref-bytes',lambda x:x['refs'][3].__setitem__('bytes',True),'CANONICAL_REF_SIZE'),
 ('wrong-vector-revision',lambda x:x.__setitem__('checkpoint_revision',8),'CANONICAL_CHECKPOINT_REVISION'),
 ('extra-vector-key',lambda x:x.__setitem__('latest',True),'CANONICAL_VECTOR_FIELDS')]:
 bad=copy.deepcopy(vec);mutate(bad);rejected(label,raw,bad,reason)
rejected('wrong-explicit-checkpoint-sha',raw,vec,'CANONICAL_CHECKPOINT_ARGUMENTS',checkpoint_sha='0'*64)
rejected('wrong-explicit-checkpoint-bytes',raw,vec,'CANONICAL_CHECKPOINT_ARGUMENTS',checkpoint_bytes=1)
rejected('wrong-explicit-checkpoint-revision',raw,vec,'CANONICAL_VECTOR_REVISION',checkpoint_revision=8)
for index in range(4):
 changed=dict(raw);changed[canonical[index]]+=b' '
 rejected('changed-current-canonical:'+canonical[index].name,changed,vec,'CANONICAL_REF_PIN')
ck('all-source-and-canonical-input-bytes-unchanged',all(Path(p).read_bytes()==raw for p,raw in before.items()))
with (N/'source-controls.result.json').open('xb') as f:f.write((json.dumps(dict(status='PASS_SOURCE_BINDING_ONLY',check_count=len(checks),checks=checks,pure_in_memory_vector_controls=True,actual_vector_created=False,actual_caller_executed=False,native_go_producer_consumer_executed=False,formal_acceptance=False),ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(status='PASS_SOURCE_BINDING_ONLY',check_count=len(checks),actual_execution=False)))
