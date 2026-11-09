import sys
sys.dont_write_bytecode=True
import ast,copy,difflib,hashlib,io,json,os,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W09/W09-99"
C=B/"w09_c19_caller_source_revision_codex/w09c19r2-1a11f08"
checks=[];inputs={}
def ck(label,value):
 checks.append(dict(label=label,passed=bool(value)))
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 e=dict(path=str(Path(ref["path"]).resolve()),sha256=ref["sha256"].removeprefix("sha256:"),bytes=ref["bytes"])
 ck("pin:"+e["path"],pin(e["path"])==e);inputs[e["path"].casefold()]=e;return e
def read(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
def fixed(p,h,b):return verify(dict(path=str(p),sha256=h,bytes=b))
fixed(C/"HDF.json","bfb479d0c441c0eeec03858ee41f1d12150e50c8b7b2cee563c16025525e58f2",6265)
fixed(C/"MF.json","455553ae51eb98c6ead665c7f9dfde0d9e6b5e765418d760f335d5f8845b0ab8",6335)
h=read(C/"HDF.json");mf=read(h["manifest_ref"]["path"])
ck("21-complete-members",mf["member_count"]==len(mf["members"])==21)
for ref in mf["members"]:verify(ref)
for ref in h.values():
 if isinstance(ref,dict) and {"path","sha256","bytes"}<=set(ref):verify(ref)
oldH=read(h["old_source_handoff_ref"]["path"]);oldN=Path(h["old_source_handoff_ref"]["path"]).parent
prevN=Path(h["old_source_independent_handoff_ref"]["path"]).parent
prevH=read(prevN/"HDF.json");verify(prevH["manifest_ref"])
for ref in read(prevH["manifest_ref"]["path"])["members"]:verify(ref)
ck("prior-review-source-accepted",prevH["status"]=="SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_REGISTRATION_AND_ACTUAL")
verify(oldH["manifest_ref"])
for ref in read(oldH["manifest_ref"]["path"])["members"]:verify(ref)
choice=read(h["choice_ref"]["path"]);oldChoice=read(oldN/"source.integration.choice.json")
contract=read(h["calling_contract_ref"]["path"]);proposal=read(h["scope_proposal_ref"]["path"])
for ref in choice["original_input_refs"]+choice["base_driver_refs"]+choice["review_refs"]+list(choice["sources"].values()):verify(ref)
canonical=[R/"execution/v2.4"/(x+".json") for x in ("checkpoint","path_ownership","step_state","commands")]
canonset={str(p.resolve()).casefold() for p in canonical}
canonbefore={p:p.read_bytes() for p in canonical}
for p in canonical:verify(pin(p))
restored=copy.deepcopy(choice);pro=restored.pop("provenance_original");restored.pop("canonical_input_binding")
restored["original_input_refs"]+=pro["canonical_refs"];restored["checkpoint_ref"]=pro["checkpoint_ref"];restored["checkpoint_revision"]=pro["checkpoint_revision"]
ck("choice-complete-inverse",restored==oldChoice)
ck("old-pins-provenance-only",pro["purpose"]=="HISTORICAL_SOURCE_REVIEW_ONLY_NOT_ACTUAL_BINDING" and len(pro["canonical_refs"])==4 and not any(str(Path(x["path"]).resolve()).casefold() in canonset for x in choice["original_input_refs"]))
ck("six-source-and-order-unchanged",choice["sources"]==oldChoice["sources"]==h["exact_original_six_source_refs"] and choice["selected_tests"]==oldChoice["selected_tests"]==["TestW09C19ChainInvalidation","TestW09C19ExplicitOriginAndUnknown"])
ck("five-paths-preserved",choice["fixed_paths"]==oldChoice["fixed_paths"]==contract["fixed_paths"] and len(choice["fixed_paths"])==5)
for label,p in choice["fixed_paths"].items():ck("fresh-path-absent:"+label,not os.path.lexists(p))
ck("contract-counts",len(contract["preparation_argv"])==13 and len(contract["producer_caller_argv"])==17)
ck("no-actual-authority-claimed",not h["execution_grant"] and not h["actual_native_executed"] and not h["actual_vector_created"] and not contract["execution_grant"] and not proposal["formal_acceptance"])
ck("proposal-not-applied",proposal["status"]=="PROPOSAL_NOT_APPLIED")
ck("root-only-registration",proposal["executor"]=="codex:/root" and proposal["scope_semantics_enforced_by"]=="Root registration and review; caller verifies exact registered input vector, not a new inferred authority parser")
ck("same-vector-order-contract",contract["same_vector_in_both_invocations"] is True and contract["expected_future_checkpoint"] is None and not contract["future_failure_ordinal_reservations"])
ck("author-existing-922-not-new",h["mechanical_failures"]==[922])
asts={};texts={};deltas=[]
dump=lambda node:ast.dump(node,include_attributes=False)
for item in read(h["complete_inverse_ref"]["path"]):
 oldref=verify(item["original_ref"]);newref=verify(item["candidate_ref"])
 old=Path(oldref["path"]).read_bytes();new=Path(newref["path"]).read_bytes()
 oldlines=old.decode().splitlines(keepends=True);newlines=new.decode().splitlines(keepends=True)
 ops=item["opcodes"];x=y=0
 for i,o in enumerate(ops):
  ck("inverse-contiguous:"+Path(newref["path"]).name+":"+str(i),o["old_start"]==x and o["new_start"]==y)
  ck("inverse-slices:"+Path(newref["path"]).name+":"+str(i),o["old_lines"]==oldlines[o["old_start"]:o["old_end"]] and o["new_lines"]==newlines[o["new_start"]:o["new_end"]])
  if o["op"]=="equal":ck("inverse-equal:"+str(i),o["old_lines"]==o["new_lines"])
  x=o["old_end"];y=o["new_end"]
 ck("inverse-full-ends:"+newref["path"],x==len(oldlines) and y==len(newlines))
 ck("inverse-full-bytes:"+newref["path"],"".join(s for o in ops for s in o["old_lines"]).encode()==old and "".join(s for o in ops for s in o["new_lines"]).encode()==new)
 ck("independent-diff-identical:"+newref["path"],list(difflib.SequenceMatcher(a=oldlines,b=newlines,autojunk=False).get_opcodes())==[(o["op"],o["old_start"],o["old_end"],o["new_start"],o["new_end"]) for o in ops])
 oa=ast.parse(old);na=ast.parse(new)
 of={x.name:x for x in oa.body if isinstance(x,ast.FunctionDef)};nf={x.name:x for x in na.body if isinstance(x,ast.FunctionDef)}
 for name,node in of.items():ck("existing-function-unchanged:"+Path(newref["path"]).name+":"+name,dump(node)==dump(nf[name]))
 ck("one-added-binding-function:"+newref["path"],set(nf)-set(of)=={"bind_canonical_input_vector"})
 name=Path(newref["path"]).name;texts[name]=new.decode();asts[name]=na
 actual=new.decode().split("def invoke(",1)[1];expected=old.decode().split("def invoke(",1)[1]
 if name.startswith("prepare"):actual=actual.replace("canonical_input_vector_ref=vector_ref,project_identity_ref=pin(identity)","project_identity_ref=pin(identity)",1)
 ck("complete-execution-jobs-finally-unchanged:"+name,actual==expected)
 ck("canonical-refs-and-vector-held:"+name,"canonical_refs+[vector_ref" in new.decode())
 ck("no-fixed-old-cp-runtime:"+name,oldChoice["checkpoint_ref"]["sha256"].encode() not in new and b"==364" not in new and b'choice["checkpoint_ref"]' not in new)
 deltas.append(dict(original_ref=oldref,candidate_ref=newref,changed_blocks=sum(o["op"]!="equal" for o in ops),complete_inverse=True))
save("independent-inverse.json",deltas)
binding=Path(C/"canonical-binding.function.py").read_bytes();bt=ast.parse(binding)
ck("binding-function-only",len(bt.body)==1 and isinstance(bt.body[0],ast.FunctionDef) and bt.body[0].name=="bind_canonical_input_vector")
for name,t in asts.items():
 fn=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="bind_canonical_input_vector")
 ck("binding-identical:"+name,dump(fn)==dump(bt.body[0]))
 ck("bind-precedes-first-output:"+name,texts[name].index("vector_ref,canonical_refs=bind_canonical_input_vector")<texts[name].index("assert not O.exists()"))
 ck("acquire-precedes-first-owned-invoke:"+name,texts[name].index(".acquire(")<texts[name].index("def invoke("))
