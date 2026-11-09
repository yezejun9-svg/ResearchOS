from readonly import *
import re
INTENT="Read pinned Source metadata field definitions and prior accepted public deployment/resource map only; no original DB access."
SQL=[]
if __name__=="__main__":
 paths=[]
 for name in ["actual-activation-binding.json","package-file-locations.json","pending-resources-and-toolgaps.json"]:
  p=R/"execution/v2.4/receipts/W05/W05-99/qualification_official_entry_resource_map_codex/20261015-current-chat"/name
  paths.append(pin(p));print("PRIOR_PUBLIC_METADATA",name,p.read_text(encoding="utf-8-sig"))
 for p in sorted((W/"internal/domain").glob("*model*stream*.go")):
  if p.name.endswith("_test.go"):continue
  text=p.read_text(encoding="utf8")
  matches=[(i+1,line) for i,line in enumerate(text.splitlines()) if any(s in line for s in ["json:",'KindModel','MODEL','ACK','raw_receipt','raw_event','confirmed','cost_status'])]
  if matches:print("SOURCE_MODEL_METADATA",p.name,json.dumps(matches[:80]))
  paths.append(pin(p))
 p=W/"internal/domain/resources.go"
 if p.is_file():
  text=p.read_text(encoding="utf8")
  print("SOURCE_RESOURCE_FIELDS",json.dumps([(i+1,l) for i,l in enumerate(text.splitlines()) if any(s in l for s in ['cost_status','cost_state','cost_evidence','measurement','resource_effects'])][:50]))
  paths.append(pin(p))
 save("g04-public-source-pins.json",paths)
 print("G04_PUBLIC_SOURCE_READ_COMPLETE")

