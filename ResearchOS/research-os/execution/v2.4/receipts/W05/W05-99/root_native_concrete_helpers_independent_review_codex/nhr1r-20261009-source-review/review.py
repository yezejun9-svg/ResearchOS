import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,re,copy
from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parents[1]
N=B/"root_native_concrete_phase_helpers_revision_codex/nhr1-1a11e7f5205729390aaee9f47b28ce6"
OLD=B/"root_native_concrete_phase_helpers_revision_codex/nh-1a11e7f5205729390aaee9f47b28ce6"
PRIOR=B/"root_native_concrete_helpers_independent_review_codex/nhr-20261009-source-review"
API=B/"integration_codex/native-broker4-positive-root-api-1791513411000/root_public_api_broker4.actual.py"
Q=B/"integration_codex/native-temp-positive-root-api-1791509017626/inspection-positive.json"
refs={};checks=[]
def read(p):
    p=Path(p).resolve();raw=p.read_bytes();refs[str(p)]=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));return raw
def pin(p):
    p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def check(name,ok):
    checks.append(dict(name=name,passed=bool(ok)));assert ok,name
def write(name,obj):
    with (O/name).open("x",encoding="utf-8",newline="\n") as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write("\n")
for name,h,z in [("HDF.json","151045d795d4ac73a7e00f74a290f051583f11582017c608ac8a526c6051b328",3265),("MF.json","f545b924574565a8141bc5a42761cee6f2b1efca5b08b3dea418f0a30a0ec5c5",5049),("root_concrete_approval_helper.py","122f586885a2f3cd8141f4697175655d03441667603fc378cdac662e21a65ac2",29098)]:
    raw=read(N/name);check("fixed:"+name,(hashlib.sha256(raw).hexdigest(),len(raw))==(h,z))
mf=json.loads(read(N/"MF.json"));check("14-manifest-members",len(mf["members"])==14)
for name,r in mf["members"].items():
    raw=read(r["path"]);check("member:"+name,(hashlib.sha256(raw).hexdigest(),len(raw))==(r["sha256"],r["bytes"]))
