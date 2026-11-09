"""Append-only read-only observer for an exact coding configuration and its qualification.
No API, GUI, subprocess, credential/config JSON, dispatch manifest, or model-body reads.
Observation is evidence; it neither grants permission nor reimplements current admission.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sqlite3
import sys
import time

REQUEST_FIELDS = {'request_id','project_id','session_id','model_config_ref','runtime_id','task_id','plan_hash','profile_hash','authorize_purpose','purpose_seconds','owner_host','owner_principal','owner_root','session_hash','configuration_hash','issued_at','expires_at'}
MAX_ROWS, MAX_JSON, MAX_OUTPUT = 1000, 2*1024*1024, 2*1024*1024
TABLES = {'client_sessions','idempotency','host_model_configurations','runtime_bindings','runtime_qualification_plans','runtime_qualification_runs','runtime_dispatches','resource_effects','domain_objects'}
CONFIG_COLUMNS = {'model_config_ref','owner_host_ref','principal','config_revision','config_hash','command_id','request_hash','scope_hash','created_at'}
MISSING = ['private_management_stdout_frames','native_verifier_process_stderr','native_verifier_numeric_process_wait_status']

class ObservationError(ValueError):
    pass

def need(condition, code):
    if not condition:
        raise ObservationError(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def decode(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='strict')
    need(isinstance(raw,str) and len(raw.encode('utf8')) <= MAX_JSON, 'JSON_BYTE_BOUND')
    def pairs(items):
        result = {}
        for key,value in items:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def bad_constant(_):
        raise ObservationError('NONFINITE_JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad_constant)

def digest(value):
    # Restricted JCS-compatible product records: no floats or non-string object keys.
    def check(v):
        need(type(v) in (dict,list,str,int,bool,type(None)), 'UNSUPPORTED_CANONICAL_VALUE')
        if type(v) is dict:
            need(all(type(k) is str and k.isascii() for k in v), 'NONASCII_CANONICAL_KEY')
            for item in v.values(): check(item)
        elif type(v) is list:
            for item in v: check(item)
        elif type(v) is int:
            need(abs(v) <= 9007199254740991,'UNSAFE_CANONICAL_INTEGER')
    check(value)
    return 'sha256:'+sha(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8'))

def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    need(parsed.tzinfo is not None,'TIMESTAMP_REQUIRES_ZONE')
    return parsed

def authorize(action, table, column, database, source):
    if action == sqlite3.SQLITE_READ:
        if database != 'main' or table not in TABLES: return sqlite3.SQLITE_DENY
        if table == 'host_model_configurations' and column not in CONFIG_COLUMNS: return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_SELECT: return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and column in {'json_extract','count','coalesce'}: return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_TRANSACTION and table in {'BEGIN','ROLLBACK'}: return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY

class Reader:
    def __init__(self, connection):
        self.c, self.log = connection, []
    def rows(self, sql, args=()):
        self.log.append({'sql':sql,'parameters':list(args)})
        rows = self.c.execute(sql,args).fetchmany(MAX_ROWS+1)
        need(len(rows)<=MAX_ROWS,'ROW_BOUND')
        return [dict(r) for r in rows]
    def one(self, sql, args, code):
        values = self.rows(sql,args)
        need(len(values)==1,code)
        return values[0]
    def idem(self, owner, project, operation, key, fields):
        # fields are constants supplied only by this module, never caller-controlled SQL.
        projections = ','.join("json_extract(body,'$."+name+"') AS "+('body_request_hash' if name=='request_hash' else name) for name in fields)
        return self.rows('SELECT principal,project,operation,key,request_hash,created_at,'+projections+' FROM idempotency WHERE principal=? AND project=? AND operation=? AND key=?',(owner,project,operation,key))
    def entity(self, project, kind, identity, fields):
        projections = ','.join("json_extract(body,'$."+name+"') AS "+('body_request_hash' if name=='request_hash' else name) for name in fields)
        return self.one('SELECT id,revision,'+projections+' FROM domain_objects WHERE project=? AND kind=? AND id=?',(project,kind,identity),'EXACT_'+kind.upper()+'_REQUIRED')

def observe(database, project, session, owner, coding_request_id=None, model_config_ref=None, qualification_request_id=None, run_id=None, expected_write_paths=None):
    need(bool(coding_request_id or model_config_ref),'CODING_REQUEST_OR_MODEL_REF_REQUIRED')
    need(not run_id or qualification_request_id,'RUN_REQUIRES_EXACT_QUALIFICATION_REQUEST')
    p = pathlib.Path(database).resolve(strict=True)
    need(p.is_file(),'DATABASE_FILE_REQUIRED')
    out = {'schema':'researchos.coding-model-readonly-observation/1','at':dt.datetime.now(dt.timezone.utc).isoformat(),'database':str(p),'database_uri_mode':'ro','query_only':True,'transaction':'BEGIN/ROLLBACK','project_id':project,'session_id':session,'owner_principal':owner,'requested_coding_request_id':coding_request_id,'requested_model_config_ref':model_config_ref,'requested_qualification_request_id':qualification_request_id,'requested_run_id':run_id,'mutations':0,'api_requests':0,'model_requests':0,'formal_increment':0,'not_observed':MISSING,'current_admission_recomputed':False,'current_authorization_not_inferred':True}
    c = sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=3)
    c.row_factory = sqlite3.Row
    try:
        c.execute('PRAGMA query_only=ON')
        need(c.execute('PRAGMA query_only').fetchone()[0]==1,'QUERY_ONLY_NOT_ENABLED')
        c.set_authorizer(authorize)
        deadline = time.monotonic()+8
        c.set_progress_handler(lambda: int(time.monotonic()>deadline),1000)
        c.execute('BEGIN')
        r = Reader(c)
        out['session'] = r.one('SELECT id,project_id,revision,writer_epoch,writer_client_id,lease_expires_at,workspace_ref,model_config_ref,core_build_id,run_id,sealed_at,archived_at FROM client_sessions WHERE project_id=? AND id=?',(project,session),'EXACT_SESSION_REQUIRED')
        out['project_counts_context_only'] = {name:r.one('SELECT COUNT(*) AS n FROM '+name+' WHERE project=?',(project,),'COUNT_REQUIRED')['n'] for name in ['runtime_qualification_runs','runtime_dispatches','resource_effects']}
        auth_fields = ['schema','confirmation_id','confirmation_hash','owner','owner_root','owner_host','project_id','session_id','model_config_ref','original_model_config_ref','configuration_command_id','workspace_ref','workspace_hash','intent','freeze_hash']
        if not coding_request_id:
            found = r.idem(owner,project,'host:coding-authorization',model_config_ref,auth_fields)
            need(len(found)==1,'EXACT_CODING_AUTHORIZATION_REQUIRED')
            coding_request_id=found[0]['confirmation_id']
        confirmation = r.idem(owner,project,'host:coding-confirmation',coding_request_id,['schema','request_id','project_id','session_id','model_config_ref','owner','owner_root','host_id','configuration_hash','workspace_hash','intent','issued_at','expires_at'])
        need(len(confirmation)==1,'EXACT_CODING_PREPARE_REQUIRED');confirmation=confirmation[0]
        need(confirmation['schema']=='researchos.explicit-workspace-coding.v1' and confirmation['request_id']==coding_request_id and confirmation['project_id']==project and confirmation['session_id']==session and confirmation['owner']==owner,'CODING_PREPARE_IDENTITY_MISMATCH')
        confirmation['intent']=decode(confirmation['intent'])
        if expected_write_paths is not None:
            need(sorted(confirmation['intent']['write_paths'])==sorted(expected_write_paths),'EXPECTED_WRITE_PATHS_MISMATCH')
        out['coding_prepare']=confirmation
        out['coding_prepare_nested_hash_recomputed']=False
        out['coding_prepare_hash_note']='Stored exact request_hash bound across installation/authorization; full private frozen/assets body intentionally not read or independently canonicalized.'
        installations=r.idem(owner,project,'host:coding-installation',coding_request_id,['state','request_id','request_hash','project_id','session_id','model_config_ref','old_model_config_ref','runtime_id','runtime_status','profile_ref','revision','config_revision','configuration_command_id','scope','normal_max_model_calls','qualification_model_calls','qualification_tool_calls','model_calls'])
        need(len(installations)<=1,'AMBIGUOUS_CODING_INSTALLATION')
        if not installations:
            need(model_config_ref is None,'REQUESTED_MODEL_NOT_INSTALLED')
            need(not qualification_request_id and not run_id,'QUALIFICATION_WITHOUT_CODING_INSTALLATION')
            out['stage']='AWAITING_CODING_INSTALLATION';out['observation_bound']=True;out['query_log']=r.log
            return out
        installed=installations[0]
        need(installed['state']=='CODING_CONFIGURED' and installed['request_id']==coding_request_id and installed['request_hash']==installed['body_request_hash']==confirmation['request_hash'] and installed['project_id']==project and installed['session_id']==session and installed['old_model_config_ref']==confirmation['model_config_ref'],'CODING_INSTALLATION_IDENTITY_MISMATCH')
        need(installed['normal_max_model_calls']==8 and installed['qualification_model_calls']==1 and installed['qualification_tool_calls']==0 and installed['model_calls']==0,'CODING_MODEL_CALL_LIMITS_MISMATCH')
        model=installed['model_config_ref'];need(isinstance(model,str) and model and model!=installed['old_model_config_ref'],'NEW_MODEL_REF_REQUIRED')
        need(model_config_ref is None or model_config_ref==model,'REQUESTED_MODEL_REF_MISMATCH')
        installed['scope']=decode(installed['scope']);installed['profile_ref']=decode(installed['profile_ref'])
        need(installed['scope']==confirmation['intent'],'CODING_SCOPE_CHANGED')
        auth=r.idem(owner,project,'host:coding-authorization',model,auth_fields);need(len(auth)==1,'EXACT_CODING_AUTHORIZATION_REQUIRED');auth=auth[0];auth['intent']=decode(auth['intent'])
        need(auth['schema']==confirmation['schema'] and auth['workspace_hash']==confirmation['workspace_hash'] and auth['confirmation_id']==coding_request_id and auth['confirmation_hash']==confirmation['request_hash'] and auth['model_config_ref']==model and auth['original_model_config_ref']==confirmation['model_config_ref'] and auth['project_id']==project and auth['session_id']==session and auth['owner']==owner and auth['owner_root']==confirmation['owner_root'] and auth['owner_host']==confirmation['host_id'] and auth['intent']==confirmation['intent'] and auth['configuration_command_id']==installed['configuration_command_id'],'CODING_AUTHORIZATION_BINDING_MISMATCH')
        config=r.one('SELECT model_config_ref,owner_host_ref,principal,config_revision,config_hash,command_id,request_hash,scope_hash,created_at FROM host_model_configurations WHERE principal=? AND model_config_ref=?',(owner,model),'EXACT_CONFIGURATION_METADATA_REQUIRED')
        need(config['owner_host_ref']==auth['owner_host'] and config['config_revision']==installed['config_revision'] and config['command_id']==installed['configuration_command_id'],'CONFIGURATION_METADATA_BINDING_MISMATCH')
        out.update(coding_installation=installed,coding_authorization=auth,configuration_metadata=config,model_config_ref=model,runtime_id=installed['runtime_id'],current_session_model_matches_observed=out['session']['model_config_ref']==model)
        runtime=installed['runtime_id'];need(isinstance(runtime,str) and runtime,'RUNTIME_REQUIRED')
        out['runtime']=r.entity(project,'RuntimeRegistration',runtime,['status','name'])
        binding=r.one('SELECT profile_ref,profile_hash,technical_hash,owner FROM runtime_bindings WHERE project=? AND runtime=?',(project,runtime),'EXACT_RUNTIME_BINDING_REQUIRED')
        binding['profile_ref']=decode(binding['profile_ref'])
        need(binding['profile_ref']==installed['profile_ref'] and binding['profile_hash']==digest(binding['profile_ref']) and binding['owner']==owner,'RUNTIME_PROFILE_MISMATCH')
        out['runtime_binding']=binding
        plans=r.rows('SELECT project,task,runtime,plan,plan_hash,author,author_root FROM runtime_qualification_plans WHERE project=? AND runtime=?',(project,runtime))
        for plan in plans:
            plan['plan']=decode(plan['plan']);need(digest(plan['plan'])==plan['plan_hash'],'PLAN_HASH_MISMATCH')
            need(plan['author_root']==confirmation['owner_root'] and plan['plan']['runtime_id']==runtime and plan['plan']['profile_ref']==installed['profile_ref'],'PLAN_BINDING_MISMATCH')
        out['runtime_plans']=plans
        candidates=r.rows("SELECT key AS request_id,request_hash,created_at,json_extract(body,'$.task_id') AS task_id,json_extract(body,'$.runtime_id') AS runtime_id,json_extract(body,'$.issued_at') AS issued_at,json_extract(body,'$.expires_at') AS expires_at FROM idempotency WHERE principal=? AND project=? AND operation='host:qualification-confirmation' AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.model_config_ref')=? ORDER BY created_at,key",(owner,project,session,model))
        out['qualification_candidates']=candidates
        out['runtime_qualification_runs']=r.rows('SELECT project,task,run,runtime,epoch,plan_hash,profile_hash,contract_hash,input_hash,context_bundle,owner_root FROM runtime_qualification_runs WHERE project=? AND runtime=? ORDER BY run',(project,runtime))
        if not qualification_request_id:
            out['stage']='CODING_CONFIGURED_REQUEST_NOT_SELECTED';out['selection_policy']='No latest selection. Pass exact UI qualification request_id to bind one request and auto-derive its consumed Run.';out['observation_bound']=True;out['query_log']=r.log
            return out
        request_row=r.one("SELECT request_hash,body,created_at FROM idempotency WHERE principal=? AND project=? AND operation='host:qualification-confirmation' AND key=?",(owner,project,qualification_request_id),'EXACT_QUALIFICATION_PREPARE_REQUIRED')
        raw=request_row.pop('body');raw=raw if isinstance(raw,bytes) else raw.encode('utf8');request=decode(raw)
        need(set(request)==REQUEST_FIELDS and type(request['purpose_seconds']) is int and 1<=request['purpose_seconds']<=3600 and all(type(v) is str for k,v in request.items() if k!='purpose_seconds'),'QUALIFICATION_REQUEST_SCHEMA')
        need(digest(request)==request_row['request_hash'],'QUALIFICATION_REQUEST_HASH_MISMATCH')
        need(request['request_id']==qualification_request_id and request['project_id']==project and request['session_id']==session and request['model_config_ref']==model and request['runtime_id']==runtime and request['owner_principal']==owner and request['owner_root']==confirmation['owner_root'] and request['owner_host']==config['owner_host_ref'] and request['configuration_hash']==config['config_hash'] and request['authorize_purpose']=='mu_turn','QUALIFICATION_REQUEST_BINDING_MISMATCH')
        selected=[p for p in plans if p['task']==request['task_id']];need(len(selected)==1,'EXACT_REQUEST_PLAN_REQUIRED');plan=selected[0]
        need(plan['plan_hash']==request['plan_hash'] and digest(plan['plan']['profile_ref'])==request['profile_hash'],'QUALIFICATION_PLAN_PROFILE_MISMATCH')
        out['qualification_request']={**request_row,'body_sha256':sha(raw),'request':request}
        task=r.entity(project,'Task',request['task_id'],['project_id','goal_id','task_type','status','active_run_id','acceptance_id','context_bundle_id'])
        need(task['project_id']==project and task['task_type']=='runtime_qualification','QUALIFICATION_TASK_MISMATCH');out['task']=task
        goal=r.entity(project,'Goal',task['goal_id'],['project_id','status','budget_policy_id']);need(goal['project_id']==project,'GOAL_PROJECT_MISMATCH');out['goal']=goal
        chain=[];seen=set();policy_id=goal['budget_policy_id']
        while policy_id:
            need(policy_id not in seen and len(chain)<20,'BUDGET_ANCESTRY_CYCLE_OR_BOUND');seen.add(policy_id)
            row=r.one("SELECT id,revision,body FROM domain_objects WHERE kind='BudgetPolicy' AND id=? AND (project=? OR project='' OR project IS NULL)",(policy_id,project),'EXACT_BUDGET_POLICY_REQUIRED');policy=decode(row['body']);chain.append(policy);policy_id=policy['parent_policy_id']
        out['budget_chain_observed']=chain;out['budget_effective_policy_recomputed']=False
        consumed=r.rows("SELECT request_hash,body,created_at FROM idempotency WHERE principal=? AND project=? AND operation='host:managed-runtime-qualification' AND key=?",(owner,project,qualification_request_id));need(len(consumed)<=1,'AMBIGUOUS_CONSUMPTION')
        current_session_hash=digest({'id':session,'project':project,'revision':out['session']['revision'],'writer_epoch':out['session']['writer_epoch'],'writer':out['session']['writer_client_id'],'run':out['session']['run_id'] or ''})
        out['current_session_hash_matches_request']=current_session_hash==request['session_hash']
        now=dt.datetime.now(dt.timezone.utc);issued=timestamp(request['issued_at']);expires=timestamp(request['expires_at']);out['qualification_request_time_valid_now']=issued<=now<expires and dt.timedelta(0)<expires-issued<=dt.timedelta(minutes=1)
        if not consumed:
            need(not run_id,'RUN_NOT_CONSUMED');out['stage']='QUALIFICATION_PREPARED_NOT_CONSUMED';out['preconfirm_goals_and_refs_current']=goal['status']=='ACTIVE' and out['current_session_model_matches_observed'] and out['current_session_hash_matches_request'];out['observation_bound']=True;out['query_log']=r.log
            return out
        consumed=consumed[0];body=decode(consumed.pop('body'));need(consumed['request_hash']==request_row['request_hash']==body['request_hash'] and body['task_id']==request['task_id'] and body['runtime_id']==runtime,'CONSUMPTION_BINDING_MISMATCH')
        bound_run=body['run_ref'];need(bound_run['entity_type']=='Run' and type(bound_run['id']) is str and bound_run['id'] and type(bound_run['revision']) is int and bound_run['revision']>=1,'CONSUMED_RUN_REF_INVALID');actual_run=bound_run['id'];need(run_id is None or run_id==actual_run,'REQUESTED_RUN_MISMATCH')
        out['consumption']={**consumed,'body':body};out['run_id']=actual_run
        qrs=[x for x in out['runtime_qualification_runs'] if x['run']==actual_run];need(len(qrs)==1,'EXACT_QUALIFICATION_RUN_REQUIRED');qr=qrs[0]
        need(qr['task']==request['task_id'] and qr['plan_hash']==request['plan_hash'] and qr['profile_hash']==request['profile_hash'] and qr['owner_root']==request['owner_root'],'QUALIFICATION_RUN_BINDING_MISMATCH')
        run=r.entity(project,'Run',actual_run,['project_id','task_id','runtime_id','lease_epoch','status','context_bundle_id','exit_code','children_stopped','queue_empty','started_at','ended_at','runtime_settled_at'])
        need(run['project_id']==project and run['task_id']==request['task_id'] and run['runtime_id']==runtime and run['lease_epoch']==qr['epoch'] and run['context_bundle_id']==qr['context_bundle'] and run['revision']>=bound_run['revision'],'RUN_OBJECT_BINDING_MISMATCH')
        out['run']=run;out['current_task_active_run_matches_observed']=task['active_run_id']==actual_run
        out['dispatches']=r.rows('SELECT project,run,epoch,dispatch_key,manifest_hash,state,worker,journal_locator,observation_sequence,observation_hash FROM runtime_dispatches WHERE project=? AND run=?',(project,actual_run));need(all(x['epoch']==qr['epoch'] for x in out['dispatches']),'DISPATCH_EPOCH_MISMATCH')
        effects=r.rows("SELECT effect_key,sequence,json_extract(body,'$.task_id') AS task_id,json_extract(body,'$.run_id') AS run_id,json_extract(body,'$.epoch') AS epoch,json_extract(body,'$.state') AS state,json_extract(body,'$.payload.capability') AS capability,json_extract(body,'$.request_hash') AS request_hash,json_extract(body,'$.reservation_id') AS reservation_id,json_extract(body,'$.receipt.actual_cost') AS actual_cost,json_extract(body,'$.receipt.model_transport') AS model_transport,json_extract(body,'$.receipt.payload.status') AS response_status FROM resource_effects WHERE project=? AND run=? ORDER BY effect_key,sequence",(project,actual_run))
        need(all(x['task_id']==request['task_id'] and x['run_id']==actual_run and x['epoch']==qr['epoch'] for x in effects),'EFFECT_BINDING_MISMATCH');out['resource_effects']=effects
        out['distinct_effect_keys_by_capability']={cap:len({e['effect_key'] for e in effects if e['capability']==cap}) for cap in sorted({e['capability'] for e in effects if e['capability']})}
        out['effect_count_note']='Distinct journal keys, not independently observed HTTP attempt counts; PREPARED/STARTED/CONFIRMED are phases, not separate calls.'
        out['ledger_entries']=r.rows("SELECT id,revision,json_extract(body,'$.run_id') AS run_id,json_extract(body,'$.operation') AS operation,json_extract(body,'$.cost_basis') AS cost_basis,json_extract(body,'$.money') AS money,json_extract(body,'$.reservation_id') AS reservation_id,json_extract(body,'$.provider_request_id') AS provider_request_id FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? ORDER BY id",(project,actual_run))
        out['acceptance_receipts']=r.rows("SELECT id,revision,json_extract(body,'$.run_id') AS run_id,json_extract(body,'$.verdict') AS verdict,json_extract(body,'$.measurement_mode') AS measurement_mode,json_extract(body,'$.independence_basis') AS independence_basis,json_extract(body,'$.contract_hash') AS contract_hash,json_extract(body,'$.receipt_hash') AS receipt_hash,json_extract(body,'$.verifier_principal_id') AS verifier_principal_id,json_extract(body,'$.checks') AS checks,json_extract(body,'$.artifact_refs') AS artifact_refs FROM domain_objects WHERE project=? AND kind='AcceptanceReceipt' AND json_extract(body,'$.run_id')=? ORDER BY id",(project,actual_run))
        for receipt in out['acceptance_receipts']:
            receipt['checks']=decode(receipt['checks']);receipt['artifact_refs']=decode(receipt['artifact_refs'])
        out['stage']='QUALIFICATION_CONSUMED_OBSERVED';out['observation_bound']=True;out['query_log']=r.log
        return out
    finally:
        if c.in_transaction: c.execute('ROLLBACK')
        c.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ['database','project-id','session-id','owner-principal','out']:parser.add_argument('--'+flag,required=True)
    for flag in ['coding-request-id','model-config-ref','qualification-request-id','run-id']:parser.add_argument('--'+flag)
    parser.add_argument('--expected-write-path',action='append')
    args=parser.parse_args();target=pathlib.Path(args.out).resolve();root=pathlib.Path(__file__).resolve().parent
    need(target.is_relative_to(root) and target!=root,'OUTPUT_MUST_BE_WITHIN_HELPER_DIRECTORY');need(not target.exists(),'APPEND_ONLY_OUTPUT_REQUIRED')
    try:
        value=observe(args.database,args.project_id,args.session_id,args.owner_principal,args.coding_request_id,args.model_config_ref,args.qualification_request_id,args.run_id,args.expected_write_path);exit_code=0
    except (ObservationError,sqlite3.Error,ValueError,KeyError,TypeError,OSError) as error:
        value={'schema':'researchos.coding-model-readonly-observation-error/1','at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'OBSERVATION_FAILED','error_type':type(error).__name__,'error_code':str(error) if isinstance(error,ObservationError) else 'READ_OR_SCHEMA_FAILURE','mutations':0,'api_requests':0,'model_requests':0,'formal_increment':0};exit_code=2
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8');need(len(raw)<=MAX_OUTPUT,'OUTPUT_BYTE_BOUND');target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(raw)
    print(json.dumps({'path':str(target),'sha256':sha(raw),'bytes':len(raw),'native_exit':exit_code,'stage':value.get('stage',value.get('status')),'mutations':0,'formal_increment':0}));return exit_code

if __name__=='__main__':
    sys.exit(main())
