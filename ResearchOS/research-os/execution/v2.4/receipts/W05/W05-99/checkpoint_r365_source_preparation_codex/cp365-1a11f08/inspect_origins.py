import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';N=Path(__file__).resolve().parent
paths={
903:B/'historical20_upgrade_source_independent_review_codex/h20r-20261009-source-review/failure-origin.903.json',
904:B/'checkpoint_r364_independent_review_codex/cp364-084378e0/failure-origin.904.json',
905:B/'root_native_c12_manual_caller_source_codex/c12-1a11ebe661670a1a49d0ea22092604a/failure-origin.905.json',
906:B/'historical20_upgrade_source_codex/h20-r1-root-1791519270000-scoped-check/failure-origin.906.json',
907:B/'historical21_session_install_contract_readonly_codex/a21-contract-084378e0/failure-origin.907.json',
908:B/'native_c12_final_prelaunch_independent_review_codex/c12pre-20261009-final-review/failure-origin.908.json',
909:B/'native_c12_final_prelaunch_independent_review_codex/c12pre-20261009-final-review/failure-origin.909.json',
910:B/'historical21_session_install_contract_readonly_codex/a21-contract-084378e0/failure-origin.910.json',
911:B/'native_c12_final_prelaunch_independent_review_codex/c12pre-20261009-final-review/failure-origin.911.json',
915:B/'native_grant_public_pin_archive_source_codex/gpa-1a11ee4f162766098eda3028b0679f2/failure-origin.915.json',
916:B/'integration_codex/native-cleanup-root-one-spec-source-1791517434000/postseal-failure-origin.916.json',
917:B/'historical20_r2_caller_independent_review_codex/h20r2-caller-01a11ee7/origin.917.json',
918:B/'native_grant_request_builder_independent_review_codex/gqbr-20261009-source-review/gqb_read3.original-tool-io.json',
919:B/'native_grant_bounded_read_independent_review_codex/gbr-review-01a11f01/origin.919.json',
920:B/'native_grant_request_builder_independent_review_codex/gqbr-20261009-source-review/gqb_review_io.original-tool-io.json',
921:R/'execution/v2.4/receipts/W09/W09-99/w09_c19_caller_source_codex/w09c19-1a11f08/mechanical-921.original-tool-io.json',
922:R/'execution/v2.4/receipts/W09/W09-99/w09_c19_caller_source_revision_codex/w09c19r2-1a11f08/mechanical-922-origin.json',
923:B/'integration_codex/native-cleanup-root-one-spec-source-1791517434000/postseal-failure-origin.923.json',
924:B/'integration_codex/native-cleanup-root-one-spec-source-1791517434000/postseal-failure-origin.924.json'}
extra=R/'execution/v2.4/receipts/W09/W09-99/independent_next_slice_readonly_codex/w09-slice-01a11ee7'
paths['912_913_disposition']=extra/'failure-origins.json'
paths['912_913_whole_tool_io']=extra/'original-tool-observations.json'
def pin(p):
 raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def reduced(value,depth=0):
 if depth>3:return {'type':type(value).__name__}
 if isinstance(value,dict):
  return {k:(dict(type=type(v).__name__,length=len(v)) if any(s in k.lower() for s in ('output','input','command','script','traceback','stdout','stderr')) and isinstance(v,(str,list,dict)) else reduced(v,depth+1)) for k,v in value.items()}
 if isinstance(value,list):return [reduced(v,depth+1) for v in value[:6]]+([{'more':len(value)-6}] if len(value)>6 else [])
 if isinstance(value,str) and len(value)>500:return value[:500]+'[DISPLAY_TRUNCATED]'
 return value
result=[]
for n,p in paths.items():
 value=json.loads(p.read_bytes());result.append(dict(ordinal=n,ref=pin(p),structure=reduced(value)))
with (N/'origin-input-inspection.json').open('xb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(result,ensure_ascii=False,indent=2))
