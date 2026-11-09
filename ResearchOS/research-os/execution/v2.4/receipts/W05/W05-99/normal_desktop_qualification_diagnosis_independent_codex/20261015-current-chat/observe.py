import base64, datetime, hashlib, json, pathlib, sqlite3

ROOT = pathlib.Path(r'D:\作品集\ResearchOS\research-os')
OUT = pathlib.Path(__file__).parent
DATA = ROOT / '.local/live/current-chat-normal-desktop-first-use-20261012/data'
RUN = 'f3dcb996b2e43cf52cba874be7abfc70'
PROJECT = 'a7ebcf2a322c6abcf87e043f601ee804'
DISPATCH = '705b11ec99044fef19e85f57e2d2b712'
REQUEST = 'bc269e772ada7e1bce54439fd080550c'
refs = []
def read_public(path):
    raw = path.read_bytes()
    refs.append({'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
    return json.loads(raw)

j = read_public(DATA / 'runtime-dispatches' / DISPATCH / 'bridge.json')
ob = {k:j.get(k) for k in ('version','dispatch_key','manifest_hash','state','reason','started','ended','observation_sequence','frames','acknowledged','context_ready','protocol_complete','cancelled','stdout_hash','stderr_hash','identity')}
ob['sandbox_receipt'] = {k:j['sandbox_receipt'].get(k) for k in ('pid','process_created_ns','job','exit_code','children_stopped','job_total_processes','timed_out','streams_drained','cleanup_complete','output_copied','started_at','finished_at')}
ob['frame_metadata'] = []
for line in base64.b64decode(j['sandbox_receipt']['stdout']).splitlines():
    frame=json.loads(line)
    meta={k:frame.get(k) for k in ('sequence','type','key','route','capability')}
    payload=frame.get('payload',{})
    if frame.get('capability')=='TOOL': meta['tool_name']=payload.get('name'); meta['check_id']=payload.get('arguments',{}).get('check_id')
    if frame.get('capability')=='MODEL':
        body=payload.get('body',{})
        meta['tool_names']=[t.get('function',{}).get('name') for t in body.get('tools',[])]
        meta['tool_choice']=body.get('tool_choice')
    ob['frame_metadata'].append(meta)
ob['admission']={k:j['manifest']['admission'].get(k) for k in ('qualification_bootstrap','permission','requested_capabilities')}
config=j['manifest']['admission']['profile']['model_config']
ob['model_config']={k:config.get(k) for k in ('ref','route','max_calls','max_output_tokens')}
ob['model_config']['tool_names']=[t.get('function',{}).get('name') for t in config.get('tools',[])]
ob['model_qualification']=j['manifest']['admission']['profile'].get('model_qualification')
queries=[]
con=sqlite3.connect((DATA/'researchos.sqlite').as_uri()+'?mode=ro',uri=True)
con.row_factory=sqlite3.Row
con.execute('PRAGMA query_only=ON'); con.execute('BEGIN')
def query(sql,args):
    queries.append({'sql':sql,'parameters':args})
    return [dict(x) for x in con.execute(sql,args)]
try:
    ob['dispatch_db']=query('SELECT project,run,epoch,dispatch_key,state,reason,updated_at,observation_sequence,observation_hash FROM runtime_dispatches WHERE project=? AND run=?',[PROJECT,RUN])
    ob['run_db']=query("SELECT id,revision,json_extract(body,'$.status') AS status,json_extract(body,'$.exit_code') AS exit_code,json_extract(body,'$.children_stopped') AS children_stopped,json_extract(body,'$.runtime_settled_at') AS runtime_settled_at FROM domain_objects WHERE project=? AND kind='Run' AND id=?",[PROJECT,RUN])
    ob['effects_db']=query("SELECT effect_key,sequence,json_extract(body,'$.state') AS state,json_extract(body,'$.payload.capability') AS capability,json_extract(body,'$.receipt.model_transport') AS model_transport,json_extract(body,'$.receipt.payload.status') AS status FROM resource_effects WHERE project=? AND run=? ORDER BY effect_key,sequence",[PROJECT,RUN])
    ob['acceptance_db']=query("SELECT id,revision FROM domain_objects WHERE project=? AND kind='AcceptanceReceipt' AND json_extract(body,'$.run_id')=?",[PROJECT,RUN])
    ob['administration_provenance']=query("SELECT id,revision,json_extract(body,'$.metadata.action') AS action,json_extract(body,'$.metadata.process_identity') AS process_identity FROM domain_objects WHERE project=? AND kind='Artifact' AND (json_extract(body,'$.metadata.request.request_id')=? OR json_extract(body,'$.provenance.request.request_id')=?)",[PROJECT,REQUEST,REQUEST])
finally:
    con.rollback(); con.close()
ob.update(schema='researchos.independent-qualification-diagnosis.v1',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_refs=refs,query_log=queries,db_mode='ro; query_only; BEGIN/ROLLBACK',mutations=0,api_requests=0,model_requests=0,formal_increment=0)
target=OUT/'01-public-observation.json'
target.write_text(json.dumps(ob,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'dispatch':ob['dispatch_db'],'frames':ob['frame_metadata']},ensure_ascii=False))
