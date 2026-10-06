from pathlib import Path
import importlib.util,json,copy,os
p=Path(os.environ["W07_CANDIDATE_ROOT"])/"execution/v2.4/formal_profile_w07_test.py";s=importlib.util.spec_from_file_location("dependency_helpers",p);m=importlib.util.module_from_spec(s);exec(compile(p.read_bytes(),str(p),"exec"),m.__dict__)
m.W07RawControls.setUpClass()
try:
 t=m.W07RawControls();context,tools=t.product_control();proof=copy.deepcopy(t.template);source=copy.deepcopy(t.source_before);omitted="internal/canonical/jcs.go";assert omitted in source;del source[omitted]
 proof["source_before_ref"]=proof["source_after_ref"]=t.write_control("omitted-source.json",source)
 vector=m.PROFILE._document(m.API,t.reader(),proof["version_vector_ref"]);vector["source"]=source;proof["version_vector_ref"]=t.write_control("omitted-vector.json",vector)
 inventory=m.PROFILE._bytes(m.API,t.reader(),proof["compilation_inputs_ref"]).decode();decoder=json.JSONDecoder();offset=0;packages=[];removed=[]
 while offset<len(inventory):
  if inventory[offset].isspace():offset+=1;continue
  pkg,offset=decoder.raw_decode(inventory,offset)
  if pkg.get("ImportPath")=="researchos.local/research-os/internal/canonical":removed.append(pkg)
  else:packages.append(pkg)
 assert len(removed)==1
 raw=t.write_bytes("omitted-go-list.json",b"\n".join(json.dumps(x).encode() for x in packages))
 proof["compilation_inputs_ref"]=raw;inv=m.PROFILE._document(m.API,t.reader(),t.compilation_ref);inv["stdout_ref"]=raw;context["compilation_invocation_ref"]=t.write_control("omitted-go-list-invocation.json",inv);context["proof_ref"]=t.write_control("omitted-proof.json",proof)
 reader=t.reader()
 try:m.PROFILE.product(m.API,reader,context,tools);reader.finish();result="ACCEPTED"
 except Exception as e:result="REJECTED: "+str(e)
 print(json.dumps({"classification":"FULL_PRODUCT_FUNCTION_NEGATIVE_NOT_REGISTERED_CURRENT","omitted_source":omitted,"omitted_go_list_package":removed[0]["ImportPath"],"original_source_file_still_present":(t.repo/omitted).exists(),"remaining_package_import_references":sum(removed[0]["ImportPath"] in x.get("Imports",[]) for x in packages),"result":result},indent=2))
finally:m.W07RawControls.tearDownClass()