prep=texts["prepare_w09_c19.actual_owned.py"];prod=texts["run_w09_c19.actual_owned.py"]
ck("prepare-six-producer-ten-args","assert len(sys.argv)==7" in prep and "assert len(sys.argv)==11" in prod)
ck("producer-same-vector-before-output",prod.index('assert isolation["canonical_input_vector_ref"]==vector_ref')<prod.index("assert not O.exists()"))
ck("prepare-ready-pins-vector",'checkout_strategy="SOURCE_AND_REQUIRED_CONFIG_ONLY",canonical_input_vector_ref=vector_ref' in prep)
ck("bounded-vector-before-json","stream.read(vector_bytes+1)" in binding.decode() and binding.decode().index("len(raw)==vector_bytes")<binding.decode().index("vector=json.loads(raw)"))
ck("guards-received-original-expected-canonical-pins","frozen += canonical_refs+[vector_ref]" in prep and 'input_refs += canonical_refs+[vector_ref,pin(R/"execution/project_identity.json")]' in prod)
ck("no-process-added-to-binding",not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ("run","Popen","run_owned","system") for x in ast.walk(bt)))
# Execute only the inspected binding FunctionDef with in-memory streams.
memory={};reads=[]
class VPath:
 def __init__(self,p):self.p=Path(p.p if isinstance(p,VPath) else p)
 def resolve(self,strict=False):
  resolved=self.p.resolve()
  if strict:assert str(resolved) in memory
  return VPath(resolved)
 def is_absolute(self):return self.p.is_absolute()
 @property
 def name(self):return self.p.name
 def is_relative_to(self,p):return self.p.is_relative_to(p)
 def __str__(self):return str(self.p)
 def open(self,mode):
  assert mode=="rb"
  class Stream(io.BytesIO):
   def read(self,n=-1):reads.append(n);return super().read(n)
  return Stream(memory[str(self.p)])
