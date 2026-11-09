import ast,json,hashlib,types,copy,difflib
from datetime import datetime,timezone,timedelta
from pathlib import Path
N=Path(__file__).resolve().parent
B=N.parents[1]
O=B/"root_native_concrete_phase_helpers_revision_codex/nh-1a11e7f5205729390aaee9f47b28ce6"
V=B/"root_native_concrete_helpers_independent_review_codex/nhr-20261009-source-review"
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(r):
 a=pin(r["path"]);assert a["sha256"]==r["sha256"].removeprefix("sha256:") and a["bytes"]==r["bytes"];return a
def save(n,v):
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def rawsave(n,raw):
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(raw)
 return pin(p)
known=[(O/"HDF.json","a4b3cbdf5fd493b1cb4ba2d0252d55561f8ce06b749c1809c0da56765074e3f4",4004),(O/"MF.json","6efe5918eb5c3ab68fc1e7d744108ab1c418748dbd8ffa0de4ca60a4ab8c09b0",7330),(V/"HDF.json","4a4d352a0828e18114a6acf7ca6fad85d5ab27fbe1a8b00177d488832a1308da",2387)]
known.append((V/"MF.json","d9c69b592e317768e21ab5f4d595d7164b1eae29ba2652ee9c50e0004646fc13",2820))
refs=[verify(dict(path=str(p),sha256=h,bytes=z)) for p,h,z in known]
for namespace in (O,V):
 mf=json.loads((namespace/"MF.json").read_bytes())
 vals=mf["members"].values() if isinstance(mf["members"],dict) else mf["members"]
 refs.extend(verify(r) for r in vals)
