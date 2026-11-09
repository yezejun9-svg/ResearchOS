import sys
sys.dont_write_bytecode=True
import hashlib,json,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
F=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-positive-ttl-failed-root-release-1791505647184/failure-origin.835.json")
V=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4/controller-runtime")
def ref(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def walk(value,path=""):
    if isinstance(value,dict):
        yield path,value
        for key,item in value.items(): yield from walk(item,path+"/"+str(key))
    elif isinstance(value,list):
        for n,item in enumerate(value): yield from walk(item,path+"/"+str(n))
def main():
    invocation=json.loads((V/"test.invocation.json").read_text(encoding="utf-8"))
    failure=json.loads(F.read_text(encoding="utf-8"))
    fields=[]
    for path,item in walk(invocation):
        selected={key:value for key,value in item.items() if key in {"actual_exit","timed_out","resumed","assigned_before_resume","job_idle_confirmed","primary_exit_confirmed","handles_closed","active_processes_last_observed","error","errors"}}
        if selected: fields.append({"path":path,"fields":selected})
    env_fields=[]
    for path,item in walk(invocation):
        selected={key:value for key,value in item.items() if key.upper() in {"TEMP","TMP","SYSTEMROOT","WINDIR"}}
        if selected: env_fields.append({"path":path,"public_environment":selected})
    facts={key:value for key,value in failure.items() if isinstance(value,(str,int,float,bool,type(None))) and not any(x in key.lower() for x in ["private","credential","owner","token","claim","key"])}
    out={"authority":"NONE","failure835_ref":ref(F),"test_invocation_ref":ref(V/"test.invocation.json"),
         "test_stdout_ref":ref(V/"test.stdout.raw"),"test_stderr_ref":ref(V/"test.stderr.raw"),
         "original_public_failure_scalar_fields":facts,
         "actual_invocation_fields":fields,"actual_invocation_public_temp_environment":env_fields,
         "actual_test_stdout":(V/"test.stdout.raw").read_text(encoding="utf-8"),
         "actual_test_stderr":(V/"test.stderr.raw").read_text(encoding="utf-8"),
         "private_payloads_or_DPAPI_resources_read":False,"new_execution":False}
    (Q/"actual835-public-evidence.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False))
code=0
try: main()
except Exception: traceback.print_exc(); code=1
finally: print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)

