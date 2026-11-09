import pathlib,sqlite3,json,datetime,time
E=pathlib.Path(__file__).parent
DB=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/live/current-chat-normal-desktop-first-use-20261012/data/researchos.sqlite')
assert DB.is_file()
c=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True,timeout=3);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
deadline=time.monotonic()+8;c.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
def rows(sql,args=()):return [dict(r) for r in c.execute(sql,args)]
q={
 'unresolved_commands':"SELECT (SELECT count(*) FROM client_command_queue WHERE state NOT IN ('CONSUMED','DROPPED'))+(SELECT count(*) FROM client_control_requests WHERE state<>'CONFIRMED') AS count",
 'active_runs':"SELECT count(*) AS count FROM domain_objects WHERE kind='Run' AND coalesce(json_extract(body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED')",
 'unresolved_effects':"SELECT count(*) AS count FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')",
 'unresolved_dispatches':"SELECT count(*) AS count FROM runtime_dispatches WHERE state IN ('PREPARED','STARTED','UNKNOWN')",
 'reservations':"SELECT count(*) AS count FROM domain_objects x WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.operation') IN ('RESERVE','UNKNOWN') AND rowid=(SELECT max(y.rowid) FROM domain_objects y WHERE y.kind='BudgetLedgerEntry' AND y.project=x.project AND json_extract(y.body,'$.run_id')=json_extract(x.body,'$.run_id') AND json_extract(y.body,'$.provider_request_id')=json_extract(x.body,'$.provider_request_id'))",
}
try:
 out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'database':str(DB),'mode':'URI mode=ro; PRAGMA query_only=ON; BEGIN read snapshot; ROLLBACK','query_only':c.execute('PRAGMA query_only').fetchone()[0],'counters':{k:rows(v)[0]['count'] for k,v in q.items()},'queries':q}
 out['run_metadata']=rows("SELECT project,id,json_extract(body,'$.task_id') task_id,json_extract(body,'$.status') status,json_extract(body,'$.children_stopped') children_stopped,json_extract(body,'$.queue_empty') queue_empty,json_extract(body,'$.ended_at') ended_at,json_extract(body,'$.lease_epoch') lease_epoch FROM domain_objects WHERE kind='Run'")
 out['ledger_metadata']=rows("SELECT project,id,json_extract(body,'$.run_id') run_id,json_extract(body,'$.operation') operation,json_extract(body,'$.provider_request_id') provider_request_id,json_extract(body,'$.cost_basis') cost_basis,json_type(body,'$.money') money_json_type,json_type(body,'$.reservation_id') reservation_json_type FROM domain_objects WHERE kind='BudgetLedgerEntry'")
 out['effects_metadata']=rows("SELECT project,run,effect_key,sequence,json_extract(body,'$.state') state,json_extract(body,'$.receipt.state') receipt_state,json_extract(body,'$.receipt.model_transport') model_transport,json_extract(body,'$.receipt.payload.status') http_status,json_extract(body,'$.receipt.payload.content_type') content_type,length(json_extract(body,'$.receipt.payload.body')) body_length,json_extract(body,'$.receipt.payload.body_encoding') body_encoding,json_type(body,'$.receipt.actual_cost') actual_cost_json_type FROM resource_effects ORDER BY project,run,effect_key,sequence")
 out['schemas']={t:rows('PRAGMA table_info('+t+')') for t in ['runtime_dispatches','idempotency','client_sessions','runtime_run_observations']}
 out['idempotency_operation_counts']=rows("SELECT operation,count(*) count FROM idempotency WHERE operation LIKE 'host:%' GROUP BY operation")
finally:c.execute('ROLLBACK');c.close()
(E/'db-readonly-state.json').write_text(json.dumps(out,ensure_ascii=True,indent=2),encoding='utf8')
print(json.dumps({'counters':out['counters'],'runs':out['run_metadata'],'ledger':out['ledger_metadata'],'effects':out['effects_metadata']},ensure_ascii=True))