finding=json.loads((V/"finding.NHR-001.json").read_bytes())
assert finding["id"]=="NHR-001"
refs += [verify(finding["producer_source_ref"]),verify(finding["historical_real_inspection_ref"])]
q=json.loads(Path(finding["historical_real_inspection_ref"]["path"]).read_bytes())
old=(O/"root_concrete_approval_helper.py").read_bytes()
assert pin(O/"root_concrete_approval_helper.py")["sha256"]=="853cbd80e0603d7f8134833319d8579065639a1dcd2839976d4f8874e6b0cb18"
addition='''def inspection_database_ref(ref):
    """Validate the Root API inspection's ordinary unprefixed receipt pin.
    This is metadata-only: never read the retained database or normalize its
    digest into a public RawPin.
    """
    require(type(ref) is dict and set(ref) == {"path", "sha256", "bytes"}, "inspection database receipt pin shape")
    require(type(ref["bytes"]) is int and ref["bytes"] >= 0, "inspection database receipt length")
    require(type(ref["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]), "inspection database bare SHA256")
    canonical(ref["path"])
    return {k: ref[k] for k in ("path", "sha256", "bytes")}

'''
anchor="class Inputs:\n"
text=old.decode();assert text.count(anchor)==1
candidate=text.replace(anchor,addition+anchor,1)
oldcall='db = canonical(plain(q["database_ref"])["path"])'
newcall='db = canonical(inspection_database_ref(q["database_ref"])["path"])'
assert candidate.count(oldcall)==1
candidate=candidate.replace(oldcall,newcall,1)
inverse=candidate.replace(newcall,oldcall,1).replace(addition,"",1)
assert inverse.encode()==old
oldtree=ast.parse(text);newtree=ast.parse(candidate)
defs=lambda tree:{node.name:ast.dump(node,include_attributes=False) for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
olddefs,newdefs=defs(oldtree),defs(newtree)
assert set(newdefs)-set(olddefs)=={"inspection_database_ref"}
unchanged=[name for name in olddefs if name!="retained"]
assert all(olddefs[name]==newdefs[name] for name in unchanged)
# AST equivalence after undoing only the retained database validator call.
retained_fixed=ast.parse(candidate.replace(newcall,oldcall,1))
assert defs(retained_fixed)["retained"]==olddefs["retained"]
rawsave("base/root_concrete_approval_helper.py",old)
candidate_ref=rawsave("root_concrete_approval_helper.py",candidate.encode())
archive_ref=rawsave("public_evidence_archive.py",(O/"public_evidence_archive.py").read_bytes())
assert pin(O/"public_evidence_archive.py")["sha256"]==archive_ref["sha256"]
rawsave("calling-contract.json",(O/"calling-contract.json").read_bytes())
rawsave("NHR-001.patch","".join(difflib.unified_diff(text.splitlines(True),candidate.splitlines(True),fromfile="original/root_concrete_approval_helper.py",tofile="revision/root_concrete_approval_helper.py")).encode())
save("source-replacements.json",dict(new_helper=addition,old_call=oldcall,new_call=newcall,exact_inverse_bytes=True))
m=types.ModuleType("nhr1_source_only");m.__file__=str(N/"root_concrete_approval_helper.py");exec(compile(candidate,m.__file__,"exec"),m.__dict__)
# Re-run the exact former 27-control block on the new module; no main invocation.
prior=(O/"verify-source.py").read_text(encoding="utf-8")
block=prior[prior.index("results=[]"):prior.index("# Static no subprocess")]
D=json.loads((O/"author-inputs.json").read_bytes())
scope=dict(m=m,Path=Path,D=D,copy=copy,datetime=datetime,timezone=timezone,timedelta=timedelta,refs=refs,pin=pin)
exec(compile(block,"<unchanged-27-controls>","exec"),scope)
results=scope["results"];assert len(results)==27
prior_results=json.loads((O/"source-controls.json").read_bytes())["controls"]
assert results==prior_results
extra=[]
def ok(name,fn):
 fn();extra.append(dict(name=name,outcome="PASS"))
def reject(name,fn):
 try:fn()
 except (ValueError,TypeError,KeyError):extra.append(dict(name=name,outcome="PASS_EXPECTED_REJECTION"))
 else:raise AssertionError(name)
bare=q["database_ref"]
ok("actual_Root_API_inspection_bare_hash_accepted",lambda:m.require(m.exact(m.inspection_database_ref(bare),bare),"same bare ref returned"))
prefixed=dict(bare,sha256="sha256:"+bare["sha256"])
reject("ordinary_inspection_rejects_prefixed_hash",lambda:m.inspection_database_ref(prefixed))
reject("ordinary_inspection_rejects_role_field",lambda:m.inspection_database_ref(dict(bare,role="database")))
reject("ordinary_inspection_rejects_bool_size",lambda:m.inspection_database_ref(dict(bare,bytes=True)))
reject("ordinary_inspection_rejects_float_size",lambda:m.inspection_database_ref(dict(bare,bytes=float(bare["bytes"]))))
reject("ordinary_inspection_rejects_negative_size",lambda:m.inspection_database_ref(dict(bare,bytes=-1)))
reject("ordinary_inspection_rejects_short_hash",lambda:m.inspection_database_ref(dict(bare,sha256=bare["sha256"][:-1])))
reject("ordinary_inspection_rejects_uppercase_hash",lambda:m.inspection_database_ref(dict(bare,sha256=bare["sha256"].upper())))
reject("ordinary_inspection_rejects_relative_path",lambda:m.inspection_database_ref(dict(bare,path="source.sqlite")))
ok("public_RawPin_prefixed_still_accepted",lambda:m.require(m.exact(m.plain(prefixed),prefixed),"same public ref returned"))
reject("public_RawPin_rejects_actual_bare_inspection_hash",lambda:m.plain(bare))
reject("public_RawPin_rejects_double_prefix",lambda:m.plain(dict(prefixed,sha256="sha256:"+prefixed["sha256"])))
# Producer AST confirms its receipt contract without opening any database.
api=Path(finding["producer_source_ref"]["path"]).read_text(encoding="utf-8")
apitree=ast.parse(api)
producer=next(n for n in apitree.body if isinstance(n,ast.FunctionDef) and n.name=="pin_raw")
pns={"Path":Path,"hashlib":hashlib}
exec(compile(ast.Module(body=[producer],type_ignores=[]),"<actual-API-pin-raw>","exec"),pns)
shape=pns["pin_raw"](bare["path"],b"public synthetic contract bytes")
ok("actual_API_pin_raw_contract_accepted_without_DB_read",lambda:m.inspection_database_ref(shape))
save("source-controls.json",dict(prior_27_controls=results,prior_controls_byte_equivalent_results=True,new_contract_controls=extra,total_controls=27+len(extra),actual_historical_inspection_ref=finding["historical_real_inspection_ref"],database_read=False,actual_API_entrypoint_called=False,new_native_SQL_model_Git_Go=False))
save("static-preservation.json",dict(exact_inverse_bytes=True,unchanged_AST_functions_and_classes=unchanged,retained_only_database_validator_call_changed=True,new_helper="inspection_database_ref",public_RawPin_plain_AST_unchanged=True,archive_byte_identical=True,calling_contract_byte_identical=True,all_other_semantics_preserved=True))
refs=list({r["path"].casefold():r for r in refs}.values())
for r in refs:
 a=pin(r["path"]);assert a["sha256"]==r["sha256"].removeprefix("sha256:") and a["bytes"]==r["bytes"]
save("sourceguard.final.json",dict(refs=refs,all_unchanged=True,method="exact read-only Source before-after pins",database_read=False))
print(json.dumps(dict(status="NHR001_SOURCE_REVISION_PREPARED",candidate=candidate_ref,archive=archive_ref,original_controls=27,new_controls=len(extra),input_refs=len(refs),new_native_SQL_model_Git_Go=False)))