ns={"Path":VPath,"R":R,"json":json,"hashlib":hashlib}
exec(compile(ast.Module(body=[bt.body[0]],type_ignores=[]),"<binding-only-in-memory>","exec"),ns)
fn=ns["bind_canonical_input_vector"];vpath=str(N/"canonical-input-vector.json")
def fixture(revision):
 before={p:json.dumps({"revision":revision,"synthetic":p.name}).encode() for p in canonical}
 refs=[dict(path=str(p.resolve()),sha256=hashlib.sha256(before[p]).hexdigest(),bytes=len(before[p])) for p in canonical]
 return before,dict(schema="researchos.w09-c19-canonical-input-vector.v1",checkpoint_revision=revision,refs=refs)
def call(before,vec,**kw):
 raw=json.dumps(vec).encode();path=kw.get("path",vpath);memory[str(Path(path).resolve())]=raw
 cp=next((x for x in vec.get("refs",[]) if x.get("path")==str(canonical[0].resolve())),{})
 return fn(canonical,before,kw.get("cp_sha",cp.get("sha256","0"*64)),kw.get("cp_bytes",cp.get("bytes",1)),kw.get("revision",vec["checkpoint_revision"]),path,kw.get("sha",hashlib.sha256(raw).hexdigest()),kw.get("size",len(raw)))
def rejected(label,before,vec,expected,**kw):
 try:call(before,vec,**kw)
 except AssertionError as e:ck("reject:"+label,str(e)==expected)
 else:ck("reject:"+label,False)
for revision in (3,371):
 before,vec=fixture(revision);vref,refs=call(before,vec)
 ck("dynamic-synthetic:"+str(revision),refs==vec["refs"] and reads[-1]==vref["bytes"]+1)
 before,vec=fixture(revision);vec["refs"].reverse();vref,refs=call(before,vec)
 ck("canonical-order-normalized:"+str(revision),[x["path"] for x in refs]==[str(p.resolve()) for p in canonical])
before,vec=fixture(3)
for label,kw,reason in [
 ("wrong-sha",{"sha":"0"*64},"CANONICAL_VECTOR_PIN"),
 ("bad-hash-format",{"sha":"X"*64},"CANONICAL_VECTOR_HASH_FORMAT"),
 ("short-size",{"size":1},"CANONICAL_VECTOR_PIN"),
 ("long-size",{"size":64000},"CANONICAL_VECTOR_PIN"),
 ("zero-size",{"size":0},"CANONICAL_VECTOR_SIZE"),
 ("bool-size",{"size":True},"CANONICAL_VECTOR_SIZE"),
 ("over-cap",{"size":65537},"CANONICAL_VECTOR_SIZE"),
 ("relative-path",{"path":"canonical-input-vector.json"},"CANONICAL_VECTOR_ABSOLUTE_PATH"),
 ("foreign-root",{"path":str(R/"canonical-input-vector.json")},"CANONICAL_VECTOR_NAMESPACE"),
 ("bad-name",{"path":str(N/"other.json")},"CANONICAL_VECTOR_NAMESPACE"),
 ("cp-sha",{"cp_sha":"0"*64},"CANONICAL_CHECKPOINT_ARGUMENTS"),
 ("cp-bytes",{"cp_bytes":1},"CANONICAL_CHECKPOINT_ARGUMENTS"),
 ("cp-revision",{"revision":4},"CANONICAL_VECTOR_REVISION")]:
 rejected(label,before,vec,reason,**kw)