prior=json.loads(read(PRIOR/"HDF.json"));read(PRIOR/"report.md");finding=json.loads(read(PRIOR/"finding.NHR-001.json"))
check("non-author-prior-finding-chain",prior["status"]=="REQUEST_CHANGES" and finding["id"]=="NHR-001")
old=read(OLD/"root_concrete_approval_helper.py");new=read(N/"root_concrete_approval_helper.py")
check("base-frozen-original",hashlib.sha256(old).hexdigest()=="853cbd80e0603d7f8134833319d8579065639a1dcd2839976d4f8874e6b0cb18" and len(old)==28426)
check("base-copy-exact",read(N/"base/root_concrete_approval_helper.py")==old)
b=old.decode("utf-8");c=new.decode("utf-8")
r=json.loads(read(N/"source-replacements.json"))
check("one-new-helper-block",c.count(r["new_helper"])==1)
check("one-retained-call-change",c.count(r["new_call"])==1 and b.count(r["old_call"])==1)
check("whole-byte-exact-inverse",c.replace(r["new_helper"],"",1).replace(r["new_call"],r["old_call"],1).encode()==old)
bt=ast.parse(b);ct=ast.parse(c)
bd={x.name:x for x in bt.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
cd={x.name:x for x in ct.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
check("only-new-declaration",set(cd)-set(bd)=={"inspection_database_ref"})
check("no-old-declaration-removed",set(bd)<=set(cd))
for name,node in bd.items():
    if name!="retained":
        check("exact-old-declaration:"+name,ast.get_source_segment(b,node)==ast.get_source_segment(c,cd[name]))
check("retained-only-validator-change",ast.get_source_segment(c,cd["retained"]).replace(r["new_call"],r["old_call"],1)==ast.get_source_segment(b,bd["retained"]))
for name in ("public_evidence_archive.py","calling-contract.json"):
    check("exact-copy:"+name,read(N/name)==read(OLD/name))
qraw=read(Q);check("real-inspection-pin",(hashlib.sha256(qraw).hexdigest(),len(qraw))==("7dfe6d48b8bfb560a31ea7830a22497440e2f62a1a27a3b325b54a37038d3409",98591))
q=json.loads(qraw)
allowed={"require","canonical","plain","inspection_database_ref"}
ns=dict(Path=Path,re=re)
exec(compile(ast.Module(body=[cd[k] for k in ("require","canonical","plain","inspection_database_ref")],type_ignores=[]),str(N/"root_concrete_approval_helper.py"),"exec"),ns)
ref=q["database_ref"];original=copy.deepcopy(ref)
check("real-ordinary-ref-accepted-byte-values-unchanged",ns["inspection_database_ref"](ref)==original and ref==original)
def reject(name,value,which="inspection_database_ref"):
    try:ns[which](value)
    except (ValueError,TypeError,KeyError):check(name,True);return
    check(name,False)
for name,key,value in [
("prefixed","sha256","sha256:"+ref["sha256"]),
("double-prefixed","sha256","sha256:sha256:"+ref["sha256"]),
("upperhex","sha256",ref["sha256"].upper()),
("63chars","sha256",ref["sha256"][:-1]),
("65chars","sha256",ref["sha256"]+"0"),
("trailing-newline","sha256",ref["sha256"]+"\n"),
("nonhex","sha256","g"*64),
("hash-integer","sha256",1),
("bool-length","bytes",True),
("float-length","bytes",1.0),
("negative-length","bytes",-1),
("string-length","bytes",str(ref["bytes"])),
("relative-path","path","source.sqlite"),
("null-in-path","path",ref["path"]+"\0"),
("path-integer","path",123),
("dotdot-path","path",str(Q.parent/"x"/".."/"source.sqlite"))]:
    reject("ordinary-reject:"+name,dict(ref,**{key:value}))
reject("ordinary-reject-extra-role",dict(ref,role="database"))
reject("ordinary-reject-missing-size",{k:v for k,v in ref.items() if k!="bytes"})
reject("ordinary-reject-array",list(ref.items()))
for value in (0,ref["bytes"],2**64):
    # Metadata-only Python integer: arbitrary precision, never coerced into native uint.
    check("nonnegative-integer-no-cast:"+str(value),ns["inspection_database_ref"](dict(ref,bytes=value))["bytes"]==value)
check("public-prefixed-pin-still-accepted",ns["plain"](dict(ref,sha256="sha256:"+ref["sha256"]))["sha256"]=="sha256:"+ref["sha256"])
reject("public-still-rejects-bare-hash",ref,"plain")
reject("public-still-rejects-double-prefix",dict(ref,sha256="sha256:sha256:"+ref["sha256"]),"plain")
api=read(API).decode("utf-8");api_tree=ast.parse(api)
producer=next(n for n in api_tree.body if isinstance(n,ast.FunctionDef) and n.name=="pin_raw")
pn=dict(Path=Path,hashlib=hashlib)
exec(compile(ast.Module(body=[producer],type_ignores=[]),str(API),"exec"),pn)
producer_ref=pn["pin_raw"](Q,b"public_source_only_control")
check("actual-producer-shape-exact",set(producer_ref)=={"path","sha256","bytes"})
check("actual-producer-bare-hash",producer_ref["sha256"]==hashlib.sha256(b"public_source_only_control").hexdigest())
check("actual-producer-output-accepted",ns["inspection_database_ref"](producer_ref)==producer_ref)
check("current-API-database-field-uses-producer",'"database_ref":pin(db_path)' in api and 'return pin_raw(path,path.read_bytes())' in api)
newfunc=cd["inspection_database_ref"]
calls=[ast.unparse(n.func) for n in ast.walk(newfunc) if isinstance(n,ast.Call)]
check("new-validator-has-no-IO-cast-normalization",set(calls)<= {"require","type","set","re.fullmatch","canonical"})
check("retained-still-requires-real-file-and-TEMP",'db.is_file() and db.is_relative_to(canonical(cfg["Environment"]["TEMP"]))' in ast.get_source_segment(c,cd["retained"]))
check("closed-NHR001-Source-only",finding["pure_source_reproduction"]["message"]=="SHA256 pin")
write("sourceguard.initial.json",dict(refs=list(refs.values()),method="read-only byte SHA256 before-after"))
for x in list(refs.values()):check("unchanged:"+Path(x["path"]).name,pin(x["path"])==x)
write("sourceguard.final.json",dict(refs=list(refs.values()),unchanged=True))
write("review-result.json",dict(status="SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL",finding="NHR-001",finding_status="CLOSED_IN_SOURCE",checks_count=len(checks),checks=checks,source_inputs=len(refs),actual_API_entrypoint_executed=False,candidate_main_executed=False,extracted_metadata_functions_only=True,actual_Git_Go_native_SQL_model=False,private_or_database_read=False,approval_generated=False,Main_canonical_write=False,new_mechanical_failures=[],formal_acceptance=False))
print(json.dumps(dict(status="SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL",finding="NHR-001 CLOSED_IN_SOURCE",checks=len(checks),inputs=len(refs))))

