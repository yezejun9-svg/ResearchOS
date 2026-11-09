import ast,copy,hashlib,json,difflib,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).parent
OLD=R/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_lease_closure_source_preparation_codex/70461c211bf5457d98d054bf62703fe1"
def pin(p):
 b=p.read_bytes();return {"path":p.relative_to(R).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,d):
 with (O/n).open("xb") as f:f.write(d if isinstance(d,bytes) else (json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(O/n)
old=(OLD/"lease_closure.sixth.proposed.py").read_bytes()
assert hashlib.sha256(old).hexdigest()=="0ae8c1488afffeabc25af674546859878c21b6ae80ef45f08696e198a448a9f5"
text=old.decode()
oldid="b8aebcea794f4d83b6371e90814f8e3c";newid="c550b87c595048dca4187601e57ecf24"
assert text.count(oldid)==3
text=text.replace(oldid,newid)
needle='    ob="/card_path_bindings/W13-03/subtasks/desktop58_finite_validation/"\n'
addition='''    for key,qkey in (("desktop58_finite_validation_failed_closure_review_ref","closure_review_ref"),("desktop58_finite_validation_failed_closure_root_ref","closure_report_ref")):
        expected=q[qkey]
        need(type(expected)is dict and set(expected)=={"path","sha256","bytes"},"fixed closure exact3key ref")
        actual=newcp["work_in_progress"][key]
        need(type(actual)is dict and set(actual)=={"path","sha256","bytes"} and actual==expected,"new closure ref exact q pin")
        ca.update("/work_in_progress/"+key+"/"+leaf for leaf in ("path","sha256","bytes"))
'''
assert text.count(needle)==1
text=text.replace(needle,addition+needle)
new=text.encode();tree=ast.parse(new);oldtree=ast.parse(old)
src=write("lease_closure.sixth.v2.proposed.py",new)
assert text.replace(addition,"").replace(newid,oldid).encode()==old
funcs=lambda t:{x.name:x for x in t.body if isinstance(x,ast.FunctionDef)}
fd,od=funcs(tree),funcs(oldtree)
segments=lambda data,t:{x.name:ast.get_source_segment(data,x) for x in t.body if isinstance(x,ast.FunctionDef)}
ns,os=segments(text,tree),segments(old.decode(),oldtree)
unchanged=[x for x in fd if x!="desired_values"]
assert all(ast.dump(fd[x],include_attributes=False)==ast.dump(od[x],include_attributes=False) and ns[x]==os[x] for x in unchanged)
q=json.loads((OLD/"request.template.json").read_bytes());q["namespace"]=q["namespace"].replace(oldid,newid);q["run_uuid"]=newid;q["source_ref"]=src
assert q["amended_at"] is None
write("request.template.json",q)
delta=list(difflib.ndiff(old.decode().splitlines(keepends=True),text.splitlines(keepends=True)))
assert "".join(difflib.restore(delta,1)).encode()==old and "".join(difflib.restore(delta,2)).encode()==new
write("whole-byte-inverse.json",{"base_ref":pin(OLD/"lease_closure.sixth.proposed.py"),"candidate_ref":src,"ndiff":delta,"added_exact_source":addition,"literal_old":oldid,"literal_new":newid,"literal_occurrences":3,"all_other_functions_byte_AST_unchanged":unchanged})
cp=json.loads((R/"execution/v2.4/checkpoint.json").read_bytes());ow=json.loads((R/"execution/v2.4/path_ownership.json").read_bytes())
for r in q["canonical_before"]:
 raw=(R/r["path"]).read_bytes();assert len(raw)==r["bytes"] and hashlib.sha256(raw).hexdigest()==r["sha256"]
# Only the authorized pure metadata functions are compiled/executed, never candidate module/main.
subset=ast.Module(body=[copy.deepcopy(fd[n]) for n in ("need","differences","desired_values")],type_ignores=[])
env={"copy":copy}
exec(compile(ast.fix_missing_locations(subset),"<pure-metadata-functions-only>","exec"),env)
rows=[]
for r in q["pending_origin_refs"]:
 p=Path(r["path"]);p=p if p.is_absolute() else R/p;raw=p.read_bytes();assert len(raw)==r["bytes"] and hashlib.sha256(raw).hexdigest()==r["sha256"]
 rows.append({"origin_key":r["sha256"],"evidence_ref":r,"original_payload":json.loads(raw),"counter_reset":False,"counted_once":True,"automatic_retry":False})
tq=copy.deepcopy(q);tq["amended_at"]="2026-10-08T00:00:00+00:00"
nc,no,cd,dow=env["desired_values"](tq,cp,ow,rows)
cases=[{"name":"actual current CP/OW positive six nested ref leaves","pass":all("/work_in_progress/"+k+"/"+l in cd for k in ("desktop58_finite_validation_failed_closure_review_ref","desktop58_finite_validation_failed_closure_root_ref") for l in ("path","sha256","bytes")) and len(nc["failure_counters"])==635 and nc["failure_counters"][:617]==cp["failure_counters"]}]
def expect_reject(name,query,copy_impl=copy):
 env["copy"]=copy_impl
 try:env["desired_values"](query,cp,ow,rows)
 except RuntimeError as e:cases.append({"name":name,"pass":True,"actual_rejection":str(e)})
 else:cases.append({"name":name,"pass":False})
 finally:env["copy"]=copy
bad=copy.deepcopy(tq);bad["closure_review_ref"]["unexpected"]=True;expect_reject("extra closure ref key rejects",bad)
bad=copy.deepcopy(tq);del bad["closure_report_ref"]["bytes"];expect_reject("missing closure ref key rejects",bad)
class MutatingCopies:
 def __init__(self,mutate):self.n=0;self.mutate=mutate
 def deepcopy(self,value):
  self.n+=1;v=copy.deepcopy(value)
  if self.n==1:self.mutate(v)
  return v
expect_reject("unrelated CP head mutation rejects",tq,MutatingCopies(lambda v:v.__setitem__("head","foreign")))
expect_reject("unrelated WIP field mutation rejects",tq,MutatingCopies(lambda v:v["work_in_progress"].__setitem__("not_allowed",True)))
# Fault-inject update directly so the exact selected desired_values body observes a wrong pin.
class WrongRefUpdate(dict):
 def update(self,*a,**k):
  d=dict(*a,**k)
  if "desktop58_finite_validation_failed_closure_review_ref" in d:
   d["desktop58_finite_validation_failed_closure_review_ref"]=dict(d["desktop58_finite_validation_failed_closure_review_ref"],sha256="0"*64)
  super().update(d)
expect_reject("allowed ref leaf wrong pin rejects",tq,MutatingCopies(lambda v:v.__setitem__("work_in_progress",WrongRefUpdate(v["work_in_progress"]))))
assert all(x["pass"] for x in cases)
assert not list((R/q["namespace"]).iterdir())
write("pure-metadata-controls.json",{"schema":"researchos.pure-metadata-controls.v1","actor":"codex:/root/w05_merge_review","extracted_functions":["need","differences","desired_values"],"candidate_module_imported":False,"candidate_main_executed":False,"actual_draft":False,"actual_CAS":False,"actual_Git":False,"cases":cases,"positive_changed_checkpoint_pointers":cd,"positive_changed_ownership_pointers":dow,"actual_current_four":[pin(R/x["path"]) for x in q["canonical_before"]]})
write("static-audit.json",{"schema":"researchos.source-static-audit.v1","source_ref":src,"whole_inverse":True,"other_functions_unchanged":unchanged,"original_13helpers_unchanged":True,"new_output_still_empty":True,"actual_draft":False,"actual_CAS":False,"actual_product_calls":0,"controls":len(cases),"new_failure_count":0})
print(json.dumps({"source_ref":src,"controls":cases,"changed_pointers":cd,"unchanged_function_count":len(unchanged)},ensure_ascii=False))

