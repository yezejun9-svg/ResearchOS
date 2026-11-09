from readonly import *
INTENT="Fixed Source excerpts locating model receipts and cost metadata fields before original historical SELECT."
SQL=[]
if __name__=="__main__":
 p=W/"internal/domain/runtime_model_stream.go";lines=p.read_text(encoding="utf8").splitlines()
 for a,b in [(1,140),(245,280),(470,570)]:print("SOURCE",p.name,a,b,"\n".join(lines[a-1:b]))
 schema=json.loads((W/"internal/api/contracts/domain.schema.json").read_text(encoding="utf8"))
 defs=schema.get("$defs",schema.get("definitions",{}))
 print("COST_RELATED_SCHEMA_NAMES",[k for k in defs if any(x in k.lower() for x in ["budgetledger","cost","resourceeffect","resourcerequest","runtimeobservation"])])
 for k,v in defs.items():
  if any(x in k.lower() for x in ["budgetledger","cost","resourceeffect","resourcerequest","runtimeobservation"]):
   print("PUBLIC_SCHEMA",k,json.dumps(v,ensure_ascii=False)[:11000])
 print("G05_SOURCE_HISTORY_FIELDS_COMPLETE")

