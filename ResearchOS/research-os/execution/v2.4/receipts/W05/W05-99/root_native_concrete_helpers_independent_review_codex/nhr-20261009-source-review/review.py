import sys
sys.dont_write_bytecode = True
import ast, copy, hashlib, json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

O=Path(__file__).resolve().parent
B=O.parents[1]
N=B/"root_native_concrete_phase_helpers_revision_codex/nh-1a11e7f5205729390aaee9f47b28ce6"
API=B/"integration_codex/native-broker4-positive-root-api-1791513411000/root_public_api_broker4.actual.py"
Q=B/"integration_codex/native-temp-positive-root-api-1791509017626/inspection-positive.json"
refs={}
def pin(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):
    p=Path(p).resolve(); raw=p.read_bytes(); ref=pin(p)
    assert ref["sha256"]==hashlib.sha256(raw).hexdigest()
    refs[str(p)]=ref
    return raw
def write(name,value):
    with (O/name).open("x",encoding="utf-8",newline="\n") as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write("\n")
expected={"HDF.json":("a4b3cbdf5fd493b1cb4ba2d0252d55561f8ce06b749c1809c0da56765074e3f4",4004),"MF.json":("6efe5918eb5c3ab68fc1e7d744108ab1c418748dbd8ffa0de4ca60a4ab8c09b0",7330),"root_concrete_approval_helper.py":("853cbd80e0603d7f8134833319d8579065639a1dcd2839976d4f8874e6b0cb18",28426),"public_evidence_archive.py":("189ebdc33751c4becf98b665e365ba84b0996497c1cb5d04576530c99a7e180c",4618)}
checks=[]
def check(name,ok):
    checks.append(dict(name=name,pass_result=bool(ok)))
    assert ok,name
for name,(h,s) in expected.items():
    raw=read(N/name);check("fixed-pin:"+name,(hashlib.sha256(raw).hexdigest(),len(raw))==(h,s))
mf=json.loads(read(N/"MF.json"))
check("manifest-count",len(mf["members"])==20)
for name,ref in mf["members"].items():
    raw=read(ref["path"])
    check("manifest-member:"+name,(hashlib.sha256(raw).hexdigest(),len(raw))==(ref["sha256"].removeprefix("sha256:"),ref["bytes"]))
for ref in json.loads(read(N/"sourceguard.initial.json"))["refs"]:
    raw=read(ref["path"])
    check("author-input:"+Path(ref["path"]).name,(hashlib.sha256(raw).hexdigest(),len(raw))==(ref["sha256"].removeprefix("sha256:"),ref["bytes"]))
