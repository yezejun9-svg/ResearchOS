from pathlib import Path
import json,collections
r=Path(r"D:\作品集\ResearchOS\research-os")
a=r/"execution/v2.4/receipts/W05/W05-99/owned_core_stop_proof_revision03_source_codex/20261015-current-chat/candidate-2816daac-final"
e=r/"execution/v2.4/receipts/W05/W05-99/owned_core_stop_proof_revision03_independent_review_codex/20261015-current-chat"
for name in ["manifest.json","failure-and-gap-ledger.json"]:
 d=json.loads((a/name).read_text(encoding="utf-8"));print(name,"keys",list(d))
 for k,v in d.items():
  if isinstance(v,list): print(k,"count",len(v),"first",json.dumps(v[:1],ensure_ascii=False)[:1800])
  elif isinstance(v,dict): print(k,"dictkeys",list(v))
  else:print(k,v)
for p in sorted(e.glob("fixture-e2e-*/case-result.json")):
 print(str(p),p.read_text(encoding="utf-8"))
