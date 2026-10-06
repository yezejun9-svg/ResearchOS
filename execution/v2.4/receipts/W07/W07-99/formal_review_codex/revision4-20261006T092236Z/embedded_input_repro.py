from pathlib import Path
import importlib.util,json,copy,os,hashlib
p=Path(os.environ["W07_CANDIDATE_ROOT"])/"execution/v2.4/formal_profile_w07_test.py";s=importlib.util.spec_from_file_location("embed_helpers",p);m=importlib.util.module_from_spec(s);exec(compile(p.read_bytes(),str(p),"exec"),m.__dict__)
m.W07RawControls.setUpClass()
try:
 t=m.W07RawControls();context,tools=t.product_control();proof=copy.deepcopy(t.template);source=copy.deepcopy(t.source_before);name="internal/domain/contracts/new-project-rules-v24.md";assert name in source;del source[name]
 proof["source_before_ref"]=proof["source_after_ref"]=t.write_control("missing-embed-source.json",source)
 vector=m.PROFILE._document(m.API,t.reader(),proof["version_vector_ref"]);vector["source"]=source;proof["version_vector_ref"]=t.write_control("missing-embed-vector.json",vector);context["proof_ref"]=t.write_control("missing-embed-proof.json",proof)
 (t.repo/name).write_bytes(b"changed embedded project rules; no product recapture")
 for ref in context["version_vector"]["source_files"]:
  if ref["path"]==name:ref["sha256"]=hashlib.sha256((t.repo/name).read_bytes()).hexdigest()
 reader=t.reader()
 try:m.PROFILE.product(m.API,reader,context,tools);reader.finish();result="ACCEPTED"
 except Exception as e:result="REJECTED: "+str(e)
 print(json.dumps({"classification":"FULL_PRODUCT_FUNCTION_NEGATIVE_NOT_REGISTERED_CURRENT","omitted_source":name,"actual_compiled_go_embed_input":True,"only_temporary_fixture_embed_changed":True,"current_context_repins_new_embed_but_proof_stays_old":True,"result":result},indent=2))
finally:m.W07RawControls.tearDownClass()