q=json.loads(read(Q));api=read(API).decode("utf-8")
helper=read(N/"root_concrete_approval_helper.py").decode("utf-8")
tree=ast.parse(helper)
allowed={"require","pairs","decode","exact","digest","canonical","plain","guard_closed","native_closed_zero","validity","signed_payload_exact","public_rows","jcs_digest"}
selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in allowed]
ns=dict(hashlib=hashlib,json=json,re=re,Path=Path,datetime=datetime,timezone=timezone,JOB_FLAGS=("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
exec(compile(ast.Module(body=selected,type_ignores=[]),str(N/"root_concrete_approval_helper.py"),"exec"),ns)
def rejects(name,fn,message=None):
    try:fn()
    except (ValueError,TypeError,KeyError) as error:
        check(name,message is None or str(error)==message)
        return dict(type=type(error).__name__,message=str(error))
    check(name,False)

check("API-database-pin-is-raw-hex",bool(re.fullmatch("[0-9a-f]{64}",q["database_ref"]["sha256"])))
check("public-row-pin-is-prefixed",q["before_ref"]["sha256"].startswith("sha256:"))
error=rejects("reproduce-retained-real-API-database-pin",lambda:ns["plain"](q["database_ref"]),"SHA256 pin")
check("candidate-retained-directly-calls-plain", 'canonical(plain(q["database_ref"])["path"])' in helper)
check("current-API-producer-uses-pin", '"database_ref":pin(db_path)' in api and 'sha256=hashlib.sha256(raw).hexdigest()' in api)
rejects("bool-ref-byte-length",lambda:ns["plain"](dict(path=str(Q),sha256="sha256:"+"a"*64,bytes=True)))
rejects("duplicate-json-key",lambda:ns["decode"](b'{"x":1,"x":2}'))
rejects("nonfinite-json",lambda:ns["decode"](b'{"x":NaN}'))
check("exact-bool-versus-integer",ns["exact"](True,1) is False)
result=dict(actual_exit=0,error=None,timed_out=False,owned_child_pid=42244,creation_time_100ns=134359866411023123,job_cleanup={k:True for k in ns["JOB_FLAGS"]})
result["job_cleanup"].update(active_processes_last_observed=0,errors=[])
ns["native_closed_zero"](result);check("decimal-FILETIME-no-float-roundtrip",True)
for key,value in (("actual_exit",True),("owned_child_pid",True),("creation_time_100ns",float(134359866411023123))):
    bad=copy.deepcopy(result);bad[key]=value
    rejects("reject-native-"+key,lambda bad=bad:ns["native_closed_zero"](bad))
bad=copy.deepcopy(result);bad["job_cleanup"]["handles_closed"]=False
rejects("reject-open-Job",lambda:ns["native_closed_zero"](bad))
rejects("reject-guard-retained-handle",lambda:ns["guard_closed"](dict(closed=True,errors=[],retained_handles_count=1)))
now=datetime(2026,10,9,0,0,tzinfo=timezone.utc)
payload=dict(issued_utc=now.isoformat(),expires_utc=(now+timedelta(seconds=240)).isoformat())
ns["validity"](payload,"grant",now);check("four-minute-validity-positive",True)
rejects("absolute-expiry-no-refresh",lambda:ns["validity"](payload,"grant",now+timedelta(seconds=240)))
rejects("future-issued-reject",lambda:ns["validity"](payload,"grant",now-timedelta(seconds=1)))
p=b'{"x":1}';ns["signed_payload_exact"](b'{"payload":{"x":1},"signature":"public-example"}',p)
check("raw-payload-exact-positive",True)
rejects("same-JSON-different-signed-bytes",lambda:ns["signed_payload_exact"](b'{"payload":{"x": 1},"signature":"public-example"}',p))
rejects("raw-rows-in-archive-domain",lambda:ns["public_rows"]({"example":{"columns":["x"],"row_digests":[{"x":"raw"}]}}))
config=json.loads(read(B/"integration_codex/native-broker4-controller-config-root-1791513411000/controller.public.config.json"))
check("4347-FrozenInputs-declared",len(config["FrozenInputs"])==4347)
check("no-candidate-imports-child-SQL-network",not any(isinstance(n,(ast.Import,ast.ImportFrom)) and any(x.name.split(".")[0] in {"subprocess","sqlite3","requests","socket","ctypes"} for x in n.names) for n in ast.walk(tree)))
initial=list(refs.values())
write("sourceguard.initial.json",dict(method="exact bytes SHA256 before and after, no native handles acquired",refs=initial))
finding=dict(id="NHR-001",priority="P1",status="REQUEST_CHANGES",file=str(N/"root_concrete_approval_helper.py"),line=334,
trigger="Root API whole-fixture inspection emits database_ref with unprefixed SHA256.",
actual="retained() passes database_ref into public RawPin plain(), which requires sha256: prefix and raises before original database existence check or approval output.",
expected="Keep explicit separate validation for real inspection raw-hash database_ref versus prefixed public RawPin. Do not blanket-normalize all evidence or weaken original Root API/phase gates.",
producer_source_ref=pin(API),historical_real_inspection_ref=pin(Q),observed_database_ref=q["database_ref"],pure_source_reproduction=error,
historical_database_was_not_read=True,new_native_SQL_model_Git_Go=False)
write("finding.NHR-001.json",finding)
for ref in initial:check("unchanged:"+Path(ref["path"]).name,pin(ref["path"])==ref)
write("sourceguard.final.json",dict(refs=initial,unchanged=True))
write("review-result.json",dict(status="REQUEST_CHANGES",findings=[finding["id"]],checks=checks,checks_count=len(checks),
candidate_entrypoint_executed=False,extracted_pure_functions_only=True,actual_native_SQL_model_Git_Go=False,
approval_created=False,private_resource_read=False,Main_canonical_write=False,formal_acceptance=False))
print(json.dumps(dict(status="REQUEST_CHANGES",finding="NHR-001",checks=len(checks),source_refs=len(initial),evidence_directory=str(O))))

