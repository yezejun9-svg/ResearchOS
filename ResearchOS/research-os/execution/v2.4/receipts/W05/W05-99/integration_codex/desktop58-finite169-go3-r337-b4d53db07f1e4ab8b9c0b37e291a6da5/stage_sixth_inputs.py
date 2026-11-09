import sys,os,json,hashlib,copy,ast
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path("D:/作品集/ResearchOS/research-os")
BASE=Path(__file__).resolve().parent
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def checked(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    need(".." not in p.parts and p.is_relative_to(ROOT) and p.resolve()==p.absolute(),"canonical Root path")
    for c in (p,*p.parents):
        if os.path.lexists(c):need(not c.is_symlink() and not(getattr(c.lstat(),"st_file_attributes",0)&0x400),"reparse")
        if c==ROOT:break
    return p
def pin(p):
    p=checked(p);b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def raw(r):
    need(set(r)=={"path","sha256","bytes"},"exact ref")
    p=checked(r["path"]);b=p.read_bytes()
    need(len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"],"pin drift "+r["path"])
    return b
def doc(r):return json.loads(raw(r))
def put(name,b):
    p=checked(BASE/name);need(p.parent==BASE and not os.path.lexists(p),"fresh staging file")
    with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
    return pin(p)
def save(name,d):return put(name,(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf8"))
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,"pinned flags")
cfg=json.loads((BASE/"literal-inputs.original.json").read_bytes())
need(cfg["before"]==[336,164,614] and cfg["after"][:2]==[337,165],"closed lease before and sixth revision")
need(cfg["after"][2]==cfg["before"][2]+len(cfg["pending_origin_refs"]),"explicit finite origin cut")
old=doc(cfg["seed_ref"]);q=copy.deepcopy(old)
review=doc(cfg["constructor_review_ref"])
need(review["decision"]=="READY_SOURCE_PREPARATION_ONLY" and review["requested_changes"]==[],"actual non-author constructor review")
mf=doc(cfg["constructor_manifest_ref"])
for r in mf["members"]:raw(r)
closure=doc(cfg["old_lease_closure_verified_ref"])
need(closure["after"]==cfg["before"] and closure["old_lease_closed_failed"] is True and closure["execution_grant"] is False,"actual old lease closure CAS")
refs=cfg["pending_origin_refs"]
seen=set()
for r in refs:
    doc(r);need(r["sha256"] not in seen,"distinct original origins");seen.add(r["sha256"])
refs=[pin(checked(r["path"])) for r in refs]
copies=[]
for r in cfg["canonical_refs"]:
    b=raw(r);need((ROOT/r["path"]).read_bytes()==b,"current canonical before")
    copies.append(put(Path(r["path"]).stem+".snapshot-before.json",b))
cp,ow=map(doc,copies[:2])
need([cp["revision"],ow["revision"],len(cp["failure_counters"])]==cfg["before"],"exact before tuple")
need(ow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]["state"]=="FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD","closed predecessor lease")
uid=cfg["sixth_uid"]
need(uid=="b4d53db07f1e4ab8b9c0b37e291a6da5" and BASE==ROOT/cfg["sixth_rel"],"exact sixth Root allocation")
allocation={"run_uuid":uid,"registration_namespace":str(BASE)}
for key,group in [("new_output_root","desktop58_finite_executor_codex"),("new_wrapper_root","desktop58_finite_launcher_codex"),("new_authorization_root","desktop58_finite_authorization_codex"),("new_grant_preflight_root","desktop58_finite_grant_preflight_codex")]:
    allocation[key]=str(ROOT/"execution/v2.4/receipts/W13/W13-03"/group/uid)
allocation["new_export_root"]=str(ROOT/".local"/("desktop58-export-"+uid))
for k,v in allocation.items():
    if k not in ("run_uuid","registration_namespace"):need(not os.path.lexists(checked(v)),"fresh future Root leaf")
need(not os.path.lexists(checked(cfg["caller_output"])),"fresh caller Root leaf")
q.update(before=cfg["before"],after=cfg["after"],canonical_copies=copies,pending_origin_refs=refs,allocation=allocation)
q["controller_review_path"]=str(ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_current_bound_scope_independent_review_codex"/uid/"review.json")
for row in q["negative_alias_declarations"]:
    need(row["path"].count(old["allocation"]["run_uuid"])==2,"negative alias literal identity")
    row["path"]=row["path"].replace(old["allocation"]["run_uuid"],uid)
metadata=[]
for r in old["metadata_code_refs"]:
    b=raw(r);name=Path(r["path"]).name
    if name in ("scope_builder.py","prepare.py","register.py","run.py","seal.py","grant_preflight.py"):
        ast.parse(b);metadata.append(put(name,b))
    else:metadata.append(r)
need(len(metadata)==8,"metadata8")
q["metadata_code_refs"]=metadata;q.update(cfg["wldp_fields"])
ctor=raw(cfg["constructor_ref"]);ast.parse(ctor)
ctor_ref=put("construct_root_inputs.desktop58.wldp.py",ctor)
allowed={"before","after","canonical_copies","pending_origin_refs","allocation","controller_review_path","negative_alias_declarations","metadata_code_refs"}
for k,v in old.items():
    if k not in allowed:need(q[k]==v,"protected old field "+k)
need(set(q)-set(old)=={"wldp_static_ref","wldp_candidate_report_ref"},"two new pinned Windows resource fields")
allocref=save("root-allocation.actual.json",{"schema":"researchos.root-literal-allocation.v1","actor":"codex:/root","before":cfg["before"],"after":cfg["after"],"allocation":allocation,"caller_output":cfg["caller_output"],"execution_authorized":False})
cb=save("canonical-before.json",{"entries":[{"canonical_path":r["path"],"ref":c} for r,c in zip(cfg["canonical_refs"],copies)]})
mr=save("metadata-code-refs.selected.json",{"entries":metadata})
qr=save("root-construction.parameters.desktop58.json",q)
audit=save("literal-staging.actual.json",{"schema":"researchos.desktop58-literal-staging.v1","actor":"codex:/root","seed_ref":cfg["seed_ref"],"constructor_ref":ctor_ref,"constructor_review_ref":cfg["constructor_review_ref"],"old_lease_closure_verified_ref":cfg["old_lease_closure_verified_ref"],"canonical_before_ref":cb,"request_ref":qr,"metadata_ref":mr,"allocation_ref":allocref,"changed_fields":sorted(allowed|{"wldp_static_ref","wldp_candidate_report_ref"}),"protected_fields_equal":True,"before":cfg["before"],"after":cfg["after"],"origin_count":len(refs),"canonical_writes":0,"product_calls":0,"formal_increment":0,"old_scope_rerun":False})
print(json.dumps({"request_ref":qr,"constructor_ref":ctor_ref,"audit_ref":audit,"allocation_ref":allocref,"canonical_before_ref":cb,"pending_origin_refs":refs,"before":cfg["before"],"after":cfg["after"]},ensure_ascii=False))
