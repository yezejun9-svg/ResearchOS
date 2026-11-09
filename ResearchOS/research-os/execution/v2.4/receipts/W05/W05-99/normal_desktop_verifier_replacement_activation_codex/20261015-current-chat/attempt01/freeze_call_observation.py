import datetime,hashlib,json,re
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
decision=read(E/'04-qualified-request-root-explicit-confirm.json');S=R/'execution/v2.4/receipts/W05/W05-99/local_model_resource_restart_codex/20261015-current-chat';before=decision['modelLogBefore'];suffixes={};lines={}
for stream,key in [('stdout','stdoutBytes'),('stderr','stderrBytes')]:
 p=S/('server.'+stream+'.raw');raw=p.read_bytes();assert len(raw)>=before[key];suffix=raw[before[key]:];copy=E/('10-server-'+stream+'-since-explicit-confirm.raw')
 with copy.open('xb') as f:f.write(suffix)
 suffixes[stream]=ref(copy);lines[stream]=suffix.decode('utf8',errors='strict').splitlines()
gin=[line for line in lines['stdout'] if line.startswith('[GIN]') and re.search(r'\bPOST\s+"/v1/chat/completions"',line)]
llama=[line for line in lines['stderr'] if 'done request: POST /v1/chat/completions ' in line]
model=R/'execution/v2.4/receipts/W05/W05-99/coding_model_observer_codex/20261014-current-chat/verifier-replacement-reopen01/after-confirm-bc269e77-01.json';obs=read(model)
assert obs['run_id']=='f3dcb996b2e43cf52cba874be7abfc70'
assert obs['distinct_effect_keys_by_capability']=={'MODEL':1}
assert len(gin)==len(llama)==1
out={'schema':'researchos.actual-qualification-call-observation.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'request_id':decision['requestId'],'request_hash':decision['requestHash'],'explicit_confirm_count':1,'consumed_run_id':obs['run_id'],'source_model_observation_ref':ref(model),'server_suffix_refs':suffixes,'ollama_frontend_post_count':len(gin),'llama_backend_post_count':len(llama),'frontend_backend_not_added_as_two_calls':True,'server_request_lines':gin+llama,'distinct_model_effect_keys':1,'model_http_response_status':200,'actual_tool_effect_count':0,'worker_tool_request_count':1,'tool_request_fact_source':'Independent diagnosis of public worker stdout frame3; tool request is not tool execution. Await frozen independent diagnostic reference.','run_status_observed':'RUNNING','dispatch_state_observed':'UNKNOWN','qualification':'NOT_ACCEPTED_UNRESOLVED_NO_REPLAY','cost':'UNKNOWN_NOT_ZERO','model_or_tool_requests_by_this_observer':0,'formal_increment':0}
with (E/'11-call-observation.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=True))
