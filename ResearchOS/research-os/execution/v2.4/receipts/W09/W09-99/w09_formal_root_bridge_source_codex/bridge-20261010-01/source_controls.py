"""Finite author controls: imports only the bridge, never Main or runtime stages."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import types
N=Path(__file__).resolve().parent
P=N/"w09_root_bridge.source.py"
raw=P.read_bytes()
tree=ast.parse(raw,str(P))
m=types.ModuleType("bridge_source_control_subject");m.__file__=str(P)
exec(compile(tree,str(P),"exec"),m.__dict__)
results=[]
def yes(name,value):
    if not value: raise AssertionError(name)
    results.append({"name":name,"status":"PASS","kind":"PURE_OR_STATIC_ONLY"})
def rejects(name,call,code):
    try: call()
    except ValueError as error: yes(name,code in str(error))
    else: raise AssertionError(name+": accepted")
rejects("duplicate_json",lambda:m.decode('{"a":1,"a":2}'),"DUPLICATE_JSON_KEY")
rejects("nonfinite_json",lambda:m.decode('{"a":NaN}'),"NONFINITE_JSON")
rejects("current4_empty",lambda:m.current4([]),"CURRENT4")
rejects("timezone_required",lambda:m.stamp("2026-10-10T00:00:00"),"TIMEZONE_REQUIRED")
yes("strict_json_preserves_decimal_integer",m.decode("134359787460741284")==134359787460741284)
yes("formal_ref_has_exactly_two_keys",m.ref2({"path":"p","sha256":"a","bytes":1})=={"path":"p","sha256":"a"})
yes("exact_four_new_routes",len(m.NEW)==4 and all(r[2]!="C19" for r in m.NEW))
yes("exact_six_total_routes",len(m.ROUTES)==len(set(m.ROUTES))==6)
yes("fixed_CM40_pin",m.TRUSTED["execution/v2.4/commands.json"]==("12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97",67323))
yes("ten_runtime_stages",set(m.STAGES)=={"seed","propose","activate","consume","roles","publish-registration","assemble","capture","check","derive"})
old_doc=m.document
m.document=lambda ref:{"schema":"wrong"}
rejects("root_gate_stops_before_engine",lambda:m.root_request({},"consume"),"ROOT_REQUEST")
m.document=old_doc
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
def calls(name,attr):
    return [n for n in ast.walk(functions[name]) if isinstance(n,ast.Call)
            and ((isinstance(n.func,ast.Attribute) and n.func.attr==attr) or
                 (isinstance(n.func,ast.Name) and n.func.id==attr))]
yes("single_owned_dispatch_call",len(calls("consume","run_owned"))==1)
yes("no_direct_process_api",not any(isinstance(n,(ast.Import,ast.ImportFrom)) and
   ((isinstance(n,ast.ImportFrom) and n.module in {"subprocess","sqlite3"}) or
    (isinstance(n,ast.Import) and any(a.name in {"subprocess","sqlite3"} for a in n.names))) for n in ast.walk(tree)))
source=raw.decode()
yes("Main_owner_verifier_only",len(calls("check","verify_owner"))==1 and len(calls("derive","derive_formal_cases"))==1)
yes("fixed_live_SS_derive",any(isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name)
    and n.value.id=="CANON" and isinstance(n.slice,ast.Constant) and n.slice.value==2
    for n in ast.walk(calls("derive","derive_formal_cases")[0])))
observe=[n.lineno for n in ast.walk(functions["consume"]) if isinstance(n,ast.Assign)
         and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=="record"
                 and isinstance(t.slice,ast.Constant) and t.slice.value=="observation" for t in n.targets)]
hashlines=[n.lineno for n in calls("consume","pin")]
yes("process_observation_before_stream_hash",len(observe)==1 and min(hashlines)>observe[0])
yes("process_receipt_before_stream_hash",'save(out / (str(index)+".process.json"), record)' in source)
yes("capture_requires_original_backend",all(x in source for x in (
   'payload["author"]==VERIFIER','meta["timestamp"]==message["timestamp"]',
   'message["metadata"]["client_authored"] is False','stream.seek(offset); line=stream.readline()')))
yes("no_role_or_index_silent_overwrite",'"ROOT_PUBLICATION_REQUIRED"' in source and
    'with path.open("xb")' in source and '"REGISTRY_SLOT_CAS"' in source)
yes("partial_child_failure_stops",'"FIRST_CHILD_FAILURE_STOP"' in source and '"PRECHILD_CAS"' in source)
yes("source_never_creates_accepted_owner",not any(isinstance(n,ast.Dict) and
     any(isinstance(k,ast.Constant) and k.value=="status" and isinstance(v,ast.Constant)
         and v.value=="ACCEPTED" for k,v in zip(n.keys,n.values())) for n in ast.walk(tree)))
report={"schema":"researchos.w09-root-bridge-finite-author-controls.v1",
        "status":"PASS","controls":results,"count":len(results),
        "subject":{"path":str(P),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)},
        "Main_modules_executed":False,"runtime_stages_executed":[],
        "Native_Go_SQL_model_dispatcher_TP_verify_owner_derive_calls":0,
        "formal_acceptance":False}
with (N/"source-controls.json").open("x",encoding="utf-8") as out:
    json.dump(report,out,ensure_ascii=False,indent=2);out.write("\n")
print(json.dumps({"controls":len(results),"status":"PASS","subject_sha256":report["subject"]["sha256"]}))