mutations=[
 ("missing-ref",lambda v:v["refs"].pop(),"CANONICAL_VECTOR_EXACT_FOUR"),
 ("extra-ref",lambda v:v["refs"].append(copy.deepcopy(v["refs"][0])),"CANONICAL_VECTOR_EXACT_FOUR"),
 ("duplicate-ref",lambda v:v["refs"].__setitem__(3,copy.deepcopy(v["refs"][0])),"CANONICAL_REF_FIXED_UNIQUE_PATH"),
 ("foreign-ref",lambda v:v["refs"][3].__setitem__("path",str(R/"AGENTS.md")),"CANONICAL_REF_FIXED_UNIQUE_PATH"),
 ("ref-relative",lambda v:v["refs"][3].__setitem__("path","commands.json"),"CANONICAL_REF_ABSOLUTE_PATH"),
 ("ref-extra",lambda v:v["refs"][3].__setitem__("x",1),"CANONICAL_REF_FIELDS"),
 ("ref-bool-bytes",lambda v:v["refs"][3].__setitem__("bytes",True),"CANONICAL_REF_SIZE"),
 ("ref-cap",lambda v:v["refs"][3].__setitem__("bytes",67108865),"CANONICAL_REF_SIZE"),
 ("ref-hash",lambda v:v["refs"][3].__setitem__("sha256","0"*64),"CANONICAL_REF_PIN"),
 ("schema",lambda v:v.__setitem__("schema","x"),"CANONICAL_VECTOR_SCHEMA"),
 ("extra-field",lambda v:v.__setitem__("latest",True),"CANONICAL_VECTOR_FIELDS"),
 ("zero-rev",lambda v:v.__setitem__("checkpoint_revision",0),"CANONICAL_VECTOR_REVISION"),
 ("bool-rev",lambda v:v.__setitem__("checkpoint_revision",True),"CANONICAL_VECTOR_REVISION"),
 ("cp-json-rev",lambda v:v.__setitem__("checkpoint_revision",4),"CANONICAL_CHECKPOINT_REVISION")]
for label,mutation,reason in mutations:
 bad=copy.deepcopy(vec);mutation(bad);rejected(label,before,bad,reason)
for p in canonical:
 changed=dict(before);changed[p]+=b" ";rejected("changed:"+p.name,changed,vec,"CANONICAL_REF_PIN")
save("synthetic-controls.json",dict(scope="BINDING_FUNCTION_ONLY_IN_MEMORY",actual_vector_written=False,actual_callers_executed=False,read_request_sizes=reads,checks=[x for x in checks if x["label"].startswith(("reject:","dynamic-synthetic:","canonical-order-normalized:"))]))
# OS read guard holds immutable inputs; canonical shared state observed only.
gp=R/"execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
graw=gp.read_bytes()
ck("accepted-guard-source",hashlib.sha256(graw).hexdigest()=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
verify(pin(gp));verify(pin(sys.executable));verify(pin(__file__))
g=types.ModuleType("w09r2_independent_guard");g.__file__=str(gp);sys.modules[g.__name__]=g;exec(compile(graw,str(gp),"exec"),g.__dict__)
for m in list(sys.modules.values()):
 for field in ("__file__","__cached__"):
  p=getattr(m,field,None)
  if p and Path(p).is_file():verify(pin(p))
guard=g.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
guard.acquire([v for k,v in inputs.items() if k not in canonset])
try:
 for v in inputs.values():ck("post-read-pin:"+v["path"],pin(v["path"])==v)
 for p,raw in canonbefore.items():ck("canonical-unchanged:"+p.name,p.read_bytes()==raw)
finally:cleanup=guard.close()
save("sourceguard.final.json",cleanup)
ck("guard-closed",cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0)
save("input-pins.json",list(inputs.values()))
save("checks.json",dict(count=len(checks),passed=sum(x["passed"] for x in checks),checks=checks))
save("review-result.json",dict(status="SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_REGISTRATION_VECTOR_AND_ACTUAL" if all(x["passed"] for x in checks) else "REQUEST_CHANGES",checks=len(checks),input_count=len(inputs),failures=[x for x in checks if not x["passed"]],source_resource_gate="PASS_CONDITIONAL_ON_ROOT_CONCRETE_SCOPE_AND_EXPLICIT_VECTOR",actual_resource_gate="NOT_RUN",formal_consumers="NOT_RUN_REGISTRY_UNBOUND",canonical_current_revision=read(canonical[0])["revision"],actual_execution=False,synthetic_binding_only=True,new_mechanical_failures=[],guard_closed=cleanup["closed"]))
assert all(x["passed"] for x in checks),json.dumps([x for x in checks if not x["passed"]])
print(json.dumps(dict(status="SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_REGISTRATION_VECTOR_AND_ACTUAL",checks=len(checks),inputs=len(inputs),guard_closed=True)))

