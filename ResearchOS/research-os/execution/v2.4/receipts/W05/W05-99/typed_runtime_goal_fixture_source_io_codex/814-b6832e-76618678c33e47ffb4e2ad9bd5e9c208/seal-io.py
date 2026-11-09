import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
I=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_io_codex/814-b6832e-76618678c33e47ffb4e2ad9bd5e9c208")
def pin(p):
    b=p.read_bytes()
    return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
members=[pin(p) for p in sorted(I.iterdir()) if p.is_file()]
manifest={"schema":"researchos.immutable_postseal_io_manifest.v1","authority":"NONE","formal_acceptance":False,"source_MF_unchanged":True,"members":members,"failure_ordinal":814,"self_hash_excluded":["MF_IO.json"],"postseal_io_excluded":["io-seal-run.json"],"failure_reset":False}
with (I/"MF_IO.json").open("x",encoding="utf-8",newline="\n") as f:
    f.write(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"MF_IO":pin(I/"MF_IO.json"),"fingerprints":pin(I/"fingerprints.json"),"failure_origin":pin(I/"failure-origin.814.json"),"members":len(members),"authority":"NONE","formal_acceptance":False},ensure_ascii=False))
