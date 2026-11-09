import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/official-test2json-resource-build-root-3e9129c5f7c9461e")
p=ROOT/"selected-official-compiler-inputs.json"
raw=p.read_bytes()
doc=json.loads(raw.decode("utf-8"))
hits=[]
def visit(v,pointer):
    if isinstance(v,dict):
        direct=[k for k,x in v.items() if isinstance(x,str) and x.replace("\\","/").endswith("/src/cmd/internal/test2json/test2json.go")]
        if direct:
            hits.append({"pointer":pointer,"value":v})
        for k,x in v.items():visit(x,pointer+"/"+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v):visit(x,pointer+"/"+str(i))
visit(doc,"")
result={"inventory":{"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)},"top_keys":list(doc) if isinstance(doc,dict) else type(doc).__name__,"internal_test2json_source_hits":hits}
with (Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49")/"official-source-locator.json").open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result,ensure_ascii=False))
