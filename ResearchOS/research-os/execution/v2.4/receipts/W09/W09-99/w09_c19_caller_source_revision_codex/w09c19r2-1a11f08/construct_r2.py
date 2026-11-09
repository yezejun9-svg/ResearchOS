import ast,copy,difflib,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
OLD=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_caller_source_codex/w09c19-1a11f08'
REV=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_caller_independent_review_codex/w09c19r-20261009-source-review'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def put(name,raw):
 raw=raw if isinstance(raw,bytes) else raw.encode('utf-8')
 with (N/name).open('xb') as f:f.write(raw)
 return pin(N/name)
def js(name,obj):return put(name,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
for p,sha,size in [(OLD/'handoff.json','93b284118a5f099fc9281930416cdd2671666db409b17791bec16473c06aa72e',2931),(OLD/'manifest.json','85f0727b213249252fdaa19d3e183f480860b97cbb691350139ce0eb7503e2d8',8040),(REV/'HDF.json','0be8fe36aeac57fd03082391153486a70318efa0054a5ead5d14c44663da871a',3870),(REV/'MF.json','c9258e3c4238c2790855f04f9a497622ca8ea9f1d6d655ffebc9c652a6398f8f',6356)]:
 q=pin(p);assert q['sha256']==sha and q['bytes']==size
C=json.loads((OLD/'source.integration.choice.json').read_bytes())
canonical=[R/'execution/v2.4'/(name+'.json') for name in ('checkpoint','path_ownership','step_state','commands')]
guards=[OLD/'handoff.json',OLD/'manifest.json',OLD/'prepare_w09_c19.actual_owned.py',OLD/'run_w09_c19.actual_owned.py',OLD/'source.integration.choice.json',REV/'HDF.json',REV/'MF.json',REV/'report.md']+[Path(ref['path']) for ref in C['original_input_refs']]
before={str(p):p.read_bytes() for p in guards}
js('input-pins.before.json',[pin(p) for p in guards])
binding='''def bind_canonical_input_vector(canonical,before,checkpoint_sha,checkpoint_bytes,checkpoint_revision,vector_path,vector_sha,vector_bytes):
 assert len(vector_sha)==64 and all(c in "0123456789abcdef" for c in vector_sha), "CANONICAL_VECTOR_HASH_FORMAT"
 assert type(vector_bytes) is int and 0<vector_bytes<=65536, "CANONICAL_VECTOR_SIZE"
 path=Path(vector_path)
 assert path.is_absolute(), "CANONICAL_VECTOR_ABSOLUTE_PATH"
 path=path.resolve(strict=True)
 assert path.name=="canonical-input-vector.json" and path.is_relative_to((R/"execution/v2.4/receipts/W09/W09-99").resolve()), "CANONICAL_VECTOR_NAMESPACE"
 with path.open("rb") as stream:raw=stream.read(vector_bytes+1)
 assert len(raw)==vector_bytes and hashlib.sha256(raw).hexdigest()==vector_sha, "CANONICAL_VECTOR_PIN"
 vector=json.loads(raw)
 assert isinstance(vector,dict) and set(vector)=={"schema","checkpoint_revision","refs"}, "CANONICAL_VECTOR_FIELDS"
 assert vector["schema"]=="researchos.w09-c19-canonical-input-vector.v1", "CANONICAL_VECTOR_SCHEMA"
 assert type(vector["checkpoint_revision"]) is int and vector["checkpoint_revision"]==checkpoint_revision and checkpoint_revision>0, "CANONICAL_VECTOR_REVISION"
 refs=vector["refs"]
 assert isinstance(refs,list) and len(refs)==4, "CANONICAL_VECTOR_EXACT_FOUR"
 fixed={str(p.resolve()):p for p in canonical};observed={}
 for ref in refs:
  assert isinstance(ref,dict) and set(ref)=={"path","sha256","bytes"}, "CANONICAL_REF_FIELDS"
  assert isinstance(ref["path"],str) and Path(ref["path"]).is_absolute(), "CANONICAL_REF_ABSOLUTE_PATH"
  key=str(Path(ref["path"]).resolve())
  assert key in fixed and key not in observed, "CANONICAL_REF_FIXED_UNIQUE_PATH"
  assert isinstance(ref["sha256"],str) and len(ref["sha256"])==64 and all(c in "0123456789abcdef" for c in ref["sha256"]), "CANONICAL_REF_HASH_FORMAT"
  assert type(ref["bytes"]) is int and 0<ref["bytes"]<=64*1024*1024, "CANONICAL_REF_SIZE"
  data=before[fixed[key]]
  assert len(data)==ref["bytes"] and hashlib.sha256(data).hexdigest()==ref["sha256"], "CANONICAL_REF_PIN"
  observed[key]={"path":key,"sha256":ref["sha256"],"bytes":ref["bytes"]}
 assert set(observed)==set(fixed), "CANONICAL_VECTOR_FIXED_SET"
 cp=observed[str(canonical[0].resolve())]
 assert cp["sha256"]==checkpoint_sha and cp["bytes"]==checkpoint_bytes, "CANONICAL_CHECKPOINT_ARGUMENTS"
 assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision, "CANONICAL_CHECKPOINT_REVISION"
 return {"path":str(path),"sha256":vector_sha,"bytes":vector_bytes},[observed[str(p.resolve())] for p in canonical]

'''
def replace(text,old,new):
 assert text.count(old)==1,old
 return text.replace(old,new,1)
deltas=[]
for name in ('prepare_w09_c19.actual_owned.py','run_w09_c19.actual_owned.py'):
 raw=(OLD/name).read_bytes();text=raw.decode();text=replace(text,'def pin(p):',binding+'def pin(p):')
 if name.startswith('prepare'):
  text=replace(text,'assert len(sys.argv)==4, "usage: prepare.py CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION"','assert len(sys.argv)==7, "usage: prepare.py CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION VECTOR_PATH VECTOR_SHA256 VECTOR_BYTES"')
  text=replace(text,'assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision==364\nassert checkpoint_sha=="6ed349c5b8380ad6b099ae2237c33513f4e2717afc7789398968366a8cddf6dd" and checkpoint_bytes==4237636','assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision\nvector_ref,canonical_refs=bind_canonical_input_vector(canonical,before,checkpoint_sha,checkpoint_bytes,checkpoint_revision,sys.argv[4],sys.argv[5],int(sys.argv[6]))')
  text=replace(text,'dict(refs=[pin(p) for p in canonical],revision=checkpoint_revision,formal_acceptance=False)','dict(refs=canonical_refs,canonical_input_vector_ref=vector_ref,revision=checkpoint_revision,formal_acceptance=False)')
  text=replace(text,'frozen += [pin(p) for p in canonical]','frozen += canonical_refs+[vector_ref]')
  text=replace(text,'checkout_strategy="SOURCE_AND_REQUIRED_CONFIG_ONLY",project_identity_ref=pin(identity)','checkout_strategy="SOURCE_AND_REQUIRED_CONFIG_ONLY",canonical_input_vector_ref=vector_ref,project_identity_ref=pin(identity)')
 else:
  text=replace(text,'assert len(sys.argv)==8, "usage: validate.py CHOICE_SHA256 CHOICE_BYTES CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION ISOLATION_READY_SHA256 ISOLATION_READY_BYTES"','assert len(sys.argv)==11, "usage: validate.py CHOICE_SHA256 CHOICE_BYTES CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION ISOLATION_READY_SHA256 ISOLATION_READY_BYTES VECTOR_PATH VECTOR_SHA256 VECTOR_BYTES"')
  text=replace(text,'assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision==364\nassert verify(choice["checkpoint_ref"])["sha256"]==checkpoint_sha and choice["checkpoint_ref"]["bytes"]==checkpoint_bytes','assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision\nvector_ref,canonical_refs=bind_canonical_input_vector(canonical,before,checkpoint_sha,checkpoint_bytes,checkpoint_revision,sys.argv[8],sys.argv[9],int(sys.argv[10]))\nassert isolation["canonical_input_vector_ref"]==vector_ref, "ISOLATION_CANONICAL_VECTOR_MISMATCH"')
  text=replace(text,'dict(refs=[pin(p) for p in canonical],revision=checkpoint_revision,formal_acceptance=False)','dict(refs=canonical_refs,canonical_input_vector_ref=vector_ref,revision=checkpoint_revision,formal_acceptance=False)')
  text=replace(text,'input_refs += [pin(p) for p in canonical]+[pin(R/"execution/project_identity.json")]','input_refs += canonical_refs+[vector_ref,pin(R/"execution/project_identity.json")]')
 candidate=put(name,text);ast.parse(text)
 old=raw.decode().splitlines(keepends=True);new=text.splitlines(keepends=True);ops=[]
 for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():ops.append(dict(op=tag,old_start=a,old_end=b,new_start=c,new_end=d,old_lines=old[a:b],new_lines=new[c:d]))
 assert ''.join(line for op in ops for line in op['old_lines']).encode()==raw
 assert ''.join(line for op in ops for line in op['new_lines']).encode()==text.encode()
 deltas.append(dict(original_ref=pin(OLD/name),candidate_ref=candidate,opcodes=ops))
js('caller-complete-inverse.json',deltas)
new_choice=copy.deepcopy(C)
fixed={str(p.resolve()) for p in canonical}
historical=[ref for ref in C['original_input_refs'] if str(Path(ref['path']).resolve()) in fixed]
assert len(historical)==4
new_choice['original_input_refs']=[ref for ref in C['original_input_refs'] if str(Path(ref['path']).resolve()) not in fixed]
new_choice['provenance_original']={'canonical_refs':historical,'checkpoint_ref':new_choice.pop('checkpoint_ref'),'checkpoint_revision':new_choice.pop('checkpoint_revision'),'purpose':'HISTORICAL_SOURCE_REVIEW_ONLY_NOT_ACTUAL_BINDING'}
new_choice['canonical_input_binding']={'schema':'researchos.w09-c19-canonical-input-vector.v1','path_rule':'Root explicit absolute canonical-input-vector.json under execution/v2.4/receipts/W09/W09-99','required_paths':[str(p.resolve()) for p in canonical],'required_ref_keys':['path','sha256','bytes'],'exact_ref_count':4,'checkpoint_revision':'EXPLICIT_CLI_AND_VECTOR_EQUALITY','implicit_latest':False,'same_vector_for_prepare_and_producer':True}
new_choice_ref=js('source.integration.choice.json',new_choice)
put('canonical-binding.function.py',binding)
js('choice-delta.json',dict(original_ref=pin(OLD/'source.integration.choice.json'),candidate_ref=new_choice_ref,old_choice=C,new_choice=new_choice,only_changes=['remove four canonical refs from original_input_refs','move old canonical and CP pins to provenance_original','add explicit canonical_input_binding contract']))
for p,raw in before.items():assert Path(p).read_bytes()==raw
js('construction-result.json',dict(status='SOURCE_ONLY_CONSTRUCTED',old_source_and_review_unchanged=True,canonical_unchanged=True,actual_execution=False,original_six_sources_unchanged=new_choice['sources']==C['sources'],all_five_actual_paths_unchanged=new_choice['fixed_paths']==C['fixed_paths']))
print(json.dumps(dict(status='SOURCE_ONLY_CONSTRUCTED',namespace=str(N),new_choice_ref=new_choice_ref),ensure_ascii=False))
