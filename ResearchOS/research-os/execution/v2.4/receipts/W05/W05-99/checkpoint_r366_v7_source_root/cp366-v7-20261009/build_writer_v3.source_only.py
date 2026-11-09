import ast,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
raw=(O/"checkpoint_w09_v7.v2.atomic.py").read_bytes()
assert hashlib.sha256(raw).hexdigest()=="7670965b0bf3c5f0b6d28d8df3db89f723b1a1560bb1171254994aec3d58cf95"
text=raw.decode("utf-8")
old='''    source_pairs = {(v["handoff_ref"]["path"], v["manifest_ref"]["path"]) for v in facts["reviews"]}
    assert (new_owner["source_handoff_ref"]["path"], new_owner["source_manifest_ref"]["path"]) in source_pairs
    assert (new_owner["independent_source_review_ref"]["path"],
            new_owner["independent_source_manifest_ref"]["path"]) in source_pairs
'''
new='''    assert any(new_owner["source_handoff_ref"] == v["handoff_ref"] and
               new_owner["source_manifest_ref"] == v["manifest_ref"]
               for v in facts["reviews"]), "FULL_SOURCE_TYPED_REF_PAIR"
    assert any(new_owner["independent_source_review_ref"] == v["handoff_ref"] and
               new_owner["independent_source_manifest_ref"] == v["manifest_ref"]
               for v in facts["reviews"]), "FULL_REVIEW_TYPED_REF_PAIR"
'''
assert text.count(old)==1
text=text.replace(old,new)
assert text.replace(new,old)==raw.decode("utf-8"),"FULL_V2_BYTE_INVERSE"
ast.parse(text)
p=O/"checkpoint_w09_v7.v3.atomic.py"
with p.open("xb") as f:f.write(text.encode("utf-8"))
data=p.read_bytes()
print({"path":str(p),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"full_v2_inverse":True,"AST_VALID":True,"actual_executed":False})
