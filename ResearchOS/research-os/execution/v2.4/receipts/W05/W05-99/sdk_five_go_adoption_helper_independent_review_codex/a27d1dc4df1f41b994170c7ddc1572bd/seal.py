import hashlib,json
from pathlib import Path
R=Path(r"D:\作品集\ResearchOS\research-os");O=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_adoption_helper_independent_review_codex/a27d1dc4df1f41b994170c7ddc1572bd"
def ref(p):
 b=p.read_bytes();return {"path":p.relative_to(R).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,d):
 with (O/n).open("x",encoding="utf8",newline="\n") as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write("\n")
 return ref(O/n)
review=ref(O/"review.json")
m=save("manifest.json",{"schema":"researchos.receipt-manifest.v1","owner":"codex:/root/w05_merge_review","members":[ref(p) for p in sorted(O.iterdir()) if p.is_file()],"self_excluded":True,"handoff_excluded":True})
h=save("handoff.json",{"schema":"researchos.sdk-five-go-helper-independent-handoff.v1","decision":"READY_FOR_ROOT_FIVE_GO_ADOPTION_AFTER_VERIFIED_SCOPE7_CLOSE","review_ref":review,"manifest_ref":m,"checks":49,"failed_checks":[],"actual_helper_execution":False,"new_actual_tool_failures":0})
print(json.dumps({"review_ref":review,"manifest_ref":m,"handoff_ref":h},ensure_ascii=False))
