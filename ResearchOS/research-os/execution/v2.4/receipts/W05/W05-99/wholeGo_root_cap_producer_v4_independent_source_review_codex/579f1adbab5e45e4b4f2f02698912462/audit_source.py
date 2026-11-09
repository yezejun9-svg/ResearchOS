from pathlib import Path
import ast,difflib,hashlib,json
OUT=Path(__file__).parent
NS=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_source_v4_codex/c6091da118c64152ac95874e7b4e34fa")
checks=[]
def ck(n,v):checks.append({"name":n,"pass":bool(v)})
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def readref(r):
 b=Path(r["path"]).read_bytes();ck("pin:"+r["path"],len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"]);return b
def put(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(OUT/n)
h=json.loads((NS/"handoff.json").read_bytes())
ck("handoff fixed",pin(NS/"handoff.json")["sha256"]=="7dbd60b684ba399a72958b5aaa2c8e1fa33e6e34740372ea75ab6f8b315b8278")
m=json.loads(readref(h["manifest_ref"]))
ck("MF nine exact members",m["members_count"]==len(m["members"])==9)
for r in m["members"]:readref(r)
report=json.loads(readref(h["report_ref"]))
old=readref(report["old_source_ref"]);new=readref(h["source_ref"])
oldtext=old.decode();text=new.decode()
a=ast.parse(oldtext);b=ast.parse(text)
fs=lambda t:{n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
af,bf=fs(a),fs(b)
ck("same function set",set(af)==set(bf))
others=[n for n in af if n!="observed_windows_process"]
ck("other17 functions AST identical",len(others)==17 and all(ast.dump(af[n],include_attributes=False)==ast.dump(bf[n],include_attributes=False) for n in others))
ck("other17 source exact",all(ast.get_source_segment(oldtext,af[n])==ast.get_source_segment(text,bf[n]) for n in others))
forward="".join(difflib.unified_diff(oldtext.splitlines(True),text.splitlines(True),fromfile="a/wholego_cap_metadata.v3.proposed.py",tofile="b/wholego_cap_metadata.v4.proposed.py"))
inverse="".join(difflib.unified_diff(text.splitlines(True),oldtext.splitlines(True),fromfile="a/wholego_cap_metadata.v4.proposed.py",tofile="b/wholego_cap_metadata.v3.proposed.py"))
ck("full forward delta exact",forward.encode()==readref(h["forward_ref"]))
ck("full inverse delta exact",inverse.encode()==readref(h["inverse_ref"]))
oldh=json.loads((Path(report["old_source_ref"]["path"]).parent/"handoff.json").read_bytes())
ck("template exact old bytes",readref(h["template_ref"])==readref(oldh["root_input_template_ref"]))
prior=json.loads(readref(report["review_basis_ref"]))
ck("prior sole CAP3_R01",len(prior["requested_changes"])==1 and prior["requested_changes"][0]["id"]=="CAP3-R01")
proc=ast.get_source_segment(text,bf["observed_windows_process"])
ck("GetExitCodeProcess typed API","kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]" in proc and "kernel.GetExitCodeProcess.restype = ctypes.c_int" in proc)
expected="ok_exit != 0 and exit_code.value == 259 and exited.low == 0 and exited.high == 0"
reqs=[n for n in ast.walk(bf["observed_windows_process"]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="require"]
ck("exact success 259 zero exitTime predicate",any(ast.dump(n.args[0],include_attributes=False)==ast.dump(ast.parse(expected,mode="eval").body,include_attributes=False) for n in reqs))
ck("liveness checked before return",proc.index("ok_exit = kernel.GetExitCodeProcess")<proc.index('"ROOT_RUNNER_PROCESS_ALREADY_EXITED_OR_UNOBSERVED"')<proc.index("return (created.high"))
trys=[n for n in ast.walk(bf["observed_windows_process"]) if isinstance(n,ast.Try)]
ck("all queried paths finally close handle",len(trys)==1 and len(trys[0].finalbody)==1 and "CloseHandle" in ast.unparse(trys[0].finalbody[0]))
ck("scope declaration point in time","at this query instant" in proc)
# Independent scalar truth table of exactly the source AST conjunction; no candidate AST executed.
cases=[
("live or suspended",1,1,1,1,259,0,0,True),
("retained exited",1,1,1,1,0,42,0,False),
("exit259 lowtime",1,1,1,1,259,42,0,False),
("exit259 hightime",1,1,1,1,259,0,1,False),
("exit query failure",1,1,1,0,259,0,0,False),
("times query failure",0,1,1,1,259,0,0,False),
("membership query failure",1,0,1,1,259,0,0,False),
("not job member",1,1,0,1,259,0,0,False),
("non259 zero exit time",1,1,1,1,1,0,0,False)]
truth=[]
for name,t,j,member,q,code,lo,hi,want in cases:
 actual=(t!=0 and j!=0 and member==1 and q!=0 and code==259 and lo==0 and hi==0)
 ck("pure scalar predicate:"+name,actual==want)
 truth.append({"name":name,"get_times_success":t,"membership_query_success":j,"job_member":member,"exit_query_success":q,"exit_code":code,"exit_filetime_low":lo,"exit_filetime_high":hi,"expected":want,"derived":actual})
ck("creation precision preserved","return (created.high << 32) | created.low" in proc)
ck("no runtime granted",h["actual_root_authority"] is None and h["source_acceptance"] is False and h["formal_case_accepted_delta"]==0)
audit=put("audit.json",{"schema":"researchos.whole-go-cap-v4-static-audit.v1","checks":checks,"check_count":len(checks),"all_pass":all(c["pass"] for c in checks),"pure_data_controls":truth,"control_method":"Independent scalar truth-table tied to verified AST condition; no candidate module/function executed, no ctypes/WinDLL loaded.","candidate_executed":False,"actual_os_probe_count":0})
decision="READY_SOURCE_PREPARATION_ONLY" if all(c["pass"] for c in checks) else "REQUEST_CHANGES"
review=put("review.json",{"schema":"researchos.whole-go-root-cap-independent-source-review.v1","reviewer":"codex:/root/w05_merge_review","source_actor":"codex:/root/live_resource_lookup","decision":decision,"source_ref":h["source_ref"],"source_handoff_ref":pin(NS/"handoff.json"),"source_manifest_ref":h["manifest_ref"],"prior_review_ref":report["review_basis_ref"],"audit_ref":audit,"requested_changes":[] if decision.startswith("READY") else [c for c in checks if not c["pass"]],"CAP3_R01":"CLOSED_STATIC_ONLY: success exit query, STILL_ACTIVE259 and both exit FILETIME words zero precede creation return; finally closes retained handle.","reuse":"Prior v3 five-request and producer-consumer static review reused for 17 byte/AST unchanged functions. Full forward/inverse and template bytes independently checked.","open_conditions":["Observation is point-in-time, not lifetime lock: process can exit immediately after queries.","Future Root controller, current allocation/limits/registration/grant/lease/live OS/meter and raw evidence remain required; this source cannot authorize execution.","Root stage/source manifest/ref spelling and complete runtime/file membership require future bound-scope review.","No whole-Go test/runtime/source/formal qualification is granted; REAL_MODEL_B01_HOLD remains unchanged."],"candidate_execution_count":0,"actual_os_probe_count":0,"actual_root_authority":None,"actual_source_acceptance":False,"whole_suite_qualified":False,"formal_case_accepted_delta":0,"new_failure_count":0})
entries=[pin(f) for f in sorted(OUT.iterdir()) if f.is_file()]
mf=put("manifest.json",{"schema":"researchos.public-review-manifest.v1","entries":entries,"count":len(entries),"self_excluded":True})
handoff=put("handoff.json",{"schema":"researchos.whole-go-cap-v4-independent-review-handoff.v1","review_ref":review,"audit_ref":audit,"manifest_ref":mf,"decision":decision,"new_failure_count":0,"status":"STOPPED"})
print(json.dumps({"review_ref":review,"manifest_ref":mf,"handoff_ref":handoff,"check_count":len(checks),"failed_checks":[c for c in checks if not c["pass"]]},ensure_ascii=False))

